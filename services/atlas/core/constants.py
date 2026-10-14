from enum import Enum


class MarketRegime(str, Enum):
    BULL_TREND = "bull_trend"
    BEAR_TREND = "bear_trend"
    SIDEWAYS = "sideways"
    HIGH_VOLATILITY = "high_volatility"
    LOW_VOLATILITY = "low_volatility"
    CRISIS = "crisis"
    UNKNOWN = "unknown"


class StrategyStatus(str, Enum):
    IDEA = "IDEA"
    EXPERIMENTAL = "EXPERIMENTAL"
    BACKTESTED = "BACKTESTED"
    VALIDATED = "VALIDATED"
    PAPER = "PAPER"
    CANARY = "CANARY"
    LIVE = "LIVE"
    DEGRADED = "DEGRADED"
    SUSPENDED = "SUSPENDED"
    RETIRED = "RETIRED"


class TradingMode(str, Enum):
    PAPER = "PAPER"
    LIVE = "LIVE"


class BrokerType(str, Enum):
    PAPER = "paper"
    ANGEL_ONE = "angel_one"


class OrderSide(str, Enum):
    BUY = "BUY"
    SELL = "SELL"


class OrderType(str, Enum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP_LIMIT = "STOP_LIMIT"


class OrderStatus(str, Enum):
    PENDING = "PENDING"
    SUBMITTED = "SUBMITTED"
    PARTIALLY_FILLED = "PARTIALLY_FILLED"
    FILLED = "FILLED"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"


class RiskDecisionType(str, Enum):
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    MODIFIED = "MODIFIED"


class CircuitBreakerAction(str, Enum):
    NORMAL = "NORMAL"
    BLOCK_NEW_ENTRIES = "BLOCK_NEW_ENTRIES"
    REDUCE_EXPOSURE = "REDUCE_EXPOSURE"
    EXIT_POSITIONS = "EXIT_POSITIONS"
    SYSTEM_HALT = "SYSTEM_HALT"


class AuditEventType(str, Enum):
    SIGNAL = "SIGNAL"
    PROPOSAL = "PROPOSAL"
    RISK_DECISION = "RISK_DECISION"
    ORDER_SUBMITTED = "ORDER_SUBMITTED"
    ORDER_FILLED = "ORDER_FILLED"
    ORDER_CANCELLED = "ORDER_CANCELLED"
    POSITION_OPENED = "POSITION_OPENED"
    POSITION_CLOSED = "POSITION_CLOSED"
    REGIME_CHANGE = "REGIME_CHANGE"
    STRATEGY_PROMOTION = "STRATEGY_PROMOTION"
    STRATEGY_DEGRADATION = "STRATEGY_DEGRADATION"
    KILL_SWITCH = "KILL_SWITCH"
    CIRCUIT_BREAKER = "CIRCUIT_BREAKER"
    RECONCILIATION = "RECONCILIATION"
    SYSTEM_ERROR = "SYSTEM_ERROR"
    CONFIG_CHANGE = "CONFIG_CHANGE"
