import logging
from typing import Any, Dict, List, Tuple
from services.atlas.core.config import config

logger = logging.getLogger("atlas.risk.limits")


class RiskLimitsValidator:
    """
    Evaluates hard risk boundaries that cannot be overridden by AI or strategy engines.
    """

    def __init__(self):
        self.max_position_pct = config.settings.MAX_POSITION_PCT # 0.03 (3%)
        self.max_sector_pct = config.settings.MAX_SECTOR_EXPOSURE_PCT # 0.15 (15%)
        self.max_gross_exposure_pct = config.settings.MAX_GROSS_EXPOSURE_PCT # 0.60 (60%)
        self.max_order_notional_pct = config.settings.MAX_ORDER_NOTIONAL_PCT # 0.03 (3%)

    def check_position_limit(
        self,
        symbol: str,
        price: float,
        quantity: int,
        portfolio_equity: float,
        active_positions: List[Dict[str, Any]],
    ) -> Tuple[bool, int, str]:
        """
        Ensures total exposure for this symbol does not exceed MAX_POSITION_PCT.
        Returns (is_valid, allowed_quantity, reason).
        """
        existing_qty = sum(
            p["quantity"] for p in active_positions if p["symbol"] == symbol and p.get("is_open", True)
        )
        total_proposed_qty = existing_qty + quantity
        proposed_notional = total_proposed_qty * price
        max_notional = portfolio_equity * self.max_position_pct

        if proposed_notional <= max_notional:
            return True, quantity, "Position size within limit"

        # Scale down quantity if possible
        available_notional = max(0.0, max_notional - (existing_qty * price))
        allowed_qty = int(available_notional / price)
        if allowed_qty > 0:
            return True, allowed_qty, f"Scaled down to fit {self.max_position_pct*100}% position limit"

        return False, 0, f"Position would exceed max limit {self.max_position_pct*100}%"

    def check_sector_limit(
        self,
        sector: str,
        price: float,
        quantity: int,
        portfolio_equity: float,
        active_positions: List[Dict[str, Any]],
    ) -> Tuple[bool, int, str]:
        """
        Ensures total exposure for the sector does not exceed MAX_SECTOR_EXPOSURE_PCT (15%).
        """
        if not sector:
            return True, quantity, "No sector specified"

        existing_sector_notional = sum(
            p["quantity"] * p.get("current_price", p.get("average_entry_price", 0.0))
            for p in active_positions
            if p.get("sector") == sector and p.get("is_open", True)
        )
        order_notional = price * quantity
        max_sector_notional = portfolio_equity * self.max_sector_pct

        if (existing_sector_notional + order_notional) <= max_sector_notional:
            return True, quantity, f"Sector {sector} within limit"

        available_sector_notional = max(0.0, max_sector_notional - existing_sector_notional)
        allowed_qty = int(available_sector_notional / price)
        if allowed_qty > 0:
            return True, allowed_qty, f"Scaled down to fit {self.max_sector_pct*100}% sector limit for {sector}"

        return False, 0, f"Sector {sector} exposure exceeds {self.max_sector_pct*100}%"

    def check_gross_exposure_limit(
        self,
        price: float,
        quantity: int,
        portfolio_equity: float,
        active_positions: List[Dict[str, Any]],
    ) -> Tuple[bool, int, str]:
        """
        Ensures total gross portfolio exposure does not exceed MAX_GROSS_EXPOSURE_PCT (60%).
        """
        current_invested = sum(
            p["quantity"] * p.get("current_price", p.get("average_entry_price", 0.0))
            for p in active_positions if p.get("is_open", True)
        )
        order_notional = price * quantity
        max_gross = portfolio_equity * self.max_gross_exposure_pct

        if (current_invested + order_notional) <= max_gross:
            return True, quantity, "Gross portfolio exposure within limit"

        available_gross = max(0.0, max_gross - current_invested)
        allowed_qty = int(available_gross / price)
        if allowed_qty > 0:
            return True, allowed_qty, f"Scaled down to fit {self.max_gross_exposure_pct*100}% gross exposure limit"

        return False, 0, f"Gross exposure would exceed {self.max_gross_exposure_pct*100}%"
