import logging
from typing import Any, Dict, Optional
from services.atlas.ai.base import AIProvider
from services.atlas.ai.disabled import DisabledAIProvider
from services.atlas.ai.ollama import OllamaProvider
from services.atlas.core.config import config

logger = logging.getLogger("atlas.research.agent")


class ResearchAgent:
    """
    Isolated Quantitative Research Agent.
    Strictly sandboxed: CANNOT place orders or contact brokers.
    Produces structured hypotheses, experiment plans, and research reports.
    """

    def __init__(self, ai_provider: Optional[AIProvider] = None):
        if ai_provider:
            self.ai = ai_provider
        elif config.settings.AI_PROVIDER == "ollama":
            self.ai = OllamaProvider()
        else:
            self.ai = DisabledAIProvider()

    async def formulate_hypothesis(self, strategy_family: str) -> Dict[str, Any]:
        prompt = (
            f"Generate an economic and quantitative hypothesis for an Indian equity {strategy_family} strategy "
            f"operating on liquid NSE cash equities. Consider transaction costs and risk-adjusted return."
        )
        schema = {
            "hypothesis": "string",
            "economic_reason": "string",
            "features": ["string"],
            "entry_logic": "string",
            "exit_logic": "string",
            "risks": ["string"],
            "required_validation": ["string"],
        }
        return await self.ai.structured_generate(prompt, schema)

    async def generate_research_report(
        self,
        experiment_title: str,
        hypothesis: str,
        parameters: Dict[str, Any],
        backtest_metrics: Dict[str, Any],
        walk_forward: Dict[str, Any],
        monte_carlo: Dict[str, Any],
        decision: str,
    ) -> str:
        summary_payload = f"""
# ATLAS Quantitative Research Report: {experiment_title}

## 1. Hypothesis
{hypothesis}

## 2. Parameters
{parameters}

## 3. Backtest Net Performance
- Total Return: {backtest_metrics.get('total_return_pct', 0.0)*100:.2f}%
- CAGR: {backtest_metrics.get('cagr_pct', 0.0)*100:.2f}%
- Sharpe Ratio: {backtest_metrics.get('sharpe_ratio', 0.0):.2f}
- Sortino Ratio: {backtest_metrics.get('sortino_ratio', 0.0):.2f}
- Max Drawdown: {backtest_metrics.get('max_drawdown_pct', 0.0)*100:.2f}%
- Profit Factor: {backtest_metrics.get('profit_factor', 0.0):.2f}
- Win Rate: {backtest_metrics.get('win_rate', 0.0)*100:.2f}%
- Expectancy: {backtest_metrics.get('expectancy', 0.0):.4f}
- Trades Count: {backtest_metrics.get('trades_count', 0)}

## 4. Walk-Forward Validation (Out-of-Sample)
- Average In-Sample Sharpe: {walk_forward.get('avg_train_sharpe', 0.0):.2f}
- Average Out-of-Sample Sharpe: {walk_forward.get('avg_test_sharpe', 0.0):.2f}
- Validation Decay: {walk_forward.get('overall_validation_decay', 0.0)*100:.2f}%
- Walk-Forward Robust: {walk_forward.get('is_robust', False)}

## 5. Monte Carlo Resampling & Tail Risk
- P5 Drawdown: {monte_carlo.get('p5_drawdown', 0.0)*100:.2f}%
- P50 (Median) Drawdown: {monte_carlo.get('p50_drawdown', 0.0)*100:.2f}%
- P95 Drawdown: {monte_carlo.get('p95_drawdown', 0.0)*100:.2f}%
- Ruin Probability: {monte_carlo.get('ruin_probability', 0.0)*100:.2f}%
- Acceptable Tail Risk: {monte_carlo.get('is_acceptable_tail_risk', False)}

## 6. Decision
**{decision}**
"""
        return summary_payload.strip()
