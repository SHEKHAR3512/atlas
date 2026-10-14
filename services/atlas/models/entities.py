import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    JSON,
    String,
    Text,
)
from sqlalchemy.orm import relationship
from services.atlas.db.session import Base


def generate_uuid() -> str:
    return str(uuid.uuid4())


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Instrument(Base):
    __tablename__ = "instruments"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    symbol = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=False)
    exchange = Column(String(20), default="NSE", nullable=False)
    sector = Column(String(100), nullable=True, index=True)
    token = Column(String(50), nullable=True)
    lot_size = Column(Integer, default=1, nullable=False)
    tick_size = Column(Float, default=0.05, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)


class MarketBar(Base):
    __tablename__ = "market_bars"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    symbol = Column(String(50), nullable=False, index=True)
    timeframe = Column(String(20), default="1d", nullable=False)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    open = Column(Float, nullable=False)
    high = Column(Float, nullable=False)
    low = Column(Float, nullable=False)
    close = Column(Float, nullable=False)
    volume = Column(Float, default=0.0, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    __table_args__ = (
        Index("idx_bar_sym_time", "symbol", "timestamp", unique=True),
    )


class MarketTick(Base):
    __tablename__ = "market_ticks"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    symbol = Column(String(50), nullable=False, index=True)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    last_price = Column(Float, nullable=False)
    volume = Column(Float, default=0.0, nullable=False)
    bid = Column(Float, nullable=True)
    ask = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)


class StrategyDefinition(Base):
    __tablename__ = "strategy_definitions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    strategy_key = Column(String(100), unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=False)
    family = Column(String(100), nullable=False, index=True) # trend, momentum, mean_reversion, factor
    description = Column(Text, nullable=True)
    status = Column(String(50), default="IDEA", nullable=False, index=True)
    allocation_pct = Column(Float, default=0.0, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)


class StrategyVersion(Base):
    __tablename__ = "strategy_versions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    strategy_id = Column(String(36), ForeignKey("strategy_definitions.id"), nullable=False, index=True)
    version = Column(String(50), nullable=False)
    parameters = Column(JSON, nullable=False)
    code_hash = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)


class StrategyStatusHistory(Base):
    __tablename__ = "strategy_status"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    strategy_id = Column(String(36), ForeignKey("strategy_definitions.id"), nullable=False, index=True)
    old_status = Column(String(50), nullable=False)
    new_status = Column(String(50), nullable=False)
    reason = Column(Text, nullable=False)
    metrics_snapshot = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)


class Experiment(Base):
    __tablename__ = "experiments"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    title = Column(String(200), nullable=False)
    hypothesis = Column(Text, nullable=False)
    economic_reason = Column(Text, nullable=True)
    strategy_key = Column(String(100), nullable=False, index=True)
    parameters = Column(JSON, nullable=False)
    status = Column(String(50), default="PENDING", nullable=False) # PENDING, RUNNING, COMPLETED, REJECTED, PROMOTED
    decision = Column(String(50), nullable=True) # REJECT, CONTINUE, PAPER
    metrics = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)


class Backtest(Base):
    __tablename__ = "backtests"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    experiment_id = Column(String(36), ForeignKey("experiments.id"), nullable=True, index=True)
    strategy_key = Column(String(100), nullable=False, index=True)
    symbol = Column(String(50), nullable=True)
    start_date = Column(DateTime(timezone=True), nullable=False)
    end_date = Column(DateTime(timezone=True), nullable=False)
    initial_capital = Column(Float, default=100000.0, nullable=False)
    cost_model = Column(String(50), default="nse_equity_v1", nullable=False)
    slippage_bps = Column(Float, default=10.0, nullable=False)
    parameters = Column(JSON, nullable=False)
    metrics = Column(JSON, nullable=False) # Sharpe, Sortino, Calmar, MaxDD, WinRate, etc.
    equity_curve = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)


class BacktestTrade(Base):
    __tablename__ = "backtest_trades"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    backtest_id = Column(String(36), ForeignKey("backtests.id"), nullable=False, index=True)
    symbol = Column(String(50), nullable=False, index=True)
    direction = Column(String(10), default="LONG", nullable=False)
    entry_time = Column(DateTime(timezone=True), nullable=False)
    entry_price = Column(Float, nullable=False)
    exit_time = Column(DateTime(timezone=True), nullable=False)
    exit_price = Column(Float, nullable=False)
    quantity = Column(Integer, nullable=False)
    gross_pnl = Column(Float, nullable=False)
    net_pnl = Column(Float, nullable=False)
    fees = Column(Float, default=0.0, nullable=False)
    return_pct = Column(Float, nullable=False)
    exit_reason = Column(String(100), nullable=True)


class WalkForwardResult(Base):
    __tablename__ = "walk_forward_results"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    backtest_id = Column(String(36), ForeignKey("backtests.id"), nullable=False, index=True)
    fold_index = Column(Integer, nullable=False)
    train_start = Column(DateTime(timezone=True), nullable=False)
    train_end = Column(DateTime(timezone=True), nullable=False)
    test_start = Column(DateTime(timezone=True), nullable=False)
    test_end = Column(DateTime(timezone=True), nullable=False)
    train_metrics = Column(JSON, nullable=False)
    test_metrics = Column(JSON, nullable=False)
    validation_decay = Column(Float, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)


