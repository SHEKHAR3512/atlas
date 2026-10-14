import pytest
from services.atlas.risk.engine import RiskEngine
from services.atlas.risk.circuit_breaker import circuit_breaker
from services.atlas.core.constants import StrategyStatus


def test_risk_engine_position_limit_rejection():
    engine = RiskEngine()
    portfolio = {"equity": 100000.0, "cash": 50000.0}
    positions = []
    signal = {"symbol": "RELIANCE"}
    market = {"sector": "Energy"}
    strategy = {"id": "trend_v1", "status": "APPROVED"}

    # Equity is 100,000, 3% max position = 3,000
    # Trying to buy 50 shares @ 2800 = 140,000 -> exceeds limit
    proposed = {"symbol": "RELIANCE", "side": "BUY", "quantity": 50, "price": 2800.0}

    decision = engine.evaluate_order_proposal(
        portfolio=portfolio,
        positions=positions,
        signal=signal,
        market=market,
        strategy=strategy,
        proposed_order=proposed,
    )

    # Risk engine scales down to approved_quantity = 1 (1 * 2800 <= 3000)
    assert decision["approved"] is True
    assert decision["approved_quantity"] == 1
    assert decision["decision"] == "MODIFIED"


def test_risk_engine_kill_switch_blocks_orders():
    engine = RiskEngine()
    circuit_breaker.trigger_kill_switch("Emergency test halt")

    decision = engine.evaluate_order_proposal(
        portfolio={"equity": 100000.0},
        positions=[],
        signal={},
        market={},
        strategy={"status": "APPROVED"},
        proposed_order={"symbol": "TCS", "side": "BUY", "quantity": 5, "price": 3800.0},
    )

    assert decision["approved"] is False
    assert decision["approved_quantity"] == 0
    assert "Kill Switch" in decision["reason"]

    # Reset
    circuit_breaker.reset_kill_switch("TEST")


def test_risk_engine_retired_strategy_blocked():
    engine = RiskEngine()
    decision = engine.evaluate_order_proposal(
        portfolio={"equity": 100000.0},
        positions=[],
        signal={},
        market={},
        strategy={"id": "old_strat", "status": StrategyStatus.RETIRED.value},
        proposed_order={"symbol": "INFY", "side": "BUY", "quantity": 5, "price": 1700.0},
    )

    assert decision["approved"] is False
    assert "RETIRED" in decision["reason"]


def test_risk_engine_daily_loss_breach():
    engine = RiskEngine()
    # 2% loss already experienced today (limit is 1.5%)
    portfolio = {
        "equity": 98000.0,
        "start_of_day_equity": 100000.0,
        "high_water_mark": 100000.0,
    }

    decision = engine.evaluate_order_proposal(
        portfolio=portfolio,
        positions=[],
        signal={},
        market={},
        strategy={"status": "APPROVED"},
        proposed_order={"symbol": "INFY", "side": "BUY", "quantity": 1, "price": 1700.0},
    )

    assert decision["approved"] is False
    assert "Daily loss breach" in decision["reason"]
