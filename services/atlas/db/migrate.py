import asyncio
import logging
from services.atlas.db.session import engine, Base
import services.atlas.models # ensure models are registered

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("atlas.migrate")


async def run_migrations():
    logger.info("Initializing database schema...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database schema applied successfully.")


def main():
    asyncio.run(run_migrations())


if __name__ == "__main__":
    main()
