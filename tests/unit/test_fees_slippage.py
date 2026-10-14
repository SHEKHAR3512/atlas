import pytest
from services.atlas.backtesting.fees import NSETransactionCostModel
from services.atlas.backtesting.slippage import SlippageModel


def test_nse_transaction_costs_buy():
    model = NSETransactionCostModel()
    # Buying 10 shares @ 3000 = Rs 30,000 turnover
    costs = model.calculate_cost("BUY", price=3000.0, quantity=10)

    assert costs["turnover"] == 30000.0
    assert costs["brokerage"] <= 20.0 # capped at Rs 20
    assert costs["stt"] == 30.0 # 0.1% on delivery = Rs 30
    assert costs["stamp_duty"] > 0.0 # stamp duty exists on buy
    assert costs["total_fees"] > 50.0


def test_nse_transaction_costs_sell():
    model = NSETransactionCostModel()
    costs = model.calculate_cost("SELL", price=3000.0, quantity=10)
    assert costs["stamp_duty"] == 0.0 # No stamp duty on sell delivery
    assert costs["stt"] == 30.0 # STT charged on sell delivery too


def test_slippage_model():
    model = SlippageModel(default_bps=10.0) # 0.10%

    buy_exec = model.calculate_slippage("BUY", price=1000.0, quantity=10)
    sell_exec = model.calculate_slippage("SELL", price=1000.0, quantity=10)

    # Buy slippage increases price paid
    assert buy_exec > 1000.0
    # Sell slippage reduces price received
    assert sell_exec < 1000.0
