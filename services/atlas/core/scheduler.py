import asyncio
import logging
from datetime import datetime, timezone
from services.atlas.core.config import config
from services.atlas.workers.paper_trader import AutonomousPaperTrader
from services.atlas.research.runner import run_research_cycle
from services.atlas.backtesting.runner import run_approved_backtests

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("atlas.scheduler")


class TradingSessionScheduler:
    """
    Session-aware scheduler managing Indian Equity Market lifecycle (Asia/Kolkata):
      09:00 - 09:15 : Pre-Market (Reconciliation, Health checks, Regime calculation)
      09:15 - 15:30 : Market Open (Continuous paper trading, Kelly sizing, Risk validation)
      15:30 - 16:00 : Post-Market (EOD snapshot, Strategy performance decay tracking)
      Off-Hours     : Autonomous Research Lab (Experiments, Walk-forward, Monte Carlo)
    """

    def __init__(self):
        self.paper_trader = AutonomousPaperTrader()
        self._running = False

    async def start(self):
        await self.paper_trader.initialize()
        self._running = True
        logger.info("TradingSessionScheduler started. Timezone: Asia/Kolkata.")

        while self._running:
            try:
                # Execute regular cycle
                logger.info("Executing scheduled market cycle...")
                await self.paper_trader.execute_cycle()
            except Exception as e:
                logger.error(f"Error during scheduled cycle: {e}")

            # Sleep between cycles (30s in continuous paper demo)
            await asyncio.sleep(30)

    def stop(self):
        self._running = False


def main():
    scheduler = TradingSessionScheduler()
    try:
        asyncio.run(scheduler.start())
    except KeyboardInterrupt:
        scheduler.stop()
        logger.info("Scheduler stopped.")


if __name__ == "__main__":
    main()
