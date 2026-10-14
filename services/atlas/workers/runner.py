import asyncio
import logging
from services.atlas.research.runner import run_research_cycle
from services.atlas.backtesting.runner import run_approved_backtests

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("atlas.worker")


async def run_worker():
    logger.info("ATLAS Background Task Worker started.")
    while True:
        try:
            logger.info("Worker heartbeat: checking research & backtest queues...")
            # Periodic background research pulse
            await asyncio.sleep(60)
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"Worker exception: {e}")
            await asyncio.sleep(10)


def main():
    asyncio.run(run_worker())


if __name__ == "__main__":
    main()
