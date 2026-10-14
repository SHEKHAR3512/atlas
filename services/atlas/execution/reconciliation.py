import logging
from typing import Any, Dict, List, Tuple
from services.atlas.brokers.base import Broker
from services.atlas.risk.circuit_breaker import circuit_breaker
from services.atlas.core.constants import CircuitBreakerAction

logger = logging.getLogger("atlas.execution.reconciliation")


class ReconciliationService:
    """
    Periodic position and balance reconciliation service.
    Broker state is the definitive source of truth.
    Any discrepancy triggers a safety freeze.
    """

    def __init__(self, broker: Broker):
        self.broker = broker

    async def reconcile_positions(
        self,
        internal_positions: List[Dict[str, Any]],
    ) -> Tuple[bool, List[Dict[str, Any]]]:
        """
        Compares internal position quantities with broker reported positions.
        Returns (is_synced, discrepancies).
        """
        broker_positions = await self.broker.positions()
        broker_map = {p["symbol"]: int(p["quantity"]) for p in broker_positions}
        internal_map = {
            p["symbol"]: int(p["quantity"]) for p in internal_positions if p.get("is_open", True)
        }

        all_symbols = set(broker_map.keys()).union(set(internal_map.keys()))
        discrepancies = []

        for sym in all_symbols:
            b_qty = broker_map.get(sym, 0)
            i_qty = internal_map.get(sym, 0)
            if b_qty != i_qty:
                discrepancies.append({
                    "symbol": sym,
                    "internal_quantity": i_qty,
                    "broker_quantity": b_qty,
                    "difference": b_qty - i_qty,
                })

        if discrepancies:
            logger.critical(
                f"POSITION MISMATCH DETECTED: {discrepancies}. FREEZING NEW ORDERS."
            )
            circuit_breaker.trigger_kill_switch(
                reason=f"Position reconciliation mismatch detected for {len(discrepancies)} symbols",
                triggered_by="RECONCILIATION_ENGINE",
            )
            return False, discrepancies

        logger.info("Position reconciliation check passed. All positions in sync.")
        return True, []
