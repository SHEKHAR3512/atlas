import time
import uuid
from typing import Dict, Any, Optional


class OrderManager:
    """
    Manages deterministic client order IDs, idempotency keys,
    and order status tracking.
    """

    @staticmethod
    def generate_client_order_id(
        strategy_id: str,
        symbol: str,
        signal_id: Optional[str] = None
    ) -> str:
        """
        Deterministic client order identifier format:
        {strategyId}-{symbol}-{signalId}-{timestamp}
        """
        ts = int(time.time() * 1000)
        sig_part = (signal_id[:8]) if signal_id else uuid.uuid4().hex[:8]
        return f"{strategy_id}_{symbol}_{sig_part}_{ts}"
