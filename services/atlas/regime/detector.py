import logging
from typing import Dict, List, Optional
import numpy as np
import pandas as pd
from services.atlas.core.constants import MarketRegime
from services.atlas.indicators.technical import (
    calculate_ema,
    calculate_realized_volatility,
    calculate_atr,
)

logger = logging.getLogger("atlas.regime")


class RegimeDetector:
    """
    Deterministic quantitative market regime classifier.
    Evaluates:
      1. Trend structure (Fast EMA vs Slow EMA vs Long-term Trend)
      2. Volatility regime (Realized Vol vs historical threshold)
      3. Market breadth & Drawdown severity (Crisis detection)
    """

    def __init__(
        self,
        vol_high_threshold: float = 0.28, # >28% annualized is high vol
        vol_low_threshold: float = 0.14,  # <14% annualized is low vol
        crisis_drawdown_pct: float = -0.15 # -15% peak-to-trough is crisis
    ):
        self.vol_high_threshold = vol_high_threshold
        self.vol_low_threshold = vol_low_threshold
        self.crisis_drawdown_pct = crisis_drawdown_pct

    def detect_regime(
        self,
        benchmark_df: pd.DataFrame,
        market_breadth_pct: Optional[float] = None,
    ) -> Dict[str, any]:
        """
        Classifies current regime from benchmark/index OHLCV data.
        Returns dict with regime, confidence, and features.
        """
        if benchmark_df is None or len(benchmark_df) < 50:
            return {
                "regime": MarketRegime.UNKNOWN,
                "confidence": 0.5,
                "features": {"error": "Insufficient history (<50 bars)"}
            }

        close = benchmark_df["close"]
        current_close = float(close.iloc[-1])

        ema20 = calculate_ema(close, 20).iloc[-1]
        ema50 = calculate_ema(close, 50).iloc[-1]
        ema200 = calculate_ema(close, 200).iloc[-1] if len(close) >= 200 else ema50

        realized_vol = calculate_realized_volatility(close, window=20).iloc[-1]
        atr = calculate_atr(benchmark_df, period=14).iloc[-1]
        atr_pct = (atr / current_close) if current_close > 0 else 0.0

        # Drawdown calculation
        rolling_peak = close.cummax().iloc[-1]
        current_dd = (current_close - rolling_peak) / rolling_peak

        features = {
            "current_close": current_close,
            "ema20": float(ema20),
            "ema50": float(ema50),
            "ema200": float(ema200),
            "realized_vol": float(realized_vol),
            "atr_pct": float(atr_pct),
            "current_drawdown": float(current_dd),
            "market_breadth_pct": float(market_breadth_pct) if market_breadth_pct is not None else 0.5,
        }

        # 1. Crisis Check: Severe market drawdown + extreme volatility spike
        if current_dd <= self.crisis_drawdown_pct and realized_vol >= self.vol_high_threshold:
            return {
                "regime": MarketRegime.CRISIS,
                "confidence": 0.95,
                "features": features
            }

        # 2. High Volatility Check
        if realized_vol >= self.vol_high_threshold:
            return {
                "regime": MarketRegime.HIGH_VOLATILITY,
                "confidence": 0.85,
                "features": features
            }

        # 3. Trend Alignment
        is_bull_structure = (current_close > ema50) and (ema20 > ema50) and (ema50 >= ema200 * 0.98)
        is_bear_structure = (current_close < ema50) and (ema20 < ema50) and (current_close < ema200)

        if is_bull_structure:
            conf = 0.90 if (market_breadth_pct is None or market_breadth_pct > 0.6) else 0.75
            return {
                "regime": MarketRegime.BULL_TREND,
                "confidence": conf,
                "features": features
            }

        if is_bear_structure:
            return {
                "regime": MarketRegime.BEAR_TREND,
                "confidence": 0.85,
                "features": features
            }

        # 4. Low Volatility vs Sideways
        if realized_vol <= self.vol_low_threshold:
            return {
                "regime": MarketRegime.LOW_VOLATILITY,
                "confidence": 0.80,
                "features": features
            }

        return {
            "regime": MarketRegime.SIDEWAYS,
            "confidence": 0.75,
            "features": features
        }
