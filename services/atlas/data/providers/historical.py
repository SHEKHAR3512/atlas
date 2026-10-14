from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional
import numpy as np
import pandas as pd
from services.atlas.data.providers.base import MarketDataProvider
from services.atlas.data.quality.validator import MarketDataValidator

# Baseline typical prices for liquid NSE stocks
STOCK_BASES = {
    "RELIANCE": {"price": 2850.0, "vol": 0.016, "drift": 0.0004},
    "TCS": {"price": 3950.0, "vol": 0.014, "drift": 0.0003},
    "HDFCBANK": {"price": 1620.0, "vol": 0.015, "drift": 0.0002},
    "INFY": {"price": 1780.0, "vol": 0.018, "drift": 0.0004},
    "ICICIBANK": {"price": 1180.0, "vol": 0.017, "drift": 0.0005},
    "SBIN": {"price": 790.0, "vol": 0.020, "drift": 0.0003},
    "BHARTIARTL": {"price": 1420.0, "vol": 0.015, "drift": 0.0006},
    "ITC": {"price": 490.0, "vol": 0.012, "drift": 0.0003},
    "LT": {"price": 3600.0, "vol": 0.016, "drift": 0.0004},
    "AXISBANK": {"price": 1190.0, "vol": 0.018, "drift": 0.0003},
    "KOTAKBANK": {"price": 1780.0, "vol": 0.015, "drift": 0.0002},
    "HINDUNILVR": {"price": 2720.0, "vol": 0.013, "drift": 0.0002},
}


class SyntheticNSEHistoricalProvider(MarketDataProvider):
    """
    High-fidelity deterministic NSE equities historical data generator.
    Uses seeded pseudo-random walks ensuring exact reproducibility across runs.
    """

    def __init__(self, seed: int = 42):
        self.seed = seed

    async def get_historical_bars(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        timeframe: str = "1d",
    ) -> pd.DataFrame:
        spec = STOCK_BASES.get(symbol, {"price": 1000.0, "vol": 0.018, "drift": 0.0003})
        base_price = spec["price"]
        daily_vol = spec["vol"]
        daily_drift = spec["drift"]

        # Deterministic seed based on symbol name to make experiments 100% reproducible
        sym_hash = sum(ord(c) for c in symbol)
        rng = np.random.default_rng(self.seed + sym_hash)

        # Generate trading calendar (excluding weekends)
        current = start_date.replace(hour=9, minute=15, second=0, microsecond=0)
        dates = []
        while current <= end_date:
            if current.weekday() < 5:  # Monday to Friday
                dates.append(current)
            current += timedelta(days=1)

        n = len(dates)
        if n == 0:
            return pd.DataFrame(columns=["timestamp", "open", "high", "low", "close", "volume"])

        # Geometric Brownian Motion with regime shifts
        shocks = rng.normal(daily_drift, daily_vol, n)
        # Add moderate cyclical momentum
        t = np.linspace(0, 4 * np.pi, n)
        trend_cycle = 0.0005 * np.sin(t)
        combined_returns = shocks + trend_cycle

        price_series = np.zeros(n)
        price_series[0] = base_price
        for i in range(1, n):
            price_series[i] = price_series[i - 1] * np.exp(combined_returns[i])

        records = []
        for i, dt in enumerate(dates):
            close = round(float(price_series[i]), 2)
            day_noise = rng.uniform(0.003, 0.015)
            open_p = round(float(price_series[i - 1] if i > 0 else close * (1 - day_noise / 2)), 2)
            high_p = round(max(open_p, close) * (1.0 + rng.uniform(0.001, day_noise)), 2)
            low_p = round(min(open_p, close) * (1.0 - rng.uniform(0.001, day_noise)), 2)
            volume = float(rng.integers(200_000, 2_500_000))

            records.append({
                "timestamp": dt,
                "open": open_p,
                "high": high_p,
                "low": low_p,
                "close": close,
                "volume": volume,
            })

        df = pd.DataFrame(records)
        return MarketDataValidator.validate_dataframe(df, symbol)

    async def get_latest_quote(self, symbol: str) -> dict:
        spec = STOCK_BASES.get(symbol, {"price": 1000.0})
        price = spec["price"]
        return {
            "symbol": symbol,
            "last_price": price,
            "bid": round(price * 0.9998, 2),
            "ask": round(price * 1.0002, 2),
            "volume": 500000.0,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
