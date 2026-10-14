from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
import pandas as pd
from services.atlas.core.constants import MarketRegime, OrderSide


class StrategySignal(BaseModel):
    symbol: str
    direction: OrderSide = OrderSide.BUY
    strength: float = Field(..., ge=0.0, le=1.0)
    strategy_key: str
    version: str = "1.0.0"
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    price: float
    market_regime: str = MarketRegime.UNKNOWN.value
    metadata: Dict[str, Any] = Field(default_factory=dict)


class Strategy(ABC):

    def __init__(self, strategy_key: str, parameters: Optional[Dict[str, Any]] = None):
        self.strategy_key = strategy_key
        self._parameters = parameters or {}

    @abstractmethod
    def generate_signals(
        self,
        market_data: Dict[str, pd.DataFrame],
        current_regime: MarketRegime = MarketRegime.UNKNOWN,
    ) -> List[StrategySignal]:
        """
        Generate deterministic trading signals across universe.
        Long-only for cash equities V1.
        """
        pass

    @abstractmethod
    def required_history(self) -> int:
        """Minimum number of historical bars required for indicator warmup."""
        pass

    def parameters(self) -> Dict[str, Any]:
        return self._parameters.copy()

    def update_parameters(self, new_params: Dict[str, Any]):
        self._parameters.update(new_params)
