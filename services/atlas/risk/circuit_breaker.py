import sys
import logging
from typing import Dict, Any, Optional
from services.atlas.core.constants import CircuitBreakerAction

logger = logging.getLogger("atlas.risk.circuit_breaker")


class CircuitBreaker:
    """
    Automated Circuit Breaker and Hard Kill Switch.
    Always fails closed upon any critical threshold breach.
    """

    def __init__(self):
        self._action: CircuitBreakerAction = CircuitBreakerAction.NORMAL
        self._kill_switch_active: bool = False
        self._kill_reason: Optional[str] = None
        self._consecutive_errors: int = 0
        self._max_consecutive_errors: int = 5

    @property
    def is_kill_switch_active(self) -> bool:
        return self._kill_switch_active

    @property
    def current_action(self) -> CircuitBreakerAction:
        if self._kill_switch_active:
            return CircuitBreakerAction.SYSTEM_HALT
        return self._action

    def trigger_kill_switch(self, reason: str, triggered_by: str = "SYSTEM"):
        self._kill_switch_active = True
        self._kill_reason = reason
        self._action = CircuitBreakerAction.SYSTEM_HALT
        logger.critical(f"HARD KILL SWITCH ACTIVATED by {triggered_by}: {reason}")

    def reset_kill_switch(self, acknowledged_by: str):
        self._kill_switch_active = False
        self._kill_reason = None
        self._action = CircuitBreakerAction.NORMAL
        self._consecutive_errors = 0
        logger.warning(f"Hard Kill Switch manually reset by {acknowledged_by}")

    def register_broker_error(self):
        self._consecutive_errors += 1
        if self._consecutive_errors >= self._max_consecutive_errors:
            self._action = CircuitBreakerAction.BLOCK_NEW_ENTRIES
            logger.error(
                f"Consecutive broker errors reached {self._consecutive_errors}. Tripping circuit breaker to BLOCK_NEW_ENTRIES."
            )

    def register_broker_success(self):
        self._consecutive_errors = max(0, self._consecutive_errors - 1)
        if self._consecutive_errors == 0 and not self._kill_switch_active and self._action == CircuitBreakerAction.BLOCK_NEW_ENTRIES:
            self._action = CircuitBreakerAction.NORMAL

    def can_open_new_position(self) -> Tuple[bool, str]:
        if self._kill_switch_active:
            return False, f"Hard Kill Switch active: {self._kill_reason}"
        if self._action in (CircuitBreakerAction.BLOCK_NEW_ENTRIES, CircuitBreakerAction.SYSTEM_HALT, CircuitBreakerAction.EXIT_POSITIONS):
            return False, f"Circuit breaker active: {self._action.value}"
        return True, "Normal operation"


# Global singleton instance
circuit_breaker = CircuitBreaker()


if __name__ == "__main__":
    if "--kill" in sys.argv:
        circuit_breaker.trigger_kill_switch(
            reason="Triggered via CLI 'make kill'",
            triggered_by="CLI"
        )
        print("==================================================")
        print("  EMERGENCY HARD KILL SWITCH ACTIVATED")
        print("  All new orders blocked. System in FAIL-CLOSED.")
        print("==================================================")
    else:
        print(f"Circuit Breaker Status: {circuit_breaker.current_action.value}")
