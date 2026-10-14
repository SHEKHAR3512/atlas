from typing import Any, Dict, List, Optional
import pandas as pd
from services.atlas.core.constants import MarketRegime, OrderSide
from services.atlas.strategies.base import Strategy, StrategySignal
from services.atlas.indicators.technical import (
    calculate_rsi,
    calculate_bollinger_bands,
    calculate_zscore,
    calculate_atr,
)


class MeanReversionStrategy(Strategy):
    """
    Strategy C — Mean Reversion
    RSI + Bollinger Bands + Z-Score oversold bounce in sideways / low vol markets.
    """

    def __init__(self, strategy_key: str = "mean_reversion_rsi_v1", parameters: Optional[Dict[str, Any]] = None):
        defaults = {
            "rsi_period": 14,
            "rsi_oversold": 30.0,
            "rsi_overbought": 70.0,
            "bb_period": 20,
            "bb_std": 2.0,
            "z_threshold": -1.5,
            "atr_multiplier": 1.5,
        }
        if parameters:
            defaults.update(parameters)
        super().__init__(strategy_key, defaults)

    def required_history(self) -> int:
        return max(int(self._parameters["bb_period"]), int(self._parameters["rsi_period"])) + 20

    def generate_signals(
        self,
        market_data: Dict[str, pd.DataFrame],
        current_regime: MarketRegime = MarketRegime.UNKNOWN,
    ) -> List[StrategySignal]:
        signals: List[StrategySignal] = []

        # Mean reversion is strictly active in Sideways or Low Volatility regimes
        if current_regime not in (MarketRegime.SIDEWAYS, MarketRegime.LOW_VOLATILITY, MarketRegime.UNKNOWN):
            return signals

        rsi_p = int(self._parameters["rsi_period"])
        rsi_os = float(self._parameters["rsi_oversold"])
        bb_p = int(self._parameters["bb_period"])
        bb_std = float(self._parameters["bb_std"])
        z_thresh = float(self._parameters["z_threshold"])
        atr_mult = float(self._parameters["atr_multiplier"])

        for symbol, df in market_data.items():
            if len(df) < self.required_history():
                continue

            close = df["close"]
            current_close = float(close.iloc[-1])

            rsi = calculate_rsi(close, period=rsi_p)
            mid_bb, upper_bb, lower_bb = calculate_bollinger_bands(close, period=bb_p, num_std=bb_std)
            zscore = calculate_zscore(close, period=bb_p)
            atr = calculate_atr(df, period=14)

            current_rsi = float(rsi.iloc[-1])
            current_lower = float(lower_bb.iloc[-1])
            current_mid = float(mid_bb.iloc[-1])
            current_z = float(zscore.iloc[-1])
            current_atr = float(atr.iloc[-1])

            # Oversold trigger: RSI < oversold AND (Price <= Lower Band OR Z-score <= -1.5)
            is_oversold = (current_rsi <= rsi_os) and (current_close <= current_lower or current_z <= z_thresh)

            if is_oversold:
                # Stronger signal the more oversold it is
                strength = min(1.0, max(0.5, (40.0 - current_rsi) / 20.0 + 0.5))
                stop_loss = round(current_close - (atr_mult * current_atr), 2)
                take_profit = round(current_mid, 2)

                signals.append(
                    StrategySignal(
                        symbol=symbol,
                        direction=OrderSide.BUY,
                        strength=round(strength, 2),
                        strategy_key=self.strategy_key,
                        price=current_close,
                        market_regime=current_regime.value,
                        metadata={
                            "rsi": round(current_rsi, 2),
                            "lower_bb": round(current_lower, 2),
                            "middle_bb": round(current_mid, 2),
                            "z_score": round(current_z, 2),
                            "stop_loss": stop_loss,
                            "take_profit": take_profit,
                        }
                    )
                )

        return signals
