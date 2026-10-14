import logging
from typing import Dict, List, Optional, Type
from services.atlas.core.config import config
from services.atlas.strategies.base import Strategy, StrategySignal
from services.atlas.strategies.trend.trend_following import TrendFollowingStrategy
from services.atlas.strategies.momentum.cross_sectional import CrossSectionalMomentumStrategy
from services.atlas.strategies.mean_reversion.rsi_bollinger import MeanReversionStrategy
from services.atlas.strategies.factor.breakout import BreakoutStrategy
from services.atlas.core.constants import MarketRegime

logger = logging.getLogger("atlas.strategies.registry")


STRATEGY_CLASS_MAP: Dict[str, Type[Strategy]] = {
    "trend": TrendFollowingStrategy,
    "trend_following": TrendFollowingStrategy,
    "momentum": CrossSectionalMomentumStrategy,
    "mean_reversion": MeanReversionStrategy,
    "breakout": BreakoutStrategy,
}


class StrategyRegistry:
    """
    Central registry for instantiated and approved trading strategies.
    """

    def __init__(self):
        self._strategies: Dict[str, Strategy] = {}
        self._strategy_metadata: Dict[str, dict] = {}
        self._load_configured_strategies()

    def _load_configured_strategies(self):
        conf_list = config.strategies_yaml.get("strategies", [])
        for entry in conf_list:
            strat_id = entry.get("id")
            family = entry.get("family", "")
            strat_class = STRATEGY_CLASS_MAP.get(family)
            if strat_class:
                instance = strat_class(strat_id, entry.get("parameters", {}))
                self._strategies[strat_id] = instance
                self._strategy_metadata[strat_id] = entry
                logger.info(f"Registered strategy: {strat_id} ({family})")
            else:
                logger.warning(f"Unknown strategy family '{family}' for {strat_id}")

    def get_strategy(self, strategy_id: str) -> Optional[Strategy]:
        return self._strategies.get(strategy_id)

    def list_strategies(self) -> List[dict]:
        res = []
        for strat_id, strat in self._strategies.items():
            meta = self._strategy_metadata.get(strat_id, {})
            res.append({
                "id": strat_id,
                "name": meta.get("name", strat_id),
                "family": meta.get("family", "custom"),
                "version": meta.get("version", "1.0.0"),
                "status": meta.get("status", "APPROVED"),
                "allocation_pct": meta.get("allocation_pct", 0.25),
                "compatible_regimes": meta.get("compatible_regimes", []),
                "parameters": strat.parameters(),
            })
        return res

    def register_custom_strategy(self, strategy_id: str, strategy: Strategy, meta: dict):
        self._strategies[strategy_id] = strategy
        self._strategy_metadata[strategy_id] = meta

    def generate_all_signals(
        self,
        market_data: dict,
        current_regime: MarketRegime,
    ) -> List[StrategySignal]:
        all_signals: List[StrategySignal] = []
        for strat_id, strategy in self._strategies.items():
            meta = self._strategy_metadata.get(strat_id, {})
            status = meta.get("status", "APPROVED")
            # Only approved, canary, or paper strategies generate tradeable signals
            if status in ("RETIRED", "SUSPENDED"):
                continue

            try:
                sigs = strategy.generate_signals(market_data, current_regime)
                all_signals.extend(sigs)
            except Exception as e:
                logger.error(f"Error generating signals for {strat_id}: {e}")
        return all_signals


# Global singleton instance
strategy_registry = StrategyRegistry()
