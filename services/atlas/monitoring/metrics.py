from prometheus_client import Counter, Gauge

# Prometheus Quantitative & System Telemetry Metrics (Section 68)
PORTFOLIO_VALUE = Gauge("atlas_portfolio_value", "Current portfolio total equity in INR")
DAILY_PNL = Gauge("atlas_daily_pnl", "Current day's realized + unrealized P&L in INR")
PORTFOLIO_DRAWDOWN = Gauge("atlas_drawdown", "Current peak-to-trough portfolio drawdown percentage")
GROSS_EXPOSURE = Gauge("atlas_gross_exposure", "Current gross portfolio exposure percentage")
OPEN_POSITIONS = Gauge("atlas_open_positions", "Number of currently active open equity positions")

ORDERS_TOTAL = Counter("atlas_orders_total", "Total count of orders submitted", ["side", "broker"])
ORDERS_REJECTED = Counter("atlas_orders_rejected", "Total count of rejected orders", ["reason"])
SIGNALS_TOTAL = Counter("atlas_signals_total", "Total strategy trading signals generated", ["strategy"])

STRATEGY_SHARPE = Gauge("atlas_strategy_sharpe", "Strategy rolling validated Sharpe ratio", ["strategy"])
STRATEGY_DRAWDOWN = Gauge("atlas_strategy_drawdown", "Strategy maximum drawdown percentage", ["strategy"])

MARKET_FEED_AGE = Gauge("atlas_market_feed_age_seconds", "Age of latest market quote in seconds")
BROKER_ERRORS_TOTAL = Counter("atlas_broker_errors_total", "Total broker communication errors", ["broker"])
RISK_REJECTIONS_TOTAL = Counter("atlas_risk_rejections_total", "Total orders blocked by Risk Engine", ["rule"])
