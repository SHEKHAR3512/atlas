import pytest
from services.atlas.portfolio.kelly import fractional_kelly, KellyPositionSizer


def test_fractional_kelly_standard():
    # 60% win rate, avg win 4%, avg loss -2%
    # b = 4 / 2 = 2
    # raw_kelly = (2 * 0.6 - 0.4) / 2 = (1.2 - 0.4) / 2 = 0.40
    # fractional (0.25) = 0.40 * 0.25 = 0.10
    # capped at maximum 0.03
    f = fractional_kelly(
        win_probability=0.60,
        average_win=0.04,
        average_loss=-0.02,
        fraction=0.25,
        maximum=0.03
    )
    assert f == 0.03


def test_fractional_kelly_negative_edge():
    # 40% win rate, avg win 2%, avg loss -3% -> negative expectancy
    f = fractional_kelly(
        win_probability=0.40,
        average_win=0.02,
        average_loss=-0.03,
        fraction=0.25,
        maximum=0.03
    )
    assert f == 0.0


def test_fractional_kelly_zero_loss():
    # Edge case: zero average loss
    f = fractional_kelly(
        win_probability=0.80,
        average_win=0.05,
        average_loss=0.0,
        fraction=0.25,
        maximum=0.03
    )
    assert f == 0.0


def test_kelly_position_sizer_insufficient_sample():
    sizer = KellyPositionSizer(min_trades=100, bootstrap_allocation=0.005)
    # Only 10 trades provided
    trades = [{"return_pct": 0.03}] * 6 + [{"return_pct": -0.02}] * 4
    alloc, meta = sizer.compute_allocation_pct(trades)
    assert meta["is_bootstrapped"] is True
    assert alloc == 0.005


def test_kelly_position_sizer_empty():
    sizer = KellyPositionSizer()
    alloc, meta = sizer.compute_allocation_pct([])
    assert alloc == 0.0
    assert meta["sample_size"] == 0