class MonteCarloResult(Base):
    __tablename__ = "monte_carlo_results"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    backtest_id = Column(String(36), ForeignKey("backtests.id"), nullable=False, index=True)
    simulations = Column(Integer, default=1000, nullable=False)
    p5_drawdown = Column(Float, nullable=False)
    p50_drawdown = Column(Float, nullable=False)
    p95_drawdown = Column(Float, nullable=False)
    ruin_probability = Column(Float, nullable=False)
    return_dispersion = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)


class Signal(Base):
    __tablename__ = "signals"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    strategy_key = Column(String(100), nullable=False, index=True)
    version = Column(String(50), default="1.0.0", nullable=False)
    symbol = Column(String(50), nullable=False, index=True)
    direction = Column(String(10), default="LONG", nullable=False)
    strength = Column(Float, nullable=False) # 0.0 to 1.0
    price_at_signal = Column(Float, nullable=False)
    market_regime = Column(String(50), nullable=False)
    metadata_json = Column(JSON, nullable=True)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)


class Portfolio(Base):
    __tablename__ = "portfolios"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(100), default="MAIN", nullable=False)
    trading_mode = Column(String(20), default="PAPER", nullable=False)
    cash = Column(Float, default=100000.0, nullable=False)
    initial_cash = Column(Float, default=100000.0, nullable=False)
    realized_pnl = Column(Float, default=0.0, nullable=False)
    unrealized_pnl = Column(Float, default=0.0, nullable=False)
    equity = Column(Float, default=100000.0, nullable=False)
    high_water_mark = Column(Float, default=100000.0, nullable=False)
    current_drawdown_pct = Column(Float, default=0.0, nullable=False)
    max_drawdown_pct = Column(Float, default=0.0, nullable=False)
    gross_exposure_pct = Column(Float, default=0.0, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)


class PortfolioSnapshot(Base):
    __tablename__ = "portfolio_snapshots"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    portfolio_id = Column(String(36), ForeignKey("portfolios.id"), nullable=False, index=True)
    timestamp = Column(DateTime(timezone=True), default=utc_now, nullable=False, index=True)
    cash = Column(Float, nullable=False)
    equity = Column(Float, nullable=False)
    daily_pnl = Column(Float, default=0.0, nullable=False)
    total_pnl = Column(Float, default=0.0, nullable=False)
    drawdown_pct = Column(Float, default=0.0, nullable=False)
    gross_exposure_pct = Column(Float, default=0.0, nullable=False)
    positions_count = Column(Integer, default=0, nullable=False)
    metrics = Column(JSON, nullable=True)


class Position(Base):
    __tablename__ = "positions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    portfolio_id = Column(String(36), ForeignKey("portfolios.id"), nullable=False, index=True)
    symbol = Column(String(50), nullable=False, index=True)
    sector = Column(String(100), nullable=True)
    strategy_key = Column(String(100), nullable=False, index=True)
    quantity = Column(Integer, nullable=False)
    average_entry_price = Column(Float, nullable=False)
    current_price = Column(Float, nullable=False)
    unrealized_pnl = Column(Float, default=0.0, nullable=False)
    realized_pnl = Column(Float, default=0.0, nullable=False)
    stop_loss = Column(Float, nullable=True)
    take_profit = Column(Float, nullable=True)
    is_open = Column(Boolean, default=True, nullable=False, index=True)
    entry_time = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    exit_time = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)


class TradeProposal(Base):
    __tablename__ = "trade_proposals"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    signal_id = Column(String(36), ForeignKey("signals.id"), nullable=False, index=True)
    strategy_key = Column(String(100), nullable=False)
    symbol = Column(String(50), nullable=False, index=True)
    direction = Column(String(10), default="LONG", nullable=False)
    proposed_quantity = Column(Integer, nullable=False)
    proposed_price = Column(Float, nullable=False)
    raw_kelly_pct = Column(Float, nullable=False)
    fractional_kelly_pct = Column(Float, nullable=False)
    win_probability = Column(Float, nullable=False)
    average_win = Column(Float, nullable=False)
    average_loss = Column(Float, nullable=False)
    volatility_adjustment = Column(Float, default=1.0, nullable=False)
    correlation_adjustment = Column(Float, default=1.0, nullable=False)
    status = Column(String(50), default="PROPOSED", nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)


class RiskDecision(Base):
    __tablename__ = "risk_decisions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    proposal_id = Column(String(36), ForeignKey("trade_proposals.id"), nullable=False, index=True)
    approved = Column(Boolean, nullable=False)
    requested_quantity = Column(Integer, nullable=False)
    approved_quantity = Column(Integer, nullable=False)
    decision = Column(String(20), nullable=False) # APPROVED, REJECTED, MODIFIED
    rules_applied = Column(JSON, nullable=False)
    reason = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)


