from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Optional
import pandas as pd


class MarketDataProvider(ABC):

    @abstractmethod
    async def get_historical_bars(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        timeframe: str = "1d",
    ) -> pd.DataFrame:
        """Fetch historical OHLCV data as validated dataframe."""
        pass

    @abstractmethod
    async def get_latest_quote(self, symbol: str) -> dict:
        """Fetch current market tick/quote."""
        pass
