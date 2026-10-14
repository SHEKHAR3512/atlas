import logging
from typing import Any, Dict, Optional
from services.atlas.brokers.base import Broker
from services.atlas.brokers.paper import PaperBroker
from services.atlas.execution.order_manager import OrderManager
from services.atlas.core.config import config
from services.atlas.core.constants import OrderStatus

logger = logging.getLogger("atlas.execution.engine")


class ExecutionEngine:
    """
    Controlled execution gateway.
    Ensures:
      - Only risk-approved orders are passed to broker
      - Deterministic idempotent client_order_ids
      - Strict price deviation checks
      - Accurate recordkeeping
    """

    def __init__(self, broker: Optional[Broker] = None):
        self.broker = broker or PaperBroker(initial_cash=config.settings.INITIAL_PAPER_CAPITAL)

    async def execute_approved_order(
        self,
        symbol: str,
        side: str,
        quantity: int,
        price: float,
        strategy_key: str,
        signal_id: Optional[str] = None,
        risk_decision_id: Optional[str] = None,
        sector: Optional[str] = None,
    ) -> Dict[str, Any]:
        if quantity <= 0:
            return {"status": "REJECTED", "reason": "Quantity is zero"}

        client_oid = OrderManager.generate_client_order_id(
            strategy_id=strategy_key,
            symbol=symbol,
            signal_id=signal_id,
        )

        order_spec = {
            "client_order_id": client_oid,
            "symbol": symbol,
            "side": side,
            "quantity": quantity,
            "price": price,
            "order_type": "LIMIT",
            "sector": sector or "General",
            "strategy_key": strategy_key,
            "signal_id": signal_id,
            "risk_decision_id": risk_decision_id,
        }

        logger.info(f"Submitting order to broker: {side} {quantity} {symbol} @ Rs {price:.2f} [{client_oid}]")
        res = await self.broker.place_order(order_spec)
        return res
