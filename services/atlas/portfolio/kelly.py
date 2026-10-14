import logging
from typing import List, Dict, Optional, Tuple

logger = logging.getLogger("atlas.portfolio.kelly")


def fractional_kelly(
    win_probability: float,
    average_win: float,
    average_loss: float,
    fraction: float = 0.25,
    maximum: float = 0.03,
) -> float:
    """
    Exact mathematical fractional Kelly Criterion implementation.
    Capital preservation priority over raw edge.
    f* = ((b * p) - q) / b
    where:
      p = estimated probability of winning
      q = 1 - p
      b = average win / abs(average loss)
    """
    if average_loss >= 0:
        return 0.0

    if average_win <= 0:
        return 0.0

    b = average_win / abs(average_loss)

    if b <= 0:
        return 0.0

    p = win_probability
    q = 1.0 - p

    raw_kelly = ((b * p) - q) / b

    if raw_kelly <= 0:
        return 0.0

    fractional = raw_kelly * fraction

    return min(fractional, maximum)


class KellyPositionSizer:
    """
    Computes Kelly position allocations based on verified historical trade sample.
    Enforces minimum sample sizes to prevent over-allocation on noisy data.
    """

    def __init__(
        self,
        fraction: float = 0.25,
        maximum: float = 0.03,
        min_trades: int = 100,
        bootstrap_allocation: float = 0.005 # 0.5% conservative seed if < min_trades
    ):
        self.fraction = fraction
        self.maximum = maximum
        self.min_trades = min_trades
        self.bootstrap_allocation = bootstrap_allocation

    def compute_allocation_pct(
        self,
        historical_trades: List[Dict[str, any]],
    ) -> Tuple[float, Dict[str, float]]:
        trade_count = len(historical_trades)
        if trade_count == 0:
            return 0.0, {
                "sample_size": 0,
                "win_probability": 0.0,
                "average_win": 0.0,
                "average_loss": 0.0,
                "raw_kelly": 0.0,
                "fractional_kelly": 0.0,
                "is_bootstrapped": False,
            }

        returns = [float(t.get("return_pct", 0.0)) for t in historical_trades]
        wins = [r for r in returns if r > 0]
        losses = [r for r in returns if r <= 0]

        win_prob = len(wins) / trade_count
        avg_win = float(sum(wins) / len(wins)) if wins else 0.0
        avg_loss = float(sum(losses) / len(losses)) if losses else 0.0

        if trade_count < self.min_trades:
            # Insufficient sample size check: fallback to conservative bootstrap or zero
            raw_k = 0.0
            if avg_loss < 0 and avg_win > 0:
                b = avg_win / abs(avg_loss)
                raw_k = max(0.0, ((b * win_prob) - (1.0 - win_prob)) / b)

            alloc = self.bootstrap_allocation if raw_k > 0 else 0.0
            return alloc, {
                "sample_size": trade_count,
                "win_probability": round(win_prob, 4),
                "average_win": round(avg_win, 4),
                "average_loss": round(avg_loss, 4),
                "raw_kelly": round(raw_k, 4),
                "fractional_kelly": round(alloc, 4),
                "is_bootstrapped": True,
            }

        # Valid sample size >= min_trades
        b = avg_win / abs(avg_loss) if (avg_loss < 0 and avg_win > 0) else 0.0
        raw_k = max(0.0, ((b * win_prob) - (1.0 - win_prob)) / b) if b > 0 else 0.0

        final_kelly = fractional_kelly(
            win_probability=win_prob,
            average_win=avg_win,
            average_loss=avg_loss,
            fraction=self.fraction,
            maximum=self.maximum,
        )

        return final_kelly, {
            "sample_size": trade_count,
            "win_probability": round(win_prob, 4),
            "average_win": round(avg_win, 4),
            "average_loss": round(avg_loss, 4),
            "raw_kelly": round(raw_k, 4),
            "fractional_kelly": round(final_kelly, 4),
            "is_bootstrapped": False,
        }
