import math
from typing import Optional


class SlippageModel:
    """
    Realistic execution slippage model.
    Slippage = Base BPS + Impact Coefficient * sqrt(Order Volume / Traded Volume)
    """

    def __init__(self, default_bps: float = 10.0, impact_coef: float = 0.05):
        self.default_bps = default_bps
        self.impact_coef = impact_coef

    def calculate_slippage(
        self,
        side: str,
        price: float,
        quantity: int,
        daily_volume: Optional[float] = None
    ) -> float:
        """
        Calculates execution price adjustment.
        Returns execution price (higher for BUY, lower for SELL).
        """
        base_rate = self.default_bps / 10000.0

        if daily_volume and daily_volume > 0:
            participation = quantity / daily_volume
            impact = self.impact_coef * math.sqrt(min(participation, 0.10))
            effective_rate = base_rate + impact
        else:
            effective_rate = base_rate

        # Cap slippage at max 50 bps for liquid safety
        effective_rate = min(effective_rate, 0.005)

        if side.upper() == "BUY":
            return round(price * (1.0 + effective_rate), 2)
        else:
            return round(price * (1.0 - effective_rate), 2)
