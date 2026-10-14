import asyncio
import logging
from datetime import datetime, timedelta, timezone
from services.atlas.core.config import config
from services.atlas.data.providers.historical import SyntheticNSEHistoricalProvider
from services.atlas.research.candidate_factory import CandidateFactory
from services.atlas.research.promotion import PromotionPipeline
from services.atlas.research.agent import ResearchAgent
from services.atlas.backtesting.engine import BacktestEngine
from services.atlas.backtesting.walk_forward import WalkForwardValidator
from services.atlas.backtesting.monte_carlo import MonteCarloAnalyzer
from services.atlas.strategies.registry import STRATEGY_CLASS_MAP
from services.atlas.db.session import async_session_factory
from services.atlas.models import Experiment, ResearchReport

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("atlas.research.runner")


async def run_research_cycle(families=None):
    if families is None:
        families = ["trend", "momentum", "mean_reversion", "breakout"]

    logger.info("==================================================")
    logger.info("   ATLAS AUTONOMOUS RESEARCH LAB - EXPERIMENTS    ")
    logger.info("==================================================")

    data_provider = SyntheticNSEHistoricalProvider()
    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=365 * 2) # 2 years historical data

    # Load universe
    universe_symbols = [s["symbol"] for s in config.symbols[:6]] or ["RELIANCE", "TCS", "HDFCBANK", "INFY", "ICICIBANK"]
    market_data = {}
    for sym in universe_symbols:
        df = await data_provider.get_historical_bars(sym, start_date, end_date)
        market_data[sym] = df

    engine = BacktestEngine(initial_capital=100000.0)
    wf_validator = WalkForwardValidator(folds=3, engine=engine)
    mc_analyzer = MonteCarloAnalyzer(num_simulations=500)
    promotion_pipeline = PromotionPipeline()
    research_agent = ResearchAgent()

    results = []

    for family in families:
        cand = CandidateFactory.generate_candidate(family=family)
        cand_id = cand["candidate_id"]
        title = cand["title"]
        params = cand["parameters"]

        logger.info(f"\n[RUNNING EXPERIMENT] {title}")
        strat_cls = STRATEGY_CLASS_MAP.get(family)
        if not strat_cls:
            continue
        strategy_inst = strat_cls(cand_id, params)

        # 1. Backtest
        bt_res = engine.run(strategy_inst, market_data)
        metrics = bt_res["metrics"]

        # 2. Walk-Forward
        wf_res = wf_validator.run_walk_forward(strategy_inst, market_data)

        # 3. Monte Carlo
        mc_res = mc_analyzer.analyze_trades(bt_res["trades"])

        # 4. Evaluation
        is_promoted, reason, eval_meta = promotion_pipeline.evaluate_candidate_for_paper(
            backtest_metrics=metrics,
            walk_forward_results=wf_res,
            monte_carlo_results=mc_res,
        )

        decision = "PAPER" if is_promoted else "REJECT"

        # 5. Generate Report
        report_md = await research_agent.generate_research_report(
            experiment_title=title,
            hypothesis=cand["hypothesis"],
            parameters=params,
            backtest_metrics=metrics,
            walk_forward=wf_res,
            monte_carlo=mc_res,
            decision=f"{decision} ({reason})",
        )

        # Save to database
        try:
            async with async_session_factory() as session:
                exp_obj = Experiment(
                    id=cand_id,
                    title=title,
                    hypothesis=cand["hypothesis"],
                    strategy_key=cand_id,
                    parameters=params,
                    status="COMPLETED",
                    decision=decision,
                    metrics={
                        "backtest": metrics,
                        "walk_forward": {
                            "avg_train_sharpe": wf_res["avg_train_sharpe"],
                            "avg_test_sharpe": wf_res["avg_test_sharpe"],
                            "decay": wf_res["overall_validation_decay"],
                        },
                        "monte_carlo": {
                            "p50_dd": mc_res["p50_drawdown"],
                            "ruin_prob": mc_res["ruin_probability"],
                        },
                        "decision_reason": reason,
                    }
                )
                session.add(exp_obj)

                rep_obj = ResearchReport(
                    experiment_id=cand_id,
                    title=title,
                    content_md=report_md,
                    decision=decision,
                    metrics=metrics,
                )
                session.add(rep_obj)
                await session.commit()
        except Exception as e:
            logger.debug(f"DB recording note: {e}")

        logger.info(f"-> Decision: {decision} | Sharpe: {metrics.get('sharpe_ratio'):.2f} | Reason: {reason}")
        results.append({
            "id": cand_id,
            "title": title,
            "decision": decision,
            "sharpe": metrics.get("sharpe_ratio"),
            "max_dd": metrics.get("max_drawdown_pct"),
            "reason": reason,
        })

    logger.info("\n==================================================")
    logger.info(f"Research cycle complete. {len(results)} experiments evaluated.")
    return results


def main():
    asyncio.run(run_research_cycle())


if __name__ == "__main__":
    main()
