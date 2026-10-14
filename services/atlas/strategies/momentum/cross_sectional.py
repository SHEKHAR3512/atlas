from typing import Any, Dict, List, Optional
import numpy as np
import pandas as pd
from services.atlas.core.constants import MarketRegime, OrderSide
from services.atlas.strategies.base import Strategy, StrategySignal
from services.atlas.indicators.technical import calculate_realized_volatility


class CrossSectionalMomentumStrategy(Strategy):
    """
    Strategy B — Cross-Sectional Momentum
    Ranks universe by risk-adjusted momentum (Return / Volatility),
    applies liquidity constraints, and selects top decile.
    """

    def __init__(self, strategy_key: str = "momentum_cross_sectional_v1", parameters: Optional[Dict[str, Any]] = None):
        defaults = {
            "lookback_days": 90,
            "top_n": 3,
            "volatility_window": 20,
            "min_avg_volume": 100_000,
        }
        if parameters:
            defaults.update(parameters)
        super().__init__(strategy_key, defaults)

    def required_history(self) -> int:
        return int(self._parameters["lookback_days"]) + 20

    def generate_signals(
        self,
        market_data: Dict[str, pd.DataFrame],
        current_regime: MarketRegime = MarketRegime.UNKNOWN,
    ) -> List[StrategySignal]:
        signals: List[StrategySignal] = []

        # Momentum degrades heavily in crisis or strong bear regimes
        if current_regime in (MarketRegime.BEAR_TREND, MarketRegime.CRISIS):
            return signals

        lookback = int(self._parameters["lookback_days"])
        vol_win = int(self._parameters["volatility_window"])
        top_n = int(self._parameters["top_n"])
        min_vol = float(self._parameters["min_avg_volume"])

        scored_candidates = []

        for symbol, df in market_data.items():
            if len(df) < self.required_history():
                continue

            close = df["close"]
            volume = df["volume"]

            avg_vol = float(volume.tail(20).mean())
            if avg_vol < min_vol:
                continue

            current_close = float(close.iloc[-1])
            past_close = float(close.iloc[-lookback])

            raw_return = (current_close - past_close) / past_close
            ann_vol = float(calculate_realized_volatility(close, window=vol_win).iloc[-1])

            # Risk-adjusted momentum (Sharpe-like score)
            risk_adj_momentum = raw_return / (ann_vol + 1e-4)

            # Only positive momentum stocks
            if raw_return > 0 and risk_adj_momentum > 0.5:
                scored_candidates.append({
                    "symbol": symbol,
                    "price": current_close,
                    "raw_return": raw_return,
                    "volatility": ann_vol,
                    "score": risk_adj_momentum,
                })

        # Sort descending by risk-adjusted momentum score
        scored_candidates.sort(key=lambda x: x["score"], reverse=True)
        top_picks = scored_candidates[:top_n]

        for rank, pick in enumerate(top_picks):
            # Strength scaled from 0.90 down to 0.70 based on rank
            strength = round(max(0.60, 0.95 - (rank * 0.10)), 2)
            signals.append(
                StrategySignal(
                    symbol=pick["symbol"],
                    direction=OrderSide.BUY,
                    strength=strength,
                    strategy_key=self.strategy_key,
                    price=pick["price"],
                    market_regime=current_regime.value,
                    metadata={
                        "rank": rank + 1,
                        "momentum_score": round(pick["score"], 3),
                        "raw_return": round(pick["raw_return"], 4),
                        "volatility": round(pick["volatility"], 4),
                    }
                )
            )

        return signals
