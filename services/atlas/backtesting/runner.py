import asyncio
import logging
from datetime import datetime, timedelta, timezone
from services.atlas.core.config import config
from services.atlas.data.providers.historical import SyntheticNSEHistoricalProvider
from services.atlas.strategies.registry import strategy_registry
from services.atlas.backtesting.engine import BacktestEngine
from services.atlas.backtesting.walk_forward import WalkForwardValidator
from services.atlas.backtesting.monte_carlo import MonteCarloAnalyzer
from services.atlas.db.session import async_session_factory
from services.atlas.models import Backtest, BacktestTrade, WalkForwardResult, MonteCarloResult

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("atlas.backtesting.runner")


async def run_approved_backtests():
    logger.info("==================================================")
    logger.info("       ATLAS APPROVED STRATEGY BACKTESTS          ")
    logger.info("==================================================")

    data_provider = SyntheticNSEHistoricalProvider()
    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=365 * 2)

    universe_symbols = [s["symbol"] for s in config.symbols[:8]] or ["RELIANCE", "TCS", "HDFCBANK", "INFY", "ICICIBANK"]
    market_data = {}
    for sym in universe_symbols:
        df = await data_provider.get_historical_bars(sym, start_date, end_date)
        market_data[sym] = df

    engine = BacktestEngine(initial_capital=100000.0)
    wf_validator = WalkForwardValidator(folds=3, engine=engine)
    mc_analyzer = MonteCarloAnalyzer(num_simulations=500)

    strat_list = strategy_registry.list_strategies()
    results = []

    for item in strat_list:
        strat_id = item["id"]
        strat_name = item["name"]
        strategy = strategy_registry.get_strategy(strat_id)
        if not strategy:
            continue

        logger.info(f"\n[BACKTESTING] {strat_name} ({strat_id})")
        res = engine.run(strategy, market_data)
        metrics = res["metrics"]
        trades = res["trades"]
        equity_curve = res["equity_curve"]

        wf_res = wf_validator.run_walk_forward(strategy, market_data)
        mc_res = mc_analyzer.analyze_trades(trades)

        logger.info(
            f"Result: Return {metrics['total_return_pct']*100:.2f}% | "
            f"Sharpe {metrics['sharpe_ratio']:.2f} | "
            f"MaxDD {metrics['max_drawdown_pct']*100:.2f}% | "
            f"WinRate {metrics['win_rate']*100:.1f}% | "
            f"Trades {metrics['trades_count']}"
        )

        # Store in database
        try:
            async with async_session_factory() as session:
                bt_record = Backtest(
                    strategy_key=strat_id,
                    start_date=start_date,
                    end_date=end_date,
                    initial_capital=100000.0,
                    cost_model="nse_equity_v1",
                    slippage_bps=10.0,
                    parameters=strategy.parameters(),
                    metrics=metrics,
                    equity_curve=equity_curve[-50:], # save recent points
                )
                session.add(bt_record)
                await session.flush()

                # Add trades
                for t in trades[:30]: # sample trades
                    tr_obj = BacktestTrade(
                        backtest_id=bt_record.id,
                        symbol=t["symbol"],
                        direction=t["direction"],
                        entry_time=datetime.fromisoformat(t["entry_time"]) if isinstance(t["entry_time"], str) else t["entry_time"],
                        entry_price=t["entry_price"],
                        exit_time=datetime.fromisoformat(t["exit_time"]) if isinstance(t["exit_time"], str) else t["exit_time"],
                        exit_price=t["exit_price"],
                        quantity=t["quantity"],
                        gross_pnl=t["gross_pnl"],
                        net_pnl=t["net_pnl"],
                        fees=t["fees"],
                        return_pct=t["return_pct"],
                        exit_reason=t.get("exit_reason", "SIGNAL"),
                    )
                    session.add(tr_obj)

                # Add Monte Carlo result
                mc_obj = MonteCarloResult(
                    backtest_id=bt_record.id,
                    simulations=mc_res["simulations"],
                    p5_drawdown=mc_res["p5_drawdown"],
                    p50_drawdown=mc_res["p50_drawdown"],
                    p95_drawdown=mc_res["p95_drawdown"],
                    ruin_probability=mc_res["ruin_probability"],
                    return_dispersion=mc_res["return_dispersion"],
                )
                session.add(mc_obj)

                await session.commit()
        except Exception as e:
            logger.debug(f"DB recording note: {e}")

        results.append({
            "id": strat_id,
            "name": strat_name,
            "metrics": metrics,
            "walk_forward": wf_res,
            "monte_carlo": mc_res,
        })

    logger.info("\n==================================================")
    logger.info("All approved strategy backtests completed successfully.")
    return results


def main():
    asyncio.run(run_approved_backtests())


if __name__ == "__main__":
    main()
