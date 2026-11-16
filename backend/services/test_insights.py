import datetime as dt
from decimal import Decimal

from services.insights import drawdown, month_movers

D = dt.date


def tx(key, kind, units, amount, date=None, n=0):
    return {"key": key, "kind": kind, "units": Decimal(str(units)), "amount": Decimal(str(amount)),
            "date": date, "created_at": dt.datetime(2026, 1, 1, 0, n)}


A, B = ("st", "A", "G"), ("st", "B", "G")
PRICES = {A: [(D(2026, 10, 30), 10.0), (D(2026, 11, 13), 12.0)], B: [(D(2026, 11, 5), 50.0), (D(2026, 11, 13), 45.0)]}


def test_mover_excludes_new_money():
    out = month_movers([tx(A, "buy", 10, 90, D(2026, 9, 1), 1), tx(A, "buy", 5, 55, D(2026, 11, 3), 2)], PRICES, D(2026, 11, 16))
    assert out == [{"key": A, "change": 15 * 12.0 - 10 * 10.0 - 55}], out


def test_new_position_this_month():
    out = month_movers([tx(B, "buy", 2, 100, D(2026, 11, 5), 1)], PRICES, D(2026, 11, 16))
    assert out == [{"key": B, "change": 90.0 - 100}], out


def test_sold_this_month_counts_proceeds():
    out = month_movers([tx(A, "buy", 10, 90, D(2026, 9, 1), 1), tx(A, "sell", 10, 115, D(2026, 11, 10), 2)], PRICES, D(2026, 11, 16))
    assert out == [{"key": A, "change": 115 - 100.0}], out


def test_drawdown_ignores_contributions():
    series = [
        {"date": D(2026, 1, 1), "invested": 100.0, "value": 100.0},
        {"date": D(2026, 1, 2), "invested": 200.0, "value": 200.0},
        {"date": D(2026, 1, 3), "invested": 200.0, "value": 180.0},
        {"date": D(2026, 1, 4), "invested": 100.0, "value": 90.0},
    ]
    flows = [(D(2026, 1, 1), 100.0), (D(2026, 1, 2), 100.0), (D(2026, 1, 4), -90.0)]
    out = drawdown(series, flows)
    assert round(out["current_pct"], 6) == -10.0 and round(out["max_pct"], 6) == -10.0, out
    assert out["peak_date"] == D(2026, 1, 2), out


def test_drawdown_flow_on_holiday_lands_on_next_day():
    series = [{"date": D(2026, 1, 2), "invested": 100.0, "value": 100.0}, {"date": D(2026, 1, 5), "invested": 200.0, "value": 210.0}]
    out = drawdown(series, [(D(2026, 1, 2), 100.0), (D(2026, 1, 3), 100.0)])
    assert out["current_pct"] == 0.0 and out["peak_date"] == D(2026, 1, 5), out


def test_drawdown_needs_two_points():
    assert drawdown([{"date": D(2026, 1, 1), "invested": 1.0, "value": 1.0}], []) is None


if __name__ == "__main__":
    for name, t in list(globals().items()):
        if name.startswith("test_"):
            t()
            print(f"ok  {name}")
