"""Self-check for return formulas. Run: python -m services.test_returns"""
import datetime as dt

from services.returns import (
    best_worst_year,
    cagr_pct,
    compute_returns,
    max_drawdown_pct,
    total_return_pct,
    value_of_lump_sum,
)


def test_total_return_pct():
    assert total_return_pct(100, 150) == 50.0
    assert total_return_pct(100, 50) == -50.0


def test_cagr_pct():
    # 100 -> 200 over exactly 2 years => 1.2^... actually sqrt(2)-1 ~= 41.42%
    d0, d1 = dt.date(2020, 1, 1), dt.date(2022, 1, 1)
    result = cagr_pct(100, 200, d0, d1)
    assert abs(result - 41.42) < 0.1

    # sub-1-year period is guarded to None, never silently annualized
    assert cagr_pct(100, 110, dt.date(2020, 1, 1), dt.date(2020, 6, 1)) is None


def test_value_of_lump_sum():
    assert value_of_lump_sum(1000, 100, 150) == 1500.0


def test_max_drawdown_pct():
    # peak 100 -> trough 50 -> partial recovery to 80: max dd is -50%
    assert max_drawdown_pct([100, 80, 50, 70, 80]) == -50.0
    # monotonically rising series: no drawdown
    assert max_drawdown_pct([100, 110, 120]) == 0.0


def test_best_worst_year():
    dates = [dt.date(2020, 1, 1), dt.date(2020, 12, 31), dt.date(2021, 1, 1), dt.date(2021, 12, 31)]
    closes = [100, 120, 120, 90]  # 2020: +20%, 2021: -25%
    best, worst = best_worst_year(dates, closes)
    assert best == {"year": 2020, "return_pct": 20.0}
    assert worst["year"] == 2021
    assert abs(worst["return_pct"] - (-25.0)) < 1e-9


def test_compute_returns_shape():
    dates = [dt.date(2020, 1, 1), dt.date(2021, 1, 1)]
    closes = [100, 150]
    out = compute_returns(dates, closes, amount=1000)
    assert out["total_return_pct"] == 50.0
    assert out["value_now"] == 1500.0
    assert out["date_start"] == dates[0] and out["date_end"] == dates[1]


if __name__ == "__main__":
    test_total_return_pct()
    test_cagr_pct()
    test_value_of_lump_sum()
    test_max_drawdown_pct()
    test_best_worst_year()
    test_compute_returns_shape()
    print("ok")
