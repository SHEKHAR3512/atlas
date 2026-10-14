import logging
from typing import Any, Dict, List, Optional
import pandas as pd
from services.atlas.backtesting.engine import BacktestEngine
from services.atlas.strategies.base import Strategy

logger = logging.getLogger("atlas.backtesting.walk_forward")


class WalkForwardValidator:
    """
    Rolling Walk-Forward Analysis engine to prevent overfitting and data leakage.
    Splits chronological timeline into distinct Train (In-Sample) and Test (Out-of-Sample) folds.
    """

    def __init__(
        self,
        train_window_bars: int = 252, # 1 trading year
        test_window_bars: int = 63,   # 1 quarter
        folds: int = 3,
        engine: Optional[BacktestEngine] = None,
    ):
        self.train_window_bars = train_window_bars
        self.test_window_bars = test_window_bars
        self.folds = folds
        self.engine = engine or BacktestEngine()

    def run_walk_forward(
        self,
        strategy: Strategy,
        market_data: Dict[str, pd.DataFrame],
    ) -> Dict[str, Any]:
        # Collect chronological unique timestamps
        all_timestamps = set()
        for df in market_data.values():
            all_timestamps.update(df["timestamp"].tolist())
        timeline = sorted(list(all_timestamps))

        total_bars_needed = self.train_window_bars + (self.test_window_bars * self.folds)
        if len(timeline) < total_bars_needed:
            # Adjust window dynamically if historical dataset is shorter
            step = max(20, len(timeline) // (self.folds + 2))
            train_len = step * 2
            test_len = step
        else:
            train_len = self.train_window_bars
            test_len = self.test_window_bars

        fold_results = []
        train_sharpes = []
        test_sharpes = []

        for fold_idx in range(self.folds):
            start_idx = fold_idx * test_len
            train_end_idx = start_idx + train_len
            test_end_idx = min(train_end_idx + test_len, len(timeline))

            if train_end_idx >= len(timeline) or test_end_idx <= train_end_idx:
                break

            train_dates = (timeline[start_idx], timeline[train_end_idx - 1])
            test_dates = (timeline[train_end_idx], timeline[test_end_idx - 1])

            # Slice datasets
            train_data = {
                sym: df[(df["timestamp"] >= train_dates[0]) & (df["timestamp"] <= train_dates[1])].reset_index(drop=True)
                for sym, df in market_data.items()
            }
            test_data = {
                sym: df[(df["timestamp"] >= test_dates[0]) & (df["timestamp"] <= test_dates[1])].reset_index(drop=True)
                for sym, df in market_data.items()
            }

            # Run in-sample
            train_res = self.engine.run(strategy, train_data)
            # Run out-of-sample
            test_res = self.engine.run(strategy, test_data)

            train_sh = train_res["metrics"].get("sharpe_ratio", 0.0)
            test_sh = test_res["metrics"].get("sharpe_ratio", 0.0)

            # Performance decay = (train_sharpe - test_sharpe) / train_sharpe
            decay = ((train_sh - test_sh) / train_sh) if train_sh > 0 else 0.0

            fold_results.append({
                "fold_index": fold_idx + 1,
                "train_start": str(train_dates[0]),
                "train_end": str(train_dates[1]),
                "test_start": str(test_dates[0]),
                "test_end": str(test_dates[1]),
                "train_metrics": train_res["metrics"],
                "test_metrics": test_res["metrics"],
                "validation_decay": round(decay, 4),
            })

            train_sharpes.append(train_sh)
            test_sharpes.append(test_sh)

        avg_train_sharpe = float(sum(train_sharpes) / len(train_sharpes)) if train_sharpes else 0.0
        avg_test_sharpe = float(sum(test_sharpes) / len(test_sharpes)) if test_sharpes else 0.0
        overall_decay = ((avg_train_sharpe - avg_test_sharpe) / avg_train_sharpe) if avg_train_sharpe > 0 else 0.0

        return {
            "folds": fold_results,
            "avg_train_sharpe": round(avg_train_sharpe, 3),
            "avg_test_sharpe": round(avg_test_sharpe, 3),
            "overall_validation_decay": round(overall_decay, 4),
            "is_robust": (overall_decay <= 0.35 and avg_test_sharpe >= 0.8),
        }
