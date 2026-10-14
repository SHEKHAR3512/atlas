from typing import Any, Dict, List, Optional
import pandas as pd
from services.atlas.core.constants import MarketRegime, OrderSide
from services.atlas.strategies.base import Strategy, StrategySignal
from services.atlas.indicators.technical import (
    calculate_donchian_channels,
    calculate_atr,
)


class BreakoutStrategy(Strategy):
    """
    Strategy D — Donchian Breakout with Volume Confirmation
    Enters on breakout of N-day highest high with volume surge and ATR trailing stop.
    """

    def __init__(self, strategy_key: str = "breakout_donchian_v1", parameters: Optional[Dict[str, Any]] = None):
        defaults = {
            "channel_period": 20,
            "volume_factor": 1.25,
            "atr_stop_multiplier": 1.5,
        }
        if parameters:
            defaults.update(parameters)
        super().__init__(strategy_key, defaults)

    def required_history(self) -> int:
        return int(self._parameters["channel_period"]) + 20

    def generate_signals(
        self,
        market_data: Dict[str, pd.DataFrame],
        current_regime: MarketRegime = MarketRegime.UNKNOWN,
    ) -> List[StrategySignal]:
        signals: List[StrategySignal] = []

        if current_regime in (MarketRegime.BEAR_TREND, MarketRegime.CRISIS):
            return signals

        period = int(self._parameters["channel_period"])
        vol_factor = float(self._parameters["volume_factor"])
        atr_mult = float(self._parameters["atr_stop_multiplier"])

        for symbol, df in market_data.items():
            if len(df) < self.required_history():
                continue

            close = df["close"]
            high = df["high"]
            volume = df["volume"]
            current_close = float(close.iloc[-1])
            current_vol = float(volume.iloc[-1])

            upper, lower, mid = calculate_donchian_channels(df, period=period)
            atr = calculate_atr(df, period=14)

            # Prior bar's 20-day upper channel
            prev_upper = float(upper.iloc[-2])
            avg_vol = float(volume.tail(period).mean())
            current_atr = float(atr.iloc[-1])

            # Breakout: Current close breaks above previous channel upper bound with volume confirmation
            is_breakout = (current_close > prev_upper) and (current_vol >= vol_factor * avg_vol)

            if is_breakout:
                strength = min(1.0, 0.65 + min(0.30, (current_vol / (avg_vol + 1e-4) - 1.0) * 0.2))
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
                            "donchian_upper": prev_upper,
                            "volume_ratio": round(current_vol / (avg_vol + 1e-4), 2),
                            "stop_loss": stop_loss,
                            "atr": current_atr,
                        }
                    )
                )

        return signals