class Order(Base):
    __tablename__ = "orders"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    client_order_id = Column(String(100), unique=True, nullable=False, index=True)
    broker_order_id = Column(String(100), nullable=True, index=True)
    strategy_key = Column(String(100), nullable=False, index=True)
    strategy_version = Column(String(50), default="1.0.0", nullable=False)
    signal_id = Column(String(36), nullable=True)
    risk_decision_id = Column(String(36), nullable=True)
    symbol = Column(String(50), nullable=False, index=True)
    side = Column(String(10), nullable=False) # BUY, SELL
    order_type = Column(String(20), default="LIMIT", nullable=False) # LIMIT, MARKET
    quantity = Column(Integer, nullable=False)
    filled_quantity = Column(Integer, default=0, nullable=False)
    price = Column(Float, nullable=False)
    average_fill_price = Column(Float, default=0.0, nullable=False)
    status = Column(String(30), default="SUBMITTED", nullable=False, index=True)
    trading_mode = Column(String(20), default="PAPER", nullable=False)
    broker = Column(String(30), default="paper", nullable=False)
    submitted_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    rejection_reason = Column(Text, nullable=True)


class OrderEvent(Base):
    __tablename__ = "order_events"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    order_id = Column(String(36), ForeignKey("orders.id"), nullable=False, index=True)
    event_type = Column(String(50), nullable=False)
    details = Column(JSON, nullable=False)
    timestamp = Column(DateTime(timezone=True), default=utc_now, nullable=False)


class Execution(Base):
    __tablename__ = "executions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    order_id = Column(String(36), ForeignKey("orders.id"), nullable=False, index=True)
    symbol = Column(String(50), nullable=False, index=True)
    side = Column(String(10), nullable=False)
    quantity = Column(Integer, nullable=False)
    price = Column(Float, nullable=False)
    fees = Column(Float, default=0.0, nullable=False)
    slippage_bps = Column(Float, default=0.0, nullable=False)
    executed_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)


class StrategyAllocation(Base):
    __tablename__ = "strategy_allocations"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    strategy_key = Column(String(100), unique=True, nullable=False, index=True)
    allocation_pct = Column(Float, nullable=False) # Target weight in portfolio (0.0 to 1.0)
    current_capital = Column(Float, default=0.0, nullable=False)
    confidence_multiplier = Column(Float, default=1.0, nullable=False) # 1.0, 0.75, 0.50, 0.25, 0.0
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)


class MarketRegimeState(Base):
    __tablename__ = "market_regimes"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    current_regime = Column(String(50), nullable=False, index=True)
    confidence = Column(Float, default=1.0, nullable=False)
    features = Column(JSON, nullable=False) # index trend, volatility, ATR, breadth
    timestamp = Column(DateTime(timezone=True), default=utc_now, nullable=False, index=True)


class RiskEvent(Base):
    __tablename__ = "risk_events"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    rule_name = Column(String(100), nullable=False)
    severity = Column(String(30), default="WARNING", nullable=False) # WARNING, CRITICAL, HALT
    details = Column(JSON, nullable=False)
    timestamp = Column(DateTime(timezone=True), default=utc_now, nullable=False)


class KillSwitchEvent(Base):
    __tablename__ = "kill_switch_events"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    triggered_by = Column(String(100), nullable=False)
    reason = Column(Text, nullable=False)
    active = Column(Boolean, default=True, nullable=False)
    timestamp = Column(DateTime(timezone=True), default=utc_now, nullable=False)


class ResearchIdea(Base):
    __tablename__ = "research_ideas"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    title = Column(String(200), nullable=False)
    hypothesis = Column(Text, nullable=False)
    economic_reason = Column(Text, nullable=True)
    features = Column(JSON, nullable=False)
    entry_logic = Column(Text, nullable=False)
    exit_logic = Column(Text, nullable=False)
    risks = Column(JSON, nullable=True)
    required_validation = Column(JSON, nullable=True)
    status = Column(String(50), default="NEW", nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)


class ResearchReport(Base):
    __tablename__ = "research_reports"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    experiment_id = Column(String(36), nullable=False, index=True)
    title = Column(String(200), nullable=False)
    content_md = Column(Text, nullable=False)
    decision = Column(String(50), nullable=False) # REJECT, CONTINUE, PAPER
    metrics = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)


class SystemEvent(Base):
    __tablename__ = "system_events"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    service = Column(String(100), nullable=False)
    event_type = Column(String(100), nullable=False)
    payload = Column(JSON, nullable=True)
    timestamp = Column(DateTime(timezone=True), default=utc_now, nullable=False)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    event_type = Column(String(50), nullable=False, index=True)
    correlation_id = Column(String(100), nullable=True, index=True)
    strategy_id = Column(String(100), nullable=True, index=True)
    signal_id = Column(String(100), nullable=True)
    order_id = Column(String(100), nullable=True)
    symbol = Column(String(50), nullable=True, index=True)
    action = Column(String(100), nullable=False)
    details = Column(JSON, nullable=False)
    timestamp = Column(DateTime(timezone=True), default=utc_now, nullable=False, index=True)
