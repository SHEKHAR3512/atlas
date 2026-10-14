import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from services.atlas.brokers.base import Broker
from services.atlas.backtesting.fees import NSETransactionCostModel
from services.atlas.backtesting.slippage import SlippageModel
from services.atlas.core.config import config

logger = logging.getLogger("atlas.brokers.paper")


class PaperBroker(Broker):
    """
    High-fidelity Paper Broker simulation.
    Features:
      - Realistic execution with NSE transaction charges and slippage
      - Complete order lifecycle (PENDING -> FILLED / REJECTED / CANCELLED)
      - Idempotent order tracking via client_order_id
      - Real-time balance and position book
    """

    def __init__(
        self,
        initial_cash: float = 100000.0,
        cost_model: Optional[NSETransactionCostModel] = None,
        slippage_model: Optional[SlippageModel] = None,
    ):
        self.initial_cash = initial_cash
        self.cash = initial_cash
        self.realized_pnl = 0.0
        self.cost_model = cost_model or NSETransactionCostModel()
        self.slippage_model = slippage_model or SlippageModel(default_bps=10.0)

        # symbol -> position dict
        self._positions: Dict[str, Dict[str, Any]] = {}
        # order_id -> order dict
        self._orders: Dict[str, Dict[str, Any]] = {}
        # client_order_id -> order_id
        self._client_order_map: Dict[str, str] = {}

    async def connect(self) -> bool:
        logger.info("PaperBroker connected. Capital: Rs %.2f", self.cash)
        return True

    async def account(self) -> Dict[str, Any]:
        unrealized = sum(p.get("unrealized_pnl", 0.0) for p in self._positions.values())
        invested = sum(p["quantity"] * p["current_price"] for p in self._positions.values())
        equity = self.cash + invested

        return {
            "trading_mode": "PAPER",
            "cash": round(self.cash, 2),
            "invested": round(invested, 2),
            "equity": round(equity, 2),
            "unrealized_pnl": round(unrealized, 2),
            "realized_pnl": round(self.realized_pnl, 2),
            "positions_count": len(self._positions),
            "currency": "INR",
        }

    async def positions(self) -> List[Dict[str, Any]]:
        return list(self._positions.values())

    async def orders(self) -> List[Dict[str, Any]]:
        return list(self._orders.values())

    async def place_order(self, order: Dict[str, Any]) -> Dict[str, Any]:
        client_oid = order.get("client_order_id", str(uuid.uuid4()))

        # Idempotency check: prevent duplicate order submissions
        if client_oid in self._client_order_map:
            existing_id = self._client_order_map[client_oid]
            logger.warning(f"Duplicate order with client_order_id {client_oid} detected. Returning existing order.")
            return self._orders[existing_id]

        order_id = f"paper_ord_{uuid.uuid4().hex[:12]}"
        symbol = order["symbol"]
        side = order["side"].upper()
        quantity = int(order["quantity"])
        price = float(order["price"])
        order_type = order.get("order_type", "LIMIT")

        if quantity <= 0 or price <= 0:
            failed_order = {
                "order_id": order_id,
                "client_order_id": client_oid,
                "symbol": symbol,
                "side": side,
                "quantity": quantity,
                "price": price,
                "status": "REJECTED",
                "rejection_reason": "Invalid quantity or price",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            self._orders[order_id] = failed_order
            self._client_order_map[client_oid] = order_id
            return failed_order

        # Execution simulation with slippage
        exec_price = self.slippage_model.calculate_slippage(side, price, quantity)
        cost_breakdown = self.cost_model.calculate_cost(side, exec_price, quantity)
        total_fees = cost_breakdown["total_fees"]

        if side == "BUY":
            total_required = (exec_price * quantity) + total_fees
            if total_required > self.cash:
                rejected = {
                    "order_id": order_id,
                    "client_order_id": client_oid,
                    "symbol": symbol,
                    "side": side,
                    "quantity": quantity,
                    "price": price,
                    "status": "REJECTED",
                    "rejection_reason": f"Insufficient paper cash: need {total_required:.2f}, have {self.cash:.2f}",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
                self._orders[order_id] = rejected
                self._client_order_map[client_oid] = order_id
                return rejected

            # Deduct cash
            self.cash -= total_required

            # Update position
            if symbol in self._positions:
                cur = self._positions[symbol]
                new_qty = cur["quantity"] + quantity
                new_avg = ((cur["quantity"] * cur["average_entry_price"]) + (quantity * exec_price)) / new_qty
                cur["quantity"] = new_qty
                cur["average_entry_price"] = round(new_avg, 2)
                cur["current_price"] = exec_price
                cur["updated_at"] = datetime.now(timezone.utc).isoformat()
            else:
                self._positions[symbol] = {
                    "symbol": symbol,
                    "sector": order.get("sector", "General"),
                    "quantity": quantity,
                    "average_entry_price": exec_price,
                    "current_price": exec_price,
                    "unrealized_pnl": 0.0,
                    "realized_pnl": 0.0,
                    "is_open": True,
                    "entry_time": datetime.now(timezone.utc).isoformat(),
                }

        elif side == "SELL":
            if symbol not in self._positions or self._positions[symbol]["quantity"] < quantity:
                rejected = {
                    "order_id": order_id,
                    "client_order_id": client_oid,
                    "symbol": symbol,
                    "side": side,
                    "quantity": quantity,
                    "price": price,
                    "status": "REJECTED",
                    "rejection_reason": "No open position to sell (No shorts permitted)",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
                self._orders[order_id] = rejected
                self._client_order_map[client_oid] = order_id
                return rejected

            pos = self._positions[symbol]
            entry_p = pos["average_entry_price"]
            gross_pnl = (exec_price - entry_p) * quantity
            net_pnl = gross_pnl - total_fees
            self.realized_pnl += net_pnl
            self.cash += (exec_price * quantity) - total_fees

            pos["quantity"] -= quantity
            if pos["quantity"] <= 0:
                del self._positions[symbol]
            else:
                pos["current_price"] = exec_price

        # Record filled order
        filled_order = {
            "order_id": order_id,
            "client_order_id": client_oid,
            "symbol": symbol,
            "side": side,
            "order_type": order_type,
            "quantity": quantity,
            "filled_quantity": quantity,
            "price": price,
            "average_fill_price": exec_price,
            "status": "FILLED",
            "fees": total_fees,
            "slippage_bps": abs(exec_price - price) / price * 10000,
            "submitted_at": datetime.now(timezone.utc).isoformat(),
            "completed_at": datetime.now(timezone.utc).isoformat(),
        }
        self._orders[order_id] = filled_order
        self._client_order_map[client_oid] = order_id

        logger.info(f"Paper order {order_id} FILLED: {side} {quantity} {symbol} @ Rs {exec_price:.2f}")
        return filled_order

    async def cancel_order(self, order_id: str) -> bool:
        if order_id in self._orders:
            ord_obj = self._orders[order_id]
            if ord_obj["status"] in ("SUBMITTED", "PENDING"):
                ord_obj["status"] = "CANCELLED"
                return True
        return False

    async def market_data(self, symbol: str) -> Dict[str, Any]:
        # Return latest simulated tick
        price = 1000.0
        if symbol in self._positions:
            price = self._positions[symbol]["current_price"]
        return {
            "symbol": symbol,
            "last_price": price,
            "bid": round(price * 0.9998, 2),
            "ask": round(price * 1.0002, 2),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
