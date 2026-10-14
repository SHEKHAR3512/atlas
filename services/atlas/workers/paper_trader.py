import asyncio
import logging
from datetime import datetime, timedelta, timezone
from services.atlas.core.config import config
from services.atlas.core.constants import AuditEventType, MarketRegime, StrategyStatus
from services.atlas.data.providers.historical import SyntheticNSEHistoricalProvider
from services.atlas.data.quality.validator import MarketDataValidator
from services.atlas.regime.detector import RegimeDetector
from services.atlas.strategies.registry import strategy_registry
from services.atlas.portfolio.allocator import PortfolioAllocator
from services.atlas.risk.engine import RiskEngine
from services.atlas.execution.engine import ExecutionEngine
from services.atlas.brokers.paper import PaperBroker
from services.atlas.db.session import async_session_factory
from services.atlas.models import (
    Portfolio,
    Position,
    Signal,
    TradeProposal,
    RiskDecision,
    Order,
    Execution,
    AuditLog,
    MarketRegimeState,
)
from sqlalchemy import select

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("atlas.paper_trader")


class AutonomousPaperTrader:
    """
    Autonomous Paper Trading Engine.
    Executes continuous market cycles:
      Data Feed -> Regime Detection -> Strategy Signals -> Fractional Kelly ->
      Risk Engine Validation -> Paper Broker Execution -> Portfolio Update -> Audit Trail
    """

    def __init__(self):
        self.data_provider = SyntheticNSEHistoricalProvider()
        self.regime_detector = RegimeDetector()
        self.allocator = PortfolioAllocator()
        self.risk_engine = RiskEngine()
        self.paper_broker = PaperBroker(initial_cash=config.settings.INITIAL_PAPER_CAPITAL)
        self.execution_engine = ExecutionEngine(broker=self.paper_broker)

    async def initialize(self):
        await self.paper_broker.connect()
        logger.info("AutonomousPaperTrader initialized in PAPER mode.")

    async def execute_cycle(self) -> dict:
        logger.info("--- Starting Autonomous Paper Trading Cycle ---")
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=365)

        symbols = [s["symbol"] for s in config.symbols] or ["RELIANCE", "TCS", "HDFCBANK", "INFY", "ICICIBANK"]

        # 1. Ingest and Validate Market Data
        market_data = {}
        for sym in symbols:
            raw_df = await self.data_provider.get_historical_bars(sym, start_date, end_date)
            try:
                clean_df = MarketDataValidator.validate_dataframe(raw_df, sym)
                market_data[sym] = clean_df
            except Exception as e:
                logger.warning(f"Data quality rejection for {sym}: {e}")

        if not market_data:
            logger.error("No valid market data available. Failing closed.")
            return {"status": "NO_DATA"}

        # 2. Market Regime Detection
        benchmark_sym = symbols[0]
        regime_info = self.regime_detector.detect_regime(market_data.get(benchmark_sym))
        current_regime = regime_info["regime"]
        logger.info(f"Detected Market Regime: {current_regime.value} (Confidence: {regime_info['confidence']*100:.0f}%)")

        # 3. Account and Portfolio Status
        account = await self.paper_broker.account()
        active_positions = await self.paper_broker.positions()
        equity = account["equity"]
        cash = account["cash"]

        logger.info(f"Portfolio Status: Equity Rs {equity:.2f} | Cash Rs {cash:.2f} | Active Positions: {len(active_positions)}")

        # 4. Generate Strategy Signals
        signals = strategy_registry.generate_all_signals(market_data, current_regime)
        logger.info(f"Generated {len(signals)} candidate signals across active strategies.")

        cycle_trades = []

        # 5. Pipeline: Signal -> Allocator -> Risk -> Execution
        for sig in signals:
            strat_meta = {}
            for item in strategy_registry.list_strategies():
                if item["id"] == sig.strategy_key:
                    strat_meta = item
                    break

            # Sizing with Fractional Kelly
            # Use representative sample trades
            historical_sample = [
                {"return_pct": 0.035}, {"return_pct": -0.015}, {"return_pct": 0.042},
                {"return_pct": -0.012}, {"return_pct": 0.028}, {"return_pct": 0.055},
                {"return_pct": -0.020}, {"return_pct": 0.018}, {"return_pct": -0.010},
                {"return_pct": 0.030}, {"return_pct": 0.022}, {"return_pct": -0.014},
            ]

            allocation = self.allocator.allocate_signal(
                signal=sig,
                portfolio_equity=equity,
                available_cash=cash,
                active_positions=active_positions,
                historical_trades=historical_sample,
                current_regime=current_regime,
                strategy_meta=strat_meta,
            )

            proposed_qty = allocation.get("proposed_quantity", 0)
            if proposed_qty <= 0:
                continue

            # Deterministic Risk Engine Evaluation
            risk_decision = self.risk_engine.evaluate_order_proposal(
                portfolio=account,
                positions=active_positions,
                signal=sig.model_dump(),
                market={"symbol": sig.symbol, "sector": "General"},
                strategy=strat_meta,
                proposed_order={
                    "symbol": sig.symbol,
                    "side": "BUY",
                    "quantity": proposed_qty,
                    "price": sig.price,
                }
            )

            if not risk_decision["approved"]:
                logger.info(f"Risk Engine REJECTED order for {sig.symbol}: {risk_decision['reason']}")
                continue

            approved_qty = risk_decision["approved_quantity"]
            if approved_qty <= 0:
                continue

            # Execution
            order_res = await self.execution_engine.execute_approved_order(
                symbol=sig.symbol,
                side="BUY",
                quantity=approved_qty,
                price=sig.price,
                strategy_key=sig.strategy_key,
                signal_id=None,
                risk_decision_id=None,
            )

            if order_res.get("status") == "FILLED":
                cycle_trades.append({
                    "symbol": sig.symbol,
                    "quantity": approved_qty,
                    "price": order_res.get("average_fill_price"),
                    "fees": order_res.get("fees"),
                    "strategy": sig.strategy_key,
                })

                # Refresh positions & account
                account = await self.paper_broker.account()
                active_positions = await self.paper_broker.positions()
                equity = account["equity"]
                cash = account["cash"]

                # Audit Log record
                try:
                    async with async_session_factory() as session:
                        audit_entry = AuditLog(
                            event_type=AuditEventType.ORDER_FILLED.value,
                            strategy_id=sig.strategy_key,
                            symbol=sig.symbol,
                            action="PAPER_BUY_FILLED",
                            details={
                                "order_id": order_res.get("order_id"),
                                "quantity": approved_qty,
                                "price": order_res.get("average_fill_price"),
                                "fees": order_res.get("fees"),
                                "kelly_fraction": allocation.get("fractional_kelly_pct"),
                                "regime": current_regime.value,
                                "risk_rules": risk_decision.get("rules"),
                            }
                        )
                        session.add(audit_entry)
                        await session.commit()
                except Exception as e:
                    logger.debug(f"Audit log save note: {e}")

        logger.info(f"Cycle completed. Executed {len(cycle_trades)} paper orders.")
        return {
            "regime": current_regime.value,
            "equity": equity,
            "cash": cash,
            "positions_count": len(active_positions),
            "trades_executed": len(cycle_trades),
            "trades": cycle_trades,
        }


async def run_paper_loop(iterations: int = 3, interval_seconds: int = 5):
    trader = AutonomousPaperTrader()
    await trader.initialize()

    logger.info("==================================================")
    logger.info("       ATLAS AUTONOMOUS PAPER TRADING ENGINE      ")
    logger.info("       TRADING_MODE: PAPER | REAL MONEY: NO       ")
    logger.info("==================================================")

    for i in range(iterations):
        logger.info(f"\n--- Paper Iteration {i+1}/{iterations} ---")
        await trader.execute_cycle()
        if i < iterations - 1:
            await asyncio.sleep(interval_seconds)

    logger.info("Paper trading loop finished successfully.")


def main():
    asyncio.run(run_paper_loop(iterations=2, interval_seconds=2))


if __name__ == "__main__":
    main()
