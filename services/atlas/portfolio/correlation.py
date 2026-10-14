from typing import Dict, List, Set
import numpy as np
import pandas as pd


class CorrelationFilter:
    """
    Computes correlation between active positions and proposed candidates.
    Enforces maximum correlated positions limit (Section 11, MAX_CORRELATED_POSITIONS=3).
    """

    def __init__(self, correlation_threshold: float = 0.70, max_correlated_positions: int = 3):
        self.correlation_threshold = correlation_threshold
        self.max_correlated_positions = max_correlated_positions

    def calculate_correlation_matrix(self, price_history: Dict[str, pd.Series]) -> pd.DataFrame:
        """Computes pairwise Pearson correlation of daily returns."""
        returns_dict = {}
        for sym, series in price_history.items():
            if len(series) > 10:
                returns_dict[sym] = series.pct_change().dropna()

        if not returns_dict:
            return pd.DataFrame()

        df = pd.DataFrame(returns_dict)
        return df.corr()

    def is_correlation_permitted(
        self,
        candidate_symbol: str,
        active_symbols: List[str],
        corr_matrix: pd.DataFrame,
    ) -> bool:
        """
        Returns False if adding candidate_symbol would exceed max_correlated_positions
        correlated above the threshold.
        """
        if not active_symbols or corr_matrix.empty or candidate_symbol not in corr_matrix.columns:
            return True

        correlated_count = 0
        for active in active_symbols:
            if active in corr_matrix.columns:
                corr = abs(float(corr_matrix.loc[candidate_symbol, active]))
                if corr >= self.correlation_threshold:
                    correlated_count += 1

        return correlated_count < self.max_correlated_positions
