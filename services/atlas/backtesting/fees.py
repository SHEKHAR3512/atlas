from typing import Dict, Any
from services.atlas.core.config import config


class NSETransactionCostModel:
    """
    Realistic transaction fee model for Indian Cash Equities (NSE Delivery).
    Calculates:
      - Brokerage: min(0.05%, Rs 20)
      - STT: 0.1% on delivery (both Buy & Sell)
      - Exchange Transaction Charge: 0.00345%
      - SEBI Turnover Fee: 0.0001% (Rs 10/crore)
      - Stamp Duty: 0.015% (Buy only)
      - GST: 18% on (Brokerage + Exchange + SEBI)
    """

    def __init__(self, schedule: Dict[str, Any] = None):
        sched = schedule or config.cost_model_yaml or {}
        brokerage_conf = sched.get("brokerage", {})
        self.brokerage_pct = float(brokerage_conf.get("percent", 0.0005))
        self.max_brokerage_fixed = float(brokerage_conf.get("max_fixed", 20.0))

        stt_conf = sched.get("stt_pct", {})
        self.stt_buy = float(stt_conf.get("buy", 0.0010))
        self.stt_sell = float(stt_conf.get("sell", 0.0010))

        self.exchange_fee_pct = float(sched.get("exchange_txn_fee_pct", 0.0000345))
        self.sebi_fee_pct = float(sched.get("sebi_turnover_fee_pct", 0.000001))
        self.stamp_duty_pct = float(sched.get("stamp_duty_buy_pct", 0.00015))
        self.gst_pct = float(sched.get("gst_pct", 0.18))

    def calculate_cost(self, side: str, price: float, quantity: int) -> Dict[str, float]:
        turnover = price * quantity
        if turnover <= 0:
            return {"total_fees": 0.0, "turnover": 0.0}

        # Brokerage
        raw_brokerage = turnover * self.brokerage_pct
        brokerage = min(raw_brokerage, self.max_brokerage_fixed)

        # STT
        stt = turnover * (self.stt_buy if side.upper() == "BUY" else self.stt_sell)

        # Exchange & SEBI fees
        exchange_fee = turnover * self.exchange_fee_pct
        sebi_fee = turnover * self.sebi_fee_pct

        # Stamp duty on Buy only
        stamp_duty = (turnover * self.stamp_duty_pct) if side.upper() == "BUY" else 0.0

        # GST on (Brokerage + Exchange + SEBI)
        gst = (brokerage + exchange_fee + sebi_fee) * self.gst_pct

        total = round(brokerage + stt + exchange_fee + sebi_fee + stamp_duty + gst, 2)

        return {
            "total_fees": total,
            "brokerage": round(brokerage, 2),
            "stt": round(stt, 2),
            "exchange_fee": round(exchange_fee, 2),
            "sebi_fee": round(sebi_fee, 2),
            "stamp_duty": round(stamp_duty, 2),
            "gst": round(gst, 2),
            "turnover": round(turnover, 2),
        }
