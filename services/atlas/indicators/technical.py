import numpy as np
import pandas as pd
from typing import Tuple


def calculate_ema(series: pd.Series, period: int) -> pd.Series:
    """Calculate Exponential Moving Average."""
    return series.ewm(span=period, adjust=False).mean()


def calculate_sma(series: pd.Series, period: int) -> pd.Series:
    """Calculate Simple Moving Average."""
    return series.rolling(window=period, min_periods=1).mean()


def calculate_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """
    Calculate Average True Range (ATR).
    TR = max(High - Low, |High - Close_prev|, |Low - Close_prev|)
    """
    high = df["high"]
    low = df["low"]
    close_prev = df["close"].shift(1)

    tr1 = high - low
    tr2 = (high - close_prev).abs()
    tr3 = (low - close_prev).abs()

    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    return tr.rolling(window=period, min_periods=1).mean()


def calculate_rsi(series: pd.Series, period: int = 14) -> pd.Series:
    """
    Calculate Relative Strength Index (RSI).
    Standard Wilder smoothing.
    """
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -1 * delta.clip(upper=0)

    avg_gain = gain.ewm(alpha=1.0 / period, min_periods=period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1.0 / period, min_periods=period, adjust=False).mean()

    rs = avg_gain / (avg_loss + 1e-10)
    rsi = 100.0 - (100.0 / (1.0 + rs))
    return rsi.fillna(50.0)


def calculate_bollinger_bands(
    series: pd.Series,
    period: int = 20,
    num_std: float = 2.0
) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """
    Calculate Bollinger Bands.
    Returns: (middle_band, upper_band, lower_band)
    """
    middle = series.rolling(window=period, min_periods=1).mean()
    std = series.rolling(window=period, min_periods=1).std(ddof=0).fillna(0.0)
    upper = middle + (num_std * std)
    lower = middle - (num_std * std)
    return middle, upper, lower


def calculate_donchian_channels(
    df: pd.DataFrame,
    period: int = 20
) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """
    Calculate Donchian Channels.
    Returns: (upper, lower, middle)
    """
    upper = df["high"].rolling(window=period, min_periods=1).max()
    lower = df["low"].rolling(window=period, min_periods=1).min()
    middle = (upper + lower) / 2.0
    return upper, lower, middle


def calculate_adx(df: pd.DataFrame, period: int = 14) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """
    Calculate Average Directional Index (ADX), +DI, -DI.
    """
    high = df["high"]
    low = df["low"]
    close = df["close"]

    # True Range
    tr = calculate_atr(df, period=1)

    # Directional Movement
    up_move = high.diff()
    down_move = -low.diff()

    plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0.0)
    minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0.0)

    tr_smoothed = pd.Series(tr).rolling(window=period, min_periods=1).sum()
    plus_di = 100.0 * (pd.Series(plus_dm).rolling(window=period, min_periods=1).sum() / (tr_smoothed + 1e-10))
    minus_di = 100.0 * (pd.Series(minus_dm).rolling(window=period, min_periods=1).sum() / (tr_smoothed + 1e-10))

    dx = 100.0 * ((plus_di - minus_di).abs() / (plus_di + minus_di + 1e-10))
    adx = dx.rolling(window=period, min_periods=1).mean().fillna(0.0)

    return adx, plus_di, minus_di


def calculate_zscore(series: pd.Series, period: int = 20) -> pd.Series:
    """Calculate rolling Z-score."""
    mean = series.rolling(window=period, min_periods=1).mean()
    std = series.rolling(window=period, min_periods=1).std().fillna(1.0)
    return (series - mean) / (std + 1e-10)


def calculate_realized_volatility(series: pd.Series, window: int = 20) -> pd.Series:
    """Calculate annualized rolling realized volatility of log returns."""
    log_returns = np.log(series / series.shift(1))
    rolling_std = log_returns.rolling(window=window, min_periods=1).std().fillna(0.0)
    return rolling_std * np.sqrt(252)
