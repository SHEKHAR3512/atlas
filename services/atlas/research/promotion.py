import logging
from typing import Any, Dict, Tuple
from services.atlas.core.config import config
from services.atlas.core.constants import StrategyStatus

logger = logging.getLogger("atlas.research.promotion")


class PromotionPipeline:
    """
    Automated Strategy Lifecycle and Promotion/Degradation Controller.
    Rules:
      - Strategies cannot jump IDEA -> LIVE
      - Promotion requires passing multi-metric gates
      - Degradation reduces capital allocation (100% -> 75% -> 50% -> 25% -> 0%)
      - Edge decay triggers retirement while permanently preserving audit history
    """

    def __init__(self):
        thresholds = config.research_yaml.get("validation_thresholds", {})
        self.min_trades = int(thresholds.get("min_trades", 30))
        self.min_sharpe = float(thresholds.get("min_sharpe", 0.8))
        self.min_profit_factor = float(thresholds.get("min_profit_factor", 1.20))
        self.max_drawdown_pct = float(thresholds.get("max_drawdown_pct", 0.15))
        self.min_expectancy = float(thresholds.get("min_expectancy", 0.002))
        self.max_validation_decay_pct = float(thresholds.get("max_validation_decay_pct", 0.35))

    def evaluate_candidate_for_paper(
        self,
        backtest_metrics: Dict[str, Any],
        walk_forward_results: Dict[str, Any],
        monte_carlo_results: Dict[str, Any],
    ) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Validates whether an experimental strategy candidate meets criteria
        to be promoted from VALIDATED to PAPER trading.
        """
        rejection_reasons = []

        trades = backtest_metrics.get("trades_count", 0)
        if trades < self.min_trades:
            rejection_reasons.append(f"Insufficient trade sample: {trades} < {self.min_trades}")

        sharpe = backtest_metrics.get("sharpe_ratio", 0.0)
        if sharpe < self.min_sharpe:
            rejection_reasons.append(f"Sharpe ratio too low: {sharpe} < {self.min_sharpe}")

        pf = backtest_metrics.get("profit_factor", 0.0)
        if pf < self.min_profit_factor:
            rejection_reasons.append(f"Profit factor too low: {pf} < {self.min_profit_factor}")

        max_dd = backtest_metrics.get("max_drawdown_pct", 1.0)
        if max_dd > self.max_drawdown_pct:
            rejection_reasons.append(f"Max drawdown too high: {max_dd*100:.1f}% > {self.max_drawdown_pct*100:.1f}%")

        expectancy = backtest_metrics.get("expectancy", -1.0)
        if expectancy <= self.min_expectancy:
            rejection_reasons.append(f"Expectancy not positive/sufficient: {expectancy:.4f} <= {self.min_expectancy}")

        # Walk-forward validation decay
        wf_decay = walk_forward_results.get("overall_validation_decay", 1.0)
        if wf_decay > self.max_validation_decay_pct:
            rejection_reasons.append(f"Excessive validation decay: {wf_decay*100:.1f}% > {self.max_validation_decay_pct*100:.1f}%")

        # Monte Carlo tail risk
        ruin_prob = monte_carlo_results.get("ruin_probability", 1.0)
        if ruin_prob > 0.02:
            rejection_reasons.append(f"Unacceptable tail ruin probability: {ruin_prob*100:.1f}% > 2%")

        if rejection_reasons:
            reason_str = "; ".join(rejection_reasons)
            return False, reason_str, {"decision": "REJECT", "reasons": rejection_reasons}

        return True, "All validation thresholds satisfied. Promoted to PAPER trading.", {
            "decision": "PAPER",
            "metrics_summary": {
                "sharpe": sharpe,
                "profit_factor": pf,
                "drawdown": max_dd,
                "decay": wf_decay,
                "ruin_prob": ruin_prob,
            }
        }

    def evaluate_live_degradation(
        self,
        rolling_sharpe: float,
        rolling_drawdown: float,
        rolling_expectancy: float,
    ) -> Tuple[float, str]:
        """
        Calculates capital allocation scaling tier based on live rolling health.
        Returns (confidence_multiplier, status_recommendation).
        """
        if rolling_drawdown >= 0.12 or rolling_expectancy < -0.01:
            return 0.0, StrategyStatus.SUSPENDED.value
        elif rolling_drawdown >= 0.08 or rolling_sharpe < 0.2:
            return 0.25, StrategyStatus.DEGRADED.value
        elif rolling_drawdown >= 0.05 or rolling_sharpe < 0.5:
            return 0.50, StrategyStatus.DEGRADED.value
        elif rolling_sharpe < 0.8:
            return 0.75, StrategyStatus.LIVE.value

        return 1.0, StrategyStatus.LIVE.value
