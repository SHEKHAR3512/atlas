import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple
import pandas as pd

logger = logging.getLogger("atlas.data.quality")


class MarketDataQualityError(Exception):
    pass


class MarketDataValidator:
    """
    Strict validation of market bars and ticks according to ATLAS safety principles.
    Invariants:
      - low <= open <= high
      - low <= close <= high
      - volume >= 0
      - timestamp is not in the future
      - no NaN / null in required price fields
    """

    @staticmethod
    def validate_bar(
        symbol: str,
        timestamp: datetime,
        open_price: float,
        high_price: float,
        low_price: float,
        close_price: float,
        volume: float,
    ) -> Tuple[bool, Optional[str]]:
        now = datetime.now(timezone.utc)
        if timestamp > now:
            return False, f"Bar timestamp {timestamp} is in future relative to {now}"

        if any(v is None or pd.isna(v) for v in (open_price, high_price, low_price, close_price)):
            return False, "Null or NaN found in OHLC values"

        if open_price <= 0 or high_price <= 0 or low_price <= 0 or close_price <= 0:
            return False, "Non-positive price in OHLC bar"

        if volume < 0 or pd.isna(volume):
            return False, f"Invalid volume: {volume}"

        if not (low_price <= open_price <= high_price):
            return False, f"OHLC violation: open {open_price} not between low {low_price} and high {high_price}"

        if not (low_price <= close_price <= high_price):
            return False, f"OHLC violation: close {close_price} not between low {low_price} and high {high_price}"

        return True, None

    @classmethod
    def validate_dataframe(cls, df: pd.DataFrame, symbol: str) -> pd.DataFrame:
        """
        Validates and cleans OHLCV dataframe.
        Raises MarketDataQualityError if data is corrupt.
        """
        required_cols = ["timestamp", "open", "high", "low", "close", "volume"]
        missing = [c for c in required_cols if c not in df.columns]
        if missing:
            raise MarketDataQualityError(f"Missing required columns: {missing} for {symbol}")

        if df.empty:
            raise MarketDataQualityError(f"Empty dataframe provided for {symbol}")

        # Ensure correct datatypes
        clean_df = df.copy()
        clean_df["timestamp"] = pd.to_datetime(clean_df["timestamp"], utc=True)
        clean_df = clean_df.sort_values("timestamp").drop_duplicates(subset=["timestamp"])

        for col in ["open", "high", "low", "close", "volume"]:
            clean_df[col] = pd.to_numeric(clean_df[col], errors="coerce")

        # Invariant filters
        valid_mask = (
            (clean_df["low"] <= clean_df["open"]) &
            (clean_df["open"] <= clean_df["high"]) &
            (clean_df["low"] <= clean_df["close"]) &
            (clean_df["close"] <= clean_df["high"]) &
            (clean_df["low"] > 0) &
            (clean_df["volume"] >= 0)
        )

        invalid_count = (~valid_mask).sum()
        if invalid_count > 0:
            logger.warning(f"Discarding {invalid_count} corrupt bars for {symbol}")
            clean_df = clean_df[valid_mask]

        if clean_df.empty:
            raise MarketDataQualityError(f"No valid data remaining for {symbol} after validation")

        return clean_df.reset_index(drop=True)
