from typing import Any, Dict, List
import numpy as np


class MonteCarloAnalyzer:
    """
    Monte Carlo Trade Order Resampling Analysis.
    Evaluates tail risk, drawdown distribution, and probability of ruin.
    """

    def __init__(
        self,
        num_simulations: int = 1000,
        ruin_drawdown_threshold: float = 0.20, # 20% drawdown is ruin threshold
        random_seed: int = 42,
    ):
        self.num_simulations = num_simulations
        self.ruin_drawdown_threshold = ruin_drawdown_threshold
        self.random_seed = random_seed

    def analyze_trades(
        self,
        trades: List[Dict[str, Any]],
        initial_capital: float = 100000.0,
    ) -> Dict[str, Any]:
        if not trades or len(trades) < 5:
            return {
                "simulations": self.num_simulations,
                "p5_drawdown": 0.0,
                "p50_drawdown": 0.0,
                "p95_drawdown": 0.0,
                "ruin_probability": 0.0,
                "return_dispersion": {"p5": 0.0, "p50": 0.0, "p95": 0.0},
                "is_acceptable_tail_risk": True,
            }

        pnls = np.array([float(t.get("net_pnl", 0.0)) for t in trades])
        n_trades = len(pnls)

        rng = np.random.default_rng(self.random_seed)

        max_drawdowns = np.zeros(self.num_simulations)
        final_equities = np.zeros(self.num_simulations)
        ruin_count = 0

        for sim_idx in range(self.num_simulations):
            # Resample trade returns with replacement
            sim_pnls = rng.choice(pnls, size=n_trades, replace=True)
            equity_path = np.zeros(n_trades + 1)
            equity_path[0] = initial_capital

            ruined = False
            for step in range(n_trades):
                equity_path[step + 1] = equity_path[step] + sim_pnls[step]
                if equity_path[step + 1] <= 0:
                    equity_path[step + 1:] = 0
                    ruined = True
                    break

            peaks = np.maximum.accumulate(equity_path)
            dds = (peaks - equity_path) / peaks
            sim_max_dd = float(np.max(dds))
            max_drawdowns[sim_idx] = sim_max_dd
            final_equities[sim_idx] = equity_path[-1]

            if ruined or sim_max_dd >= self.ruin_drawdown_threshold:
                ruin_count += 1

        p5_dd = float(np.percentile(max_drawdowns, 5))
        p50_dd = float(np.percentile(max_drawdowns, 50))
        p95_dd = float(np.percentile(max_drawdowns, 95))

        p5_eq = float(np.percentile(final_equities, 5))
        p50_eq = float(np.percentile(final_equities, 50))
        p95_eq = float(np.percentile(final_equities, 95))

        ruin_prob = float(ruin_count / self.num_simulations)

        # Acceptable if probability of ruin is <= 1.0% and P95 drawdown <= 25%
        is_acceptable = (ruin_prob <= 0.01) and (p95_dd <= 0.25)

        return {
            "simulations": self.num_simulations,
            "p5_drawdown": round(p5_dd, 4),
            "p50_drawdown": round(p50_dd, 4),
            "p95_drawdown": round(p95_dd, 4),
            "ruin_probability": round(ruin_prob, 4),
            "return_dispersion": {
                "p5_equity": round(p5_eq, 2),
                "p50_equity": round(p50_eq, 2),
                "p95_equity": round(p95_eq, 2),
            },
            "is_acceptable_tail_risk": is_acceptable,
        }
