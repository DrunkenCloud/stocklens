import datetime as dt
from decimal import Decimal

from services.mf import mf_positions


def tx(code, broker, kind, units, amount, date=None, n=0):
    return {"code": code, "broker": broker, "kind": kind, "units": Decimal(str(units)), "amount": Decimal(str(amount)),
            "date": date, "created_at": dt.datetime(2026, 1, 1, 0, n)}


def test_buys_accumulate_and_sells_use_average_cost():
    p = mf_positions([
        tx(1, "Groww", "buy", 10, 1000, n=1),
        tx(1, "Groww", "buy", 10, 3000, n=2),
        tx(1, "Groww", "sell", 5, 1500, n=3),
    ])
    assert p == {(1, "Groww"): {"units": 15.0, "invested": 3000.0, "realized": 500.0}}, p


def test_brokers_are_separate_positions_and_order_is_by_date():
    p = mf_positions([
        tx(1, "ICICI", "sell", 2, 300, date=dt.date(2026, 3, 1), n=1),
        tx(1, "ICICI", "buy", 4, 400, date=dt.date(2026, 2, 1), n=2),
        tx(1, "Groww", "buy", 1, 50, n=3),
    ])
    assert p[(1, "ICICI")] == {"units": 2.0, "invested": 200.0, "realized": 100.0}, p
    assert p[(1, "Groww")]["units"] == 1.0


def test_fully_sold_position_disappears():
    p = mf_positions([tx(1, "Groww", "buy", 3, 300, n=1), tx(1, "Groww", "sell", 3, 330, n=2)])
    assert p == {}, p


def test_selling_more_than_held_is_an_error():
    try:
        mf_positions([tx(1, "Groww", "buy", 1, 100, n=1), tx(1, "Groww", "sell", 2, 250, n=2)])
    except ValueError as e:
        assert "more units than held" in str(e)
    else:
        raise AssertionError("expected ValueError")


if __name__ == "__main__":
    for t in (test_buys_accumulate_and_sells_use_average_cost, test_brokers_are_separate_positions_and_order_is_by_date,
              test_fully_sold_position_disappears, test_selling_more_than_held_is_an_error):
        t()
        print(f"ok  {t.__name__}")
