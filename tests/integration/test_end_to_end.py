import pytest
from services.atlas.brokers.paper import PaperBroker
from services.atlas.risk.engine import RiskEngine
from services.atlas.execution.engine import ExecutionEngine
from services.atlas.portfolio.allocator import PortfolioAllocator
from services.atlas.strategies.base import StrategySignal
from services.atlas.core.constants import MarketRegime, OrderSide
from services.atlas.execution.reconciliation import ReconciliationService


@pytest.mark.asyncio
async def test_full_pipeline_end_to_end():
    # 1. Initialize paper broker with Rs 100,000 capital
    broker = PaperBroker(initial_cash=200000.0)
    await broker.connect()

    account_before = await broker.account()
    assert account_before["cash"] == 200000.0

    # 2. Strategy generates signal
    sig = StrategySignal(
        symbol="RELIANCE",
        direction=OrderSide.BUY,
        strength=1.0,
        strategy_key="trend_following_v1",
        price=2800.0,
        market_regime=MarketRegime.BULL_TREND.value,
        metadata={"atr": 30.0},
    )

    # 3. Portfolio Allocator calculates position with Fractional Kelly (>=100 validated sample trades)
    allocator = PortfolioAllocator()
    sample_trades = [
        {"return_pct": 0.045}, {"return_pct": -0.018}, {"return_pct": 0.035},
        {"return_pct": 0.052}, {"return_pct": -0.015}, {"return_pct": 0.028},
    ] * 20 # 120 trades
    alloc = allocator.allocate_signal(
        signal=sig,
        portfolio_equity=200000.0,
        available_cash=200000.0,
        active_positions=[],
        historical_trades=sample_trades,
        current_regime=MarketRegime.BULL_TREND,
        strategy_meta={"id": "trend_following_v1", "compatible_regimes": ["bull_trend"]},
    )

    assert alloc["proposed_quantity"] > 0
    proposed_qty = alloc["proposed_quantity"]

    # 4. Deterministic Risk Engine evaluation
    risk_engine = RiskEngine()
    decision = risk_engine.evaluate_order_proposal(
        portfolio=account_before,
        positions=[],
        signal=sig.model_dump(),
        market={"symbol": "RELIANCE", "sector": "Energy"},
        strategy={"id": "trend_following_v1", "status": "APPROVED"},
        proposed_order={
            "symbol": "RELIANCE",
            "side": "BUY",
            "quantity": proposed_qty,
            "price": 2800.0,
        }
    )

    assert decision["approved"] is True
    assert decision["approved_quantity"] > 0
    approved_qty = decision["approved_quantity"]

    # 5. Execution Engine dispatches to PaperBroker
    exec_engine = ExecutionEngine(broker=broker)
    order_res = await exec_engine.execute_approved_order(
        symbol="RELIANCE",
        side="BUY",
        quantity=approved_qty,
        price=2800.0,
        strategy_key="trend_following_v1",
    )

    assert order_res["status"] == "FILLED"
    assert order_res["filled_quantity"] == approved_qty
    assert order_res["fees"] > 0 # Fees deducted

    # 6. Verify Portfolio and Position Book state
    account_after = await broker.account()
    positions_after = await broker.positions()

    assert account_after["cash"] < 200000.0
    assert len(positions_after) == 1
    assert positions_after[0]["symbol"] == "RELIANCE"
    assert positions_after[0]["quantity"] == approved_qty

    # 7. Position Reconciliation Check
    reconciler = ReconciliationService(broker=broker)
    synced, discrepancies = await reconciler.reconcile_positions(positions_after)
    assert synced is True
    assert len(discrepancies) == 0
