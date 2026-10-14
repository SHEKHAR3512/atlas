import asyncio
import logging
from datetime import datetime, timedelta, timezone
from services.atlas.core.config import config
from services.atlas.db.session import engine, async_session_factory, Base
from services.atlas.models import (
    Instrument,
    StrategyDefinition,
    StrategyVersion,
    Portfolio,
    MarketBar,
)
from services.atlas.data.providers.historical import SyntheticNSEHistoricalProvider
from sqlalchemy import select

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("atlas.data.seed")


async def seed_all():
    logger.info("Initializing database schema...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session_factory() as session:
        # 1. Seed Portfolio
        res = await session.execute(select(Portfolio).where(Portfolio.name == "MAIN"))
        portfolio = res.scalar_one_or_none()
        if not portfolio:
            logger.info("Seeding main portfolio with Rs 100,000 paper capital...")
            portfolio = Portfolio(
                name="MAIN",
                trading_mode="PAPER",
                cash=config.settings.INITIAL_PAPER_CAPITAL,
                initial_cash=config.settings.INITIAL_PAPER_CAPITAL,
                equity=config.settings.INITIAL_PAPER_CAPITAL,
                high_water_mark=config.settings.INITIAL_PAPER_CAPITAL,
            )
            session.add(portfolio)

        # 2. Seed Instruments
        logger.info("Seeding NSE Liquid Universe instruments...")
        for sym_meta in config.symbols:
            sym = sym_meta["symbol"]
            existing = await session.execute(select(Instrument).where(Instrument.symbol == sym))
            if not existing.scalar_one_or_none():
                inst = Instrument(
                    symbol=sym,
                    name=sym_meta.get("name", sym),
                    exchange="NSE",
                    sector=sym_meta.get("sector", "General"),
                    token=sym_meta.get("token"),
                    lot_size=sym_meta.get("lot_size", 1),
                )
                session.add(inst)

        # 3. Seed Strategies
        logger.info("Seeding Approved Quantitative Strategies...")
        for strat_entry in config.strategies_yaml.get("strategies", []):
            strat_key = strat_entry["id"]
            existing_strat = await session.execute(
                select(StrategyDefinition).where(StrategyDefinition.strategy_key == strat_key)
            )
            if not existing_strat.scalar_one_or_none():
                strat_def = StrategyDefinition(
                    strategy_key=strat_key,
                    name=strat_entry.get("name", strat_key),
                    family=strat_entry.get("family", "custom"),
                    description=strat_entry.get("name"),
                    status=strat_entry.get("status", "APPROVED"),
                    allocation_pct=strat_entry.get("allocation_pct", 0.25),
                )
                session.add(strat_def)
                await session.flush()

                v_obj = StrategyVersion(
                    strategy_id=strat_def.id,
                    version=strat_entry.get("version", "1.0.0"),
                    parameters=strat_entry.get("parameters", {}),
                    is_active=True,
                )
                session.add(v_obj)

        await session.commit()

    # 4. Seed Historical Market Bars for Universe
    logger.info("Generating and caching historical NSE daily bars...")
    data_provider = SyntheticNSEHistoricalProvider()
    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=365 * 2)

    symbols = [s["symbol"] for s in config.symbols[:6]]
    async with async_session_factory() as session:
        for sym in symbols:
            df = await data_provider.get_historical_bars(sym, start_date, end_date)
            # Sample bars to store in DB
            sample_df = df.tail(60)
            for _, row in sample_df.iterrows():
                bar_time = row["timestamp"]
                # Check duplicate
                existing_bar = await session.execute(
                    select(MarketBar).where(
                        (MarketBar.symbol == sym) & (MarketBar.timestamp == bar_time)
                    )
                )
                if not existing_bar.scalar_one_or_none():
                    bar = MarketBar(
                        symbol=sym,
                        timestamp=bar_time,
                        open=float(row["open"]),
                        high=float(row["high"]),
                        low=float(row["low"]),
                        close=float(row["close"]),
                        volume=float(row["volume"]),
                    )
                    session.add(bar)
        await session.commit()

    logger.info("Database seeding complete!")


def main():
    asyncio.run(seed_all())


if __name__ == "__main__":
    main()
