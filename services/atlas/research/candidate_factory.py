import random
import uuid
from typing import Any, Dict, List
from services.atlas.core.config import config


class CandidateFactory:
    """
    Generates structured experimental strategy candidates within constrained parameter spaces.
    Prevents unconstrained data mining (Section 31 & 77).
    """

    @staticmethod
    def generate_candidate(family: str = "trend") -> Dict[str, Any]:
        spaces = config.research_yaml.get("mutation_spaces", {})
        cand_id = f"cand_{family}_{uuid.uuid4().hex[:8]}"

        if family == "trend":
            space = spaces.get("trend", {})
            fast_ema = random.choice(space.get("fast_ema", [10, 20, 30]))
            slow_ema = random.choice(space.get("slow_ema", [50, 100]))
            atr_mult = random.choice(space.get("atr_multiplier", [1.5, 2.0, 2.5]))
            params = {
                "fast_ema": fast_ema,
                "slow_ema": slow_ema,
                "trend_ema": 200,
                "adx_threshold": 20.0,
                "atr_multiplier": atr_mult,
            }
            title = f"Trend Following (Fast {fast_ema} / Slow {slow_ema} / ATR {atr_mult})"
            hypothesis = f"Hypothesis: EMA cross ({fast_ema}/{slow_ema}) with ATR {atr_mult} stop captures medium-term trends efficiently."

        elif family == "momentum":
            space = spaces.get("momentum", {})
            lookback = random.choice(space.get("lookback_days", [30, 60, 90, 120]))
            top_n = random.choice(space.get("top_n", [2, 3, 5]))
            params = {
                "lookback_days": lookback,
                "top_n": top_n,
                "volatility_window": 20,
            }
            title = f"Risk-Adjusted Momentum ({lookback}d Lookback / Top {top_n})"
            hypothesis = f"Hypothesis: Selecting top {top_n} liquid stocks with highest return-to-volatility over {lookback} days yields positive persistence."

        elif family == "mean_reversion":
            space = spaces.get("mean_reversion", {})
            rsi_os = random.choice(space.get("rsi_oversold", [25.0, 30.0, 35.0]))
            bb_p = random.choice(space.get("bb_period", [15, 20, 25]))
            params = {
                "rsi_period": 14,
                "rsi_oversold": rsi_os,
                "bb_period": bb_p,
                "bb_std": 2.0,
                "z_threshold": -1.5,
            }
            title = f"Mean Reversion (RSI {rsi_os} / BB {bb_p})"
            hypothesis = f"Hypothesis: Oversold bounces when RSI <= {rsi_os} and close touches lower Bollinger ({bb_p}) generate reliable mean reversion in range-bound regimes."

        else: # breakout
            space = spaces.get("breakout", {})
            ch_p = random.choice(space.get("channel_period", [15, 20, 30]))
            vol_f = random.choice(space.get("volume_factor", [1.1, 1.25, 1.5]))
            params = {
                "channel_period": ch_p,
                "volume_factor": vol_f,
                "atr_stop_multiplier": 1.5,
            }
            title = f"Donchian Breakout ({ch_p}d Channel / {vol_f}x Volume)"
            hypothesis = f"Hypothesis: New {ch_p}-day highs supported by {vol_f}x volume surges have higher follow-through probability."

        return {
            "candidate_id": cand_id,
            "title": title,
            "family": family,
            "hypothesis": hypothesis,
            "parameters": params,
        }
