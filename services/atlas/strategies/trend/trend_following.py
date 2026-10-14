from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import pandas as pd
from services.atlas.core.constants import MarketRegime, OrderSide
from services.atlas.strategies.base import Strategy, StrategySignal
from services.atlas.indicators.technical import (
    calculate_ema,
    calculate_adx,
    calculate_atr,
)


class TrendFollowingStrategy(Strategy):
    """
    Strategy A — Trend Following
    EMA 20/50/200 + ADX/DI trend strength + ATR trailing stop.
    """

    def __init__(self, strategy_key: str = "trend_following_v1", parameters: Optional[Dict[str, Any]] = None):
        defaults = {
            "fast_ema": 20,
            "slow_ema": 50,
            "trend_ema": 200,
            "adx_period": 14,
            "adx_threshold": 20.0,
            "atr_period": 14,
            "atr_multiplier": 2.0,
        }
        if parameters:
            defaults.update(parameters)
        super().__init__(strategy_key, defaults)

    def required_history(self) -> int:
        return max(self._parameters["trend_ema"] + 20, 220)

    def generate_signals(
        self,
        market_data: Dict[str, pd.DataFrame],
        current_regime: MarketRegime = MarketRegime.UNKNOWN,
    ) -> List[StrategySignal]:
        signals: List[StrategySignal] = []

        # Only open new trend-following long entries in favorable regimes
        if current_regime in (MarketRegime.BEAR_TREND, MarketRegime.CRISIS):
            return signals

        fast_p = int(self._parameters["fast_ema"])
        slow_p = int(self._parameters["slow_ema"])
        trend_p = int(self._parameters["trend_ema"])
        adx_thresh = float(self._parameters["adx_threshold"])
        atr_p = int(self._parameters["atr_period"])
        atr_mult = float(self._parameters["atr_multiplier"])

        for symbol, df in market_data.items():
            if len(df) < self.required_history():
                continue

            close = df["close"]
            current_close = float(close.iloc[-1])
            prev_close = float(close.iloc[-2])

            fast_ema = calculate_ema(close, fast_p)
            slow_ema = calculate_ema(close, slow_p)
            trend_ema = calculate_ema(close, trend_p)

            adx, plus_di, minus_di = calculate_adx(df, period=int(self._parameters["adx_period"]))
            atr = calculate_atr(df, period=atr_p)

            current_fast = float(fast_ema.iloc[-1])
            prev_fast = float(fast_ema.iloc[-2])
            current_slow = float(slow_ema.iloc[-1])
            prev_slow = float(slow_ema.iloc[-2])
            current_trend = float(trend_ema.iloc[-1])

            current_adx = float(adx.iloc[-1])
            current_pdi = float(plus_di.iloc[-1])
            current_mdi = float(minus_di.iloc[-1])
            current_atr = float(atr.iloc[-1])

            # Entry condition:
            # 1. Price above 200 EMA
            # 2. Fast EMA crosses above Slow EMA or holds above with positive slope
            # 3. ADX > threshold and +DI > -DI
            trend_aligned = current_close > current_trend and current_fast > current_slow
            adx_confirmed = current_adx >= adx_thresh and current_pdi > current_mdi
            recent_cross = (prev_fast <= prev_slow and current_fast > current_slow) or (current_close > current_fast and prev_close <= prev_fast)

            if trend_aligned and adx_confirmed and (recent_cross or current_fast > current_slow * 1.01):
                # Strength normalized by ADX intensity (20-50 maps to 0.5-1.0)
                strength = min(1.0, max(0.5, (current_adx / 50.0)))
                stop_loss = round(current_close - (atr_mult * current_atr), 2)

                signals.append(
                    StrategySignal(
                        symbol=symbol,
                        direction=OrderSide.BUY,
                        strength=round(strength, 2),
                        strategy_key=self.strategy_key,
                        price=current_close,
                        market_regime=current_regime.value,
                        metadata={
                            "fast_ema": current_fast,
                            "slow_ema": current_slow,
                            "trend_ema": current_trend,
                            "adx": current_adx,
                            "stop_loss": stop_loss,
                            "atr": current_atr,
                        }
                    )
                )

        return signals
