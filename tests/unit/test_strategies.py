import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, timezone
from services.atlas.strategies.trend.trend_following import TrendFollowingStrategy
from services.atlas.strategies.momentum.cross_sectional import CrossSectionalMomentumStrategy
from services.atlas.strategies.mean_reversion.rsi_bollinger import MeanReversionStrategy
from services.atlas.strategies.factor.breakout import BreakoutStrategy
from services.atlas.core.constants import MarketRegime


def create_sample_bars(n: int = 250, trend: float = 0.001) -> pd.DataFrame:
    now = datetime.now(timezone.utc)
    dates = [now - timedelta(days=n - i) for i in range(n)]
    prices = [1000.0]
    for _ in range(n - 1):
        prices.append(prices[-1] * (1.0 + trend + np.random.normal(0, 0.01)))

    records = []
    for i, dt in enumerate(dates):
        p = prices[i]
        records.append({
            "timestamp": dt,
            "open": p * 0.998,
            "high": p * 1.01,
            "low": p * 0.99,
            "close": p,
            "volume": 500000.0,
        })
    return pd.DataFrame(records)


def test_trend_following_signals():
    strat = TrendFollowingStrategy()
    df = create_sample_bars(250, trend=0.002) # upward trending
    sigs = strat.generate_signals({"RELIANCE": df}, MarketRegime.BULL_TREND)
    assert isinstance(sigs, list)


def test_momentum_strategy():
    strat = CrossSectionalMomentumStrategy()
    df1 = create_sample_bars(150, trend=0.003) # high return
    df2 = create_sample_bars(150, trend=0.0001) # low return
    sigs = strat.generate_signals({"HIGH_MOM": df1, "LOW_MOM": df2}, MarketRegime.BULL_TREND)
    assert isinstance(sigs, list)


def test_mean_reversion_strategy():
    strat = MeanReversionStrategy()
    df = create_sample_bars(100, trend=0.0)
    # Mean reversion in sideways regime
    sigs = strat.generate_signals({"SIDEWAYS": df}, MarketRegime.SIDEWAYS)
    assert isinstance(sigs, list)


def test_breakout_strategy():
    strat = BreakoutStrategy()
    df = create_sample_bars(100, trend=0.001)
    sigs = strat.generate_signals({"BREAKOUT": df}, MarketRegime.BULL_TREND)
    assert isinstance(sigs, list)
