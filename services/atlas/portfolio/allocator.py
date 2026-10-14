import logging
from typing import Any, Dict, List, Optional
import pandas as pd
from services.atlas.core.config import config
from services.atlas.core.constants import MarketRegime
from services.atlas.strategies.base import StrategySignal
from services.atlas.portfolio.kelly import KellyPositionSizer
from services.atlas.portfolio.correlation import CorrelationFilter

logger = logging.getLogger("atlas.portfolio.allocator")


class PortfolioAllocator:
    """
    Capital Allocator and Multi-Layer Position Sizing Engine.
    Flow:
      Raw strategy signal
             ↓
      Regime & Strategy Confidence Multiplier
             ↓
      Fractional Kelly Sizing
             ↓
      Volatility Adjustment
             ↓
      Correlation Check
             ↓
      Per-position Hard Limit
             ↓
      Final Proposed Quantity
    """

    def __init__(
        self,
        kelly_sizer: Optional[KellyPositionSizer] = None,
        correlation_filter: Optional[CorrelationFilter] = None,
    ):
        self.kelly_sizer = kelly_sizer or KellyPositionSizer(
            fraction=config.settings.KELLY_FRACTION,
            maximum=config.settings.MAX_POSITION_PCT,
            min_trades=config.settings.MIN_BACKTEST_TRADES,
        )
        self.correlation_filter = correlation_filter or CorrelationFilter(
            correlation_threshold=0.70,
            max_correlated_positions=config.settings.MAX_CORRELATED_POSITIONS,
        )

    def allocate_signal(
        self,
        signal: StrategySignal,
        portfolio_equity: float,
        available_cash: float,
        active_positions: List[Dict[str, Any]],
        historical_trades: List[Dict[str, Any]],
        current_regime: MarketRegime,
        strategy_meta: Dict[str, Any],
        corr_matrix: Optional[pd.DataFrame] = None,
    ) -> Dict[str, Any]:
        """
        Calculates mathematically justified position size and returns TradeProposal dict.
        """
        symbol = signal.symbol
        price = signal.price
        if price <= 0 or portfolio_equity <= 0:
            return {"proposed_quantity": 0, "reason": "Invalid price or equity"}

        # 1. Regime compatibility check
        compat_regimes = strategy_meta.get("compatible_regimes", [])
        if compat_regimes and current_regime.value not in compat_regimes and current_regime != MarketRegime.UNKNOWN:
            return {
                "proposed_quantity": 0,
                "reason": f"Regime {current_regime.value} not compatible with strategy {signal.strategy_key}",
            }

        # 2. Strategy Confidence Multiplier (degradation tier: 1.0, 0.75, 0.5, 0.25, 0.0)
        confidence_mult = float(strategy_meta.get("confidence_multiplier", 1.0))
        if confidence_mult <= 0:
            return {"proposed_quantity": 0, "reason": "Strategy degraded/suspended (0% allocation)"}

        # 3. Fractional Kelly Calculation
        kelly_pct, kelly_meta = self.kelly_sizer.compute_allocation_pct(historical_trades)
        if kelly_pct <= 0:
            return {
                "proposed_quantity": 0,
                "reason": "Kelly criterion calculated zero or negative edge",
                "kelly_meta": kelly_meta,
            }

        # 4. Volatility Adjustment
        # If signal metadata includes ATR / price ratio, adjust sizing inversely to volatility
        atr = signal.metadata.get("atr")
        vol_adj = 1.0
        if atr and price > 0:
            atr_pct = atr / price
            # Baseline benchmark daily volatility ~ 1.2%
            if atr_pct > 0.012:
                vol_adj = max(0.5, min(1.0, 0.012 / atr_pct))

        # 5. Correlation Check
        active_symbols = [p["symbol"] for p in active_positions if p.get("is_open", True)]
        if corr_matrix is not None and not self.correlation_filter.is_correlation_permitted(
            symbol, active_symbols, corr_matrix
        ):
            return {
                "proposed_quantity": 0,
                "reason": f"Correlation limit exceeded (max {self.correlation_filter.max_correlated_positions} correlated positions)",
            }

        # 6. Sizing combination
        effective_pct = kelly_pct * confidence_mult * vol_adj * signal.strength
        # Hard cap at max_position_pct
        effective_pct = min(effective_pct, config.settings.MAX_POSITION_PCT)

        target_notional = portfolio_equity * effective_pct
        # Cash boundary check
        affordable_notional = min(target_notional, available_cash * 0.98) # retain 2% cash buffer
        quantity = int(affordable_notional / price)

        return {
            "proposed_quantity": quantity,
            "proposed_price": price,
            "raw_kelly_pct": kelly_meta.get("raw_kelly", 0.0),
            "fractional_kelly_pct": kelly_pct,
            "win_probability": kelly_meta.get("win_probability", 0.0),
            "average_win": kelly_meta.get("average_win", 0.0),
            "average_loss": kelly_meta.get("average_loss", 0.0),
            "volatility_adjustment": vol_adj,
            "effective_allocation_pct": round(effective_pct, 4),
            "target_notional": round(target_notional, 2),
            "reason": "APPROVED_BY_ALLOCATOR" if quantity > 0 else "Insufficient cash or rounded to zero",
        }
