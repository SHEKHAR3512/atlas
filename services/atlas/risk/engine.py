import logging
from typing import Any, Dict, List, Optional
from services.atlas.core.config import config
from services.atlas.core.constants import StrategyStatus
from services.atlas.risk.limits import RiskLimitsValidator
from services.atlas.risk.drawdown import DrawdownMonitor
from services.atlas.risk.circuit_breaker import circuit_breaker

logger = logging.getLogger("atlas.risk.engine")


class RiskEngine:
    """
    Deterministic Quantitative Risk Engine.
    Primary mandate: Protect capital and enforce immutable constraints.
    Cannot be bypassed or modified by AI research models.
    """

    def __init__(
        self,
        limits_validator: Optional[RiskLimitsValidator] = None,
        drawdown_monitor: Optional[DrawdownMonitor] = None,
    ):
        self.limits = limits_validator or RiskLimitsValidator()
        self.drawdown = drawdown_monitor or DrawdownMonitor()

    def evaluate_order_proposal(
        self,
        portfolio: Dict[str, Any],
        positions: List[Dict[str, Any]],
        signal: Dict[str, Any],
        market: Dict[str, Any],
        strategy: Dict[str, Any],
        proposed_order: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Pure deterministic decision pipeline.
        Returns approval status, approved quantity, list of rules evaluated, and explicit reason.
        """
        rules_applied = []
        requested_qty = int(proposed_order.get("quantity", 0))
        symbol = proposed_order.get("symbol", "")
        side = proposed_order.get("side", "BUY")
        price = float(proposed_order.get("price", 0.0))
        sector = market.get("sector") or strategy.get("sector", "")
        equity = float(portfolio.get("equity", 100000.0))

        # Rule 1: Kill switch & Circuit breaker
        can_trade, cb_reason = circuit_breaker.can_open_new_position()
        rules_applied.append({"rule": "circuit_breaker", "passed": can_trade, "reason": cb_reason})
        if not can_trade:
            return {
                "approved": False,
                "requested_quantity": requested_qty,
                "approved_quantity": 0,
                "decision": "REJECTED",
                "rules": rules_applied,
                "reason": cb_reason,
            }

        # Rule 2: Strategy status check
        strat_status = strategy.get("status", "APPROVED")
        strat_key = strategy.get("id", "")
        if strat_status in (StrategyStatus.RETIRED.value, StrategyStatus.SUSPENDED.value):
            reason = f"Strategy {strat_key} is {strat_status} and cannot trade"
            rules_applied.append({"rule": "strategy_status", "passed": False, "reason": reason})
            return {
                "approved": False,
                "requested_quantity": requested_qty,
                "approved_quantity": 0,
                "decision": "REJECTED",
                "rules": rules_applied,
                "reason": reason,
            }

        # Rule 3: Experimental strategy cannot trade on live broker
        is_live = config.is_live
        if is_live and strat_status != StrategyStatus.LIVE.value:
            reason = f"Strategy status {strat_status} not permitted for live execution (APPROVED/LIVE required)"
            rules_applied.append({"rule": "live_strategy_status", "passed": False, "reason": reason})
            return {
                "approved": False,
                "requested_quantity": requested_qty,
                "approved_quantity": 0,
                "decision": "REJECTED",
                "rules": rules_applied,
                "reason": reason,
            }

        # Rule 4: Direction restriction (Long-only cash equities V1)
        if side.upper() != "BUY":
            # Exits / Sells are always approved to reduce risk!
            rules_applied.append({"rule": "exit_approval", "passed": True, "reason": "Risk-reducing sell order approved"})
            return {
                "approved": True,
                "requested_quantity": requested_qty,
                "approved_quantity": requested_qty,
                "decision": "APPROVED",
                "rules": rules_applied,
                "reason": "Risk-reducing sell approved",
            }

        # Rule 5: Zero or non-positive requested quantity
        if requested_qty <= 0 or price <= 0:
            rules_applied.append({"rule": "quantity_sanity", "passed": False, "reason": "Quantity or price non-positive"})
            return {
                "approved": False,
                "requested_quantity": requested_qty,
                "approved_quantity": 0,
                "decision": "REJECTED",
                "rules": rules_applied,
                "reason": "Requested quantity or price <= 0",
            }

        # Rule 6: Drawdown and Loss Limits
        dd_passed, dd_reason = self.drawdown.check_drawdown_limits(
            current_equity=equity,
            start_of_day_equity=float(portfolio.get("start_of_day_equity", equity)),
            start_of_week_equity=float(portfolio.get("start_of_week_equity", equity)),
            high_water_mark=float(portfolio.get("high_water_mark", equity)),
        )
        rules_applied.append({"rule": "drawdown_limits", "passed": dd_passed, "reason": dd_reason})
        if not dd_passed:
            return {
                "approved": False,
                "requested_quantity": requested_qty,
                "approved_quantity": 0,
                "decision": "REJECTED",
                "rules": rules_applied,
                "reason": dd_reason,
            }

        # Rule 7: Hard Position Sizing Limit
        pos_passed, allowed_qty, pos_reason = self.limits.check_position_limit(
            symbol=symbol,
            price=price,
            quantity=requested_qty,
            portfolio_equity=equity,
            active_positions=positions,
        )
        rules_applied.append({"rule": "position_limit", "passed": pos_passed, "reason": pos_reason})
        if not pos_passed or allowed_qty <= 0:
            return {
                "approved": False,
                "requested_quantity": requested_qty,
                "approved_quantity": 0,
                "decision": "REJECTED",
                "rules": rules_applied,
                "reason": pos_reason,
            }
        current_approved_qty = min(requested_qty, allowed_qty)

        # Rule 8: Sector Exposure Limit
        sec_passed, allowed_sec_qty, sec_reason = self.limits.check_sector_limit(
            sector=sector,
            price=price,
            quantity=current_approved_qty,
            portfolio_equity=equity,
            active_positions=positions,
        )
        rules_applied.append({"rule": "sector_limit", "passed": sec_passed, "reason": sec_reason})
        if not sec_passed or allowed_sec_qty <= 0:
            return {
                "approved": False,
                "requested_quantity": requested_qty,
                "approved_quantity": 0,
                "decision": "REJECTED",
                "rules": rules_applied,
                "reason": sec_reason,
            }
        current_approved_qty = min(current_approved_qty, allowed_sec_qty)

        # Rule 9: Gross Portfolio Exposure Limit
        gross_passed, allowed_gross_qty, gross_reason = self.limits.check_gross_exposure_limit(
            price=price,
            quantity=current_approved_qty,
            portfolio_equity=equity,
            active_positions=positions,
        )
        rules_applied.append({"rule": "gross_exposure_limit", "passed": gross_passed, "reason": gross_reason})
        if not gross_passed or allowed_gross_qty <= 0:
            return {
                "approved": False,
                "requested_quantity": requested_qty,
                "approved_quantity": 0,
                "decision": "REJECTED",
                "rules": rules_applied,
                "reason": gross_reason,
            }
        current_approved_qty = min(current_approved_qty, allowed_gross_qty)

        # Final decision
        is_modified = current_approved_qty < requested_qty
        decision = "MODIFIED" if is_modified else "APPROVED"

        return {
            "approved": True,
            "requested_quantity": requested_qty,
            "approved_quantity": current_approved_qty,
            "decision": decision,
            "rules": rules_applied,
            "reason": "All risk limits satisfied" if not is_modified else f"Modified: {pos_reason or sec_reason}",
        }
