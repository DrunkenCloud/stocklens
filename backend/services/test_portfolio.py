from decimal import Decimal

from services.portfolio import summarize


def h(symbol, qty, invested, close, prev, broker, sector, asset_class="equity"):
    return {"id": symbol, "symbol": symbol, "name": symbol.title(), "sector": sector, "quantity": Decimal(qty),
            "invested": Decimal(invested), "broker": broker, "source": "manual",
            "close": None if close is None else Decimal(close), "prev_close": None if prev is None else Decimal(prev),
            "price_date": None, "buy_date": None, "note": None, "asset_class": asset_class, "kind": "stock"}


ITC = h("ITC", "10", "4000", "450", "440", "Zerodha", "FMCG")
TCS = h("TCS", "2", "7000", "3000", "3100", "ICICI", "IT")
BEL = h("BEL", "5", "1500", None, None, "ICICI", None)
GOLD = h("GOLDBEES", "10", "800", "100", "100", "Zerodha", None, "gold")


def close(a, b):
    return a is not None and abs(a - b) < 1e-6


def test_per_holding_numbers():
    by = {x["symbol"]: x for x in summarize([ITC, TCS, BEL])["holdings"]}
    itc = by["ITC"]
    assert (itc["avg_cost"], itc["value"], itc["pnl"], itc["day_change"]) == (400.0, 4500.0, 500.0, 100.0), itc
    assert close(itc["pnl_pct"], 12.5) and close(itc["weight_pct"], 4500 / 10500 * 100), itc
    assert close(itc["day_change_pct"], 100 / 4400 * 100), itc
    bel = by["BEL"]
    assert [bel[k] for k in ("value", "pnl", "pnl_pct", "day_change", "weight_pct")] == [None] * 5, bel
    assert bel["avg_cost"] == 300.0


def test_totals_count_unpriced_in_invested_but_not_pnl():
    t = summarize([ITC, TCS, BEL])["totals"]
    assert (t["invested"], t["priced_invested"], t["value"], t["pnl"], t["day_change"]) == (12500.0, 11000.0, 10500.0, -500.0, -100.0), t
    assert close(t["pnl_pct"], -500 / 11000 * 100) and close(t["day_change_pct"], -100 / 10600 * 100), t


def test_broker_and_sector_breakdowns():
    s = summarize([ITC, TCS, BEL])
    assert [(b["broker"], b["invested"], b["value"], b["pnl"], b["count"]) for b in s["by_broker"]] == [
        ("ICICI", 8500.0, 6000.0, -1000.0, 2), ("Zerodha", 4000.0, 4500.0, 500.0, 1)], s["by_broker"]
    assert close(s["by_broker"][0]["pnl_pct"], -1000 / 7000 * 100)
    assert [x["sector"] for x in s["by_sector"]] == ["IT", "FMCG"], s["by_sector"]
    assert close(sum(x["weight_pct"] for x in s["by_sector"]), 100.0)


def test_nothing_priced_or_nothing_held_does_not_divide_by_zero():
    t = summarize([BEL])["totals"]
    assert (t["invested"], t["value"], t["pnl"], t["pnl_pct"], t["day_change_pct"]) == (1500.0, 0.0, None, None, None), t
    empty = summarize([])
    assert empty["holdings"] == [] and empty["by_broker"] == [] and empty["totals"]["invested"] == 0.0, empty


def test_asset_class_split_uses_current_value():
    s = summarize([ITC, TCS, GOLD, BEL])
    assert [(a["asset_class"], a["value"]) for a in s["by_asset_class"]] == [("equity", 10500.0), ("gold", 1000.0)], s["by_asset_class"]
    assert close(sum(a["weight_pct"] for a in s["by_asset_class"]), 100.0)


if __name__ == "__main__":
    for t in (test_asset_class_split_uses_current_value, test_per_holding_numbers, test_totals_count_unpriced_in_invested_but_not_pnl,
              test_broker_and_sector_breakdowns, test_nothing_priced_or_nothing_held_does_not_divide_by_zero):
        t()
        print(f"ok  {t.__name__}")
