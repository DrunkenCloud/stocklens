import datetime as dt
from decimal import Decimal

from services.ledger import growth_series, positions, xirr

D = dt.date


def tx(key, kind, units, amount, date=None, n=0):
    return {"key": key, "kind": kind, "units": Decimal(str(units)), "amount": Decimal(str(amount)),
            "date": date, "created_at": dt.datetime(2026, 1, 1, 0, n)}


def test_buys_accumulate_and_sells_use_average_cost():
    p = positions([tx("A", "buy", 10, 1000, n=1), tx("A", "buy", 10, 3000, n=2), tx("A", "sell", 5, 1500, n=3)])
    assert p == {"A": {"units": 15.0, "invested": 3000.0, "realized": 500.0}}, p


def test_order_is_by_date_and_keys_are_separate():
    p = positions([
        tx(("A", "ICICI"), "sell", 2, 300, date=D(2026, 3, 1), n=1),
        tx(("A", "ICICI"), "buy", 4, 400, date=D(2026, 2, 1), n=2),
        tx(("A", "Groww"), "buy", 1, 50, n=3),
    ])
    assert p[("A", "ICICI")] == {"units": 2.0, "invested": 200.0, "realized": 100.0}, p
    assert p[("A", "Groww")]["units"] == 1.0


def test_fully_sold_position_disappears():
    assert positions([tx("A", "buy", 3, 300, n=1), tx("A", "sell", 3, 330, n=2)]) == {}


def test_selling_more_than_held_is_an_error():
    try:
        positions([tx("A", "buy", 1, 100, n=1), tx("A", "sell", 2, 250, n=2)])
    except ValueError as e:
        assert "more units than held" in str(e)
    else:
        raise AssertionError("expected ValueError")


def test_xirr_of_doubling_in_one_year_is_100_percent():
    assert abs(xirr([(D(2025, 1, 1), -1000.0), (D(2026, 1, 1), 2000.0)]) - 100.0) < 0.01


def test_xirr_with_two_buys():
    r = xirr([(D(2025, 1, 1), -1000.0), (D(2025, 7, 1), -1000.0), (D(2026, 1, 1), 2300.0)])
    assert 17.0 < r < 21.0, r


def test_xirr_needs_a_sign_change():
    assert xirr([(D(2025, 1, 1), -1000.0)]) is None


def test_growth_series_tracks_invested_and_value():
    txs = [
        tx("A", "buy", 10, 1000, date=D(2026, 1, 2), n=1),
        tx("B", "buy", 5, 500, date=D(2026, 1, 3), n=2),
        tx("A", "sell", 5, 600, date=D(2026, 1, 5), n=3),
    ]
    prices = {
        "A": [(D(2026, 1, 2), 100.0), (D(2026, 1, 3), 110.0), (D(2026, 1, 5), 120.0)],
        "B": [(D(2026, 1, 2), 99.0), (D(2026, 1, 5), 90.0)],
    }
    s = {p["date"]: p for p in growth_series(txs, prices)}
    assert list(s) == [D(2026, 1, 2), D(2026, 1, 3), D(2026, 1, 5)], list(s)
    assert (s[D(2026, 1, 2)]["invested"], s[D(2026, 1, 2)]["value"]) == (1000.0, 1000.0)
    assert (s[D(2026, 1, 3)]["invested"], s[D(2026, 1, 3)]["value"]) == (1500.0, 10 * 110.0 + 5 * 99.0)
    assert (s[D(2026, 1, 5)]["invested"], s[D(2026, 1, 5)]["value"]) == (1000.0, 5 * 120.0 + 5 * 90.0)


def test_growth_series_ignores_undated_entries():
    txs = [tx("A", "buy", 1, 100, date=None, n=1), tx("B", "buy", 1, 10, date=D(2026, 1, 2), n=2)]
    s = growth_series(txs, {"A": [(D(2026, 1, 2), 150.0)], "B": [(D(2026, 1, 2), 12.0)]})
    assert s == [{"date": D(2026, 1, 2), "invested": 10.0, "value": 12.0}], s


if __name__ == "__main__":
    tests = [v for k, v in dict(globals()).items() if k.startswith("test_")]
    for t in tests:
        t()
        print(f"ok  {t.__name__}")
