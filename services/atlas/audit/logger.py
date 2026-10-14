import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional

REDACTED_KEYS = {
    "password", "secret", "totp", "api_key", "token", "access_token",
    "refresh_token", "jwt", "authorization", "angel_password", "angel_api_key",
}


def sanitize_dict(data: Any) -> Any:
    if isinstance(data, dict):
        clean = {}
        for k, v in data.items():
            if any(red in k.lower() for red in REDACTED_KEYS):
                clean[k] = "[REDACTED]"
            else:
                clean[k] = sanitize_dict(v)
        return clean
    elif isinstance(data, list):
        return [sanitize_dict(item) for item in data]
    return data


class StructuredLogger:
    """
    Structured JSON logger with automatic correlation IDs and credential redaction.
    """

    def __init__(self, logger_name: str = "atlas.audit"):
        self.logger = logging.getLogger(logger_name)

    def log_event(
        self,
        event_type: str,
        action: str,
        strategy_id: Optional[str] = None,
        symbol: Optional[str] = None,
        order_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        cid = correlation_id or str(uuid.uuid4())
        record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "correlation_id": cid,
            "event_type": event_type,
            "action": action,
            "strategy_id": strategy_id,
            "symbol": symbol,
            "order_id": order_id,
            "details": sanitize_dict(details or {}),
        }
        self.logger.info(json.dumps(record))


audit_logger = StructuredLogger()
