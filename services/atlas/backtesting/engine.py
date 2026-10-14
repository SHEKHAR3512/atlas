import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
import numpy as np
import pandas as pd
from services.atlas.backtesting.fees import NSETransactionCostModel
from services.atlas.backtesting.slippage import SlippageModel
from services.atlas.backtesting.metrics import BacktestMetricsCalculator
from services.atlas.strategies.base import Strategy
from services.atlas.core.constants import MarketRegime, OrderSide

logger = logging.getLogger("atlas.backtesting.engine")


class BacktestEngine:
    """
    Event-driven / bar-by-bar backtesting simulation engine.
    Invariants:
      - Execution delay: orders fill on NEXT bar open
      - Realistic transaction costs and taxes (NSE cash schedule)
      - Realistic slippage
      - Long-only cash equity
      - No cash overdrafts (cash >= 0)
    """

    def __init__(
        self,
        initial_capital: float = 100000.0,
        cost_model: Optional[NSETransactionCostModel] = None,
        slippage_model: Optional[SlippageModel] = None,
        max_position_pct: float = 0.03,
    ):
        self.initial_capital = initial_capital
        self.cost_model = cost_model or NSETransactionCostModel()
        self.slippage_model = slippage_model or SlippageModel(default_bps=10.0)
        self.max_position_pct = max_position_pct

    def run(
        self,
        strategy: Strategy,
        market_data: Dict[str, pd.DataFrame],
        regime: MarketRegime = MarketRegime.BULL_TREND,
    ) -> Dict[str, Any]:
        """
        Executes backtest across the provided universe of historical data.
        Returns metrics, trades, and equity curve.
        """
        # Determine shared chronological timeline
        all_timestamps = set()
        for sym, df in market_data.items():
            all_timestamps.update(df["timestamp"].tolist())
        timeline = sorted(list(all_timestamps))

        if len(timeline) < strategy.required_history():
            return {
                "metrics": BacktestMetricsCalculator.calculate_metrics(pd.Series([]), []),
                "trades": [],
                "equity_curve": [],
            }

        cash = self.initial_capital
        positions: Dict[str, Dict[str, Any]] = {} # symbol -> {quantity, entry_price, entry_time}
        completed_trades: List[Dict[str, Any]] = []
        equity_records: List[Dict[str, Any]] = []
        pending_orders: List[Dict[str, Any]] = []

        # Step forward bar-by-bar
        for idx in range(strategy.required_history(), len(timeline)):
            current_dt = timeline[idx]

            # 1. Execute any pending orders from the PREVIOUS bar at CURRENT bar open (Execution Delay)
            for order in pending_orders:
                sym = order["symbol"]
                df = market_data.get(sym)
                bar_row = df[df["timestamp"] == current_dt]
                if bar_row.empty:
                    continue

                open_price = float(bar_row["open"].iloc[0])
                daily_vol = float(bar_row["volume"].iloc[0])
                side = order["side"]

                if side == OrderSide.BUY and sym not in positions:
                    exec_price = self.slippage_model.calculate_slippage("BUY", open_price, order["quantity"], daily_vol)
                    fees = self.cost_model.calculate_cost("BUY", exec_price, order["quantity"])["total_fees"]
                    cost = (exec_price * order["quantity"]) + fees

                    if cost <= cash:
                        cash -= cost
                        positions[sym] = {
                            "quantity": order["quantity"],
                            "entry_price": exec_price,
                            "entry_time": current_dt,
                            "stop_loss": order.get("stop_loss"),
                            "take_profit": order.get("take_profit"),
                        }

                elif side == OrderSide.SELL and sym in positions:
                    pos = positions.pop(sym)
                    qty = pos["quantity"]
                    exec_price = self.slippage_model.calculate_slippage("SELL", open_price, qty, daily_vol)
                    fees = self.cost_model.calculate_cost("SELL", exec_price, qty)["total_fees"]

                    gross_pnl = (exec_price - pos["entry_price"]) * qty
                    net_pnl = gross_pnl - fees
                    cash += (exec_price * qty) - fees

                    ret_pct = (exec_price - pos["entry_price"]) / pos["entry_price"]
                    completed_trades.append({
                        "symbol": sym,
                        "direction": "LONG",
                        "entry_time": pos["entry_time"].isoformat() if hasattr(pos["entry_time"], "isoformat") else str(pos["entry_time"]),
                        "entry_price": round(pos["entry_price"], 2),
                        "exit_time": current_dt.isoformat() if hasattr(current_dt, "isoformat") else str(current_dt),
                        "exit_price": round(exec_price, 2),
                        "quantity": qty,
                        "gross_pnl": round(gross_pnl, 2),
                        "net_pnl": round(net_pnl, 2),
                        "fees": round(fees, 2),
                        "return_pct": round(ret_pct, 4),
                        "exit_reason": order.get("reason", "SIGNAL"),
                    })

            pending_orders = []

            # 2. Slice market data up to current_dt for strategy signal generation (Prevent future lookahead)
            sliced_data = {}
            current_portfolio_value = cash
            for sym, df in market_data.items():
                sub_df = df[df["timestamp"] <= current_dt]
                if not sub_df.empty:
                    sliced_data[sym] = sub_df
                    if sym in positions:
                        cur_close = float(sub_df["close"].iloc[-1])
                        current_portfolio_value += cur_close * positions[sym]["quantity"]

            # Check stop loss / take profit triggers on existing positions
            for sym, pos in list(positions.items()):
                sub_df = sliced_data.get(sym)
                if sub_df is None or sub_df.empty:
                    continue
                cur_close = float(sub_df["close"].iloc[-1])
                stop_l = pos.get("stop_loss")
                take_p = pos.get("take_profit")

                if stop_l and cur_close <= stop_l:
                    pending_orders.append({"symbol": sym, "side": OrderSide.SELL, "reason": "STOP_LOSS"})
                elif take_p and cur_close >= take_p:
                    pending_orders.append({"symbol": sym, "side": OrderSide.SELL, "reason": "TAKE_PROFIT"})

            # Generate new signals
            signals = strategy.generate_signals(sliced_data, current_regime=regime)
            for sig in signals:
                if sig.symbol not in positions and sig.direction == OrderSide.BUY:
                    # Allocate based on max_position_pct
                    target_alloc = current_portfolio_value * self.max_position_pct
                    qty = int(target_alloc / sig.price)
                    if qty > 0 and (qty * sig.price) <= cash:
                        pending_orders.append({
                            "symbol": sig.symbol,
                            "side": OrderSide.BUY,
                            "quantity": qty,
                            "stop_loss": sig.metadata.get("stop_loss"),
                            "take_profit": sig.metadata.get("take_profit"),
                        })

            equity_records.append({
                "timestamp": current_dt.isoformat() if hasattr(current_dt, "isoformat") else str(current_dt),
                "equity": round(current_portfolio_value, 2),
                "cash": round(cash, 2),
                "positions_count": len(positions),
            })

        # Calculate final metrics
        eq_series = pd.Series([r["equity"] for r in equity_records])
        metrics = BacktestMetricsCalculator.calculate_metrics(
            equity_series=eq_series,
            trades=completed_trades,
            initial_capital=self.initial_capital,
        )

        return {
            "metrics": metrics,
            "trades": completed_trades,
            "equity_curve": equity_records,
        }
