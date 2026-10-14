import logging
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import declarative_base
from services.atlas.core.config import config, get_project_root

logger = logging.getLogger("atlas.db")

Base = declarative_base()

import socket
from urllib.parse import urlparse

# Default fallback SQLite path
sqlite_path = get_project_root() / "atlas.db"
sqlite_url = f"sqlite+aiosqlite:///{sqlite_path}"

# Determine database URL
raw_db_url = config.settings.DATABASE_URL
if raw_db_url.startswith("postgresql://"):
    raw_db_url = raw_db_url.replace("postgresql://", "postgresql+psycopg://")
elif raw_db_url.startswith("postgresql+psycopg2://"):
    raw_db_url = raw_db_url.replace("postgresql+psycopg2://", "postgresql+psycopg://")

# Check if postgres host is resolvable; if not, use SQLite fallback
db_url = raw_db_url
try:
    parsed = urlparse(raw_db_url.replace("+psycopg", ""))
    if parsed.hostname and parsed.hostname != "localhost" and parsed.hostname != "127.0.0.1":
        socket.gethostbyname(parsed.hostname)
except Exception as e:
    logger.info(f"Database host {parsed.hostname} not reachable ({e}). Using SQLite fallback: {sqlite_url}")
    db_url = sqlite_url

engine = create_async_engine(
    db_url,
    echo=False,
    future=True,
    pool_pre_ping=True
)
async_session_factory = async_sessionmaker(
    engine,
    expire_on_commit=False,
    class_=AsyncSession
)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def check_db_health() -> bool:
    global engine, async_session_factory
    try:
        from sqlalchemy import text
        async with async_session_factory() as session:
            await session.execute(text("SELECT 1"))
        return True
    except Exception as e:
        logger.warning(f"Database health check failed on primary URL: {e}")
        # If postgres failed, switch global engine to SQLite fallback
        if config.settings.SQLITE_FALLBACK and "sqlite" not in str(engine.url):
            logger.info(f"Switching database engine to fallback SQLite: {sqlite_url}")
            engine = create_async_engine(sqlite_url, echo=False, future=True)
            async_session_factory = async_sessionmaker(
                engine,
                expire_on_commit=False,
                class_=AsyncSession
            )
            try:
                from sqlalchemy import text
                async with async_session_factory() as session:
                    await session.execute(text("SELECT 1"))
                return True
            except Exception as e2:
                logger.error(f"SQLite fallback also failed: {e2}")
                return False
        return False
