import datetime as dt
from decimal import Decimal

from services.tax import fifo, fy_bounds, long_term_on, tax_class, tax_report

D = dt.date


def tx(key, kind, units, amount, date=None, n=0):
    return {"key": key, "kind": kind, "units": Decimal(str(units)), "amount": Decimal(str(amount)),
            "date": date, "created_at": dt.datetime(2026, 1, 1, 0, n)}


A = ("st", "A", "Zerodha")


def meta(cls="equity", price=20.0):
    return {A: {"name": "Alpha", "tax_class": cls, "price": price, "symbol": "A", "kind": "stock", "broker": "Zerodha"}}


def test_sell_spans_lots_fifo():
    lots, realised = fifo([
        tx(A, "buy", 10, 100, D(2024, 1, 1), 1),
        tx(A, "buy", 10, 200, D(2025, 1, 1), 2),
        tx(A, "sell", 15, 450, D(2026, 6, 1), 3),
    ])
    assert [(l["date"], l["units"], l["cost"]) for l in lots] == [(D(2025, 1, 1), 5.0, 100.0)], lots
    assert [(r["buy_date"], r["units"], r["cost"], r["proceeds"]) for r in realised] == [
        (D(2024, 1, 1), 10.0, 100.0, 300.0), (D(2025, 1, 1), 5.0, 100.0, 150.0)], realised


def test_long_term_after_12_months_plus_a_day():
    assert long_term_on(D(2025, 11, 20), "equity") == D(2026, 11, 21)
    assert long_term_on(D(2024, 2, 29), "listed_other") == D(2025, 3, 1)


def test_fof_needs_24_months():
    assert long_term_on(D(2025, 1, 10), "unlisted_other") == D(2027, 1, 11)


def test_debt_after_april_2023_never_long_term():
    assert long_term_on(D(2023, 4, 1), "debt") is None
    assert long_term_on(D(2023, 3, 31), "debt") == D(2025, 4, 1)


def test_undated_lot_has_no_long_term_date():
    lots, _ = fifo([tx(A, "buy", 10, 100, None, 1)])
    report = tax_report(lots, [], meta(), D(2026, 11, 16))
    assert report["lots"][0]["term"] == "unknown" and report["lots"][0]["long_term_on"] is None
    assert report["upcoming"] == []
    assert report["unrealised"]["equity"]["unknown"] == 100.0


def test_fy_bounds():
    assert fy_bounds(D(2026, 11, 16)) == (D(2026, 4, 1), D(2027, 3, 31))
    assert fy_bounds(D(2027, 2, 1)) == (D(2026, 4, 1), D(2027, 3, 31))
    assert fy_bounds(D(2026, 3, 31)) == (D(2025, 4, 1), D(2026, 3, 31))


def test_exemption_counts_only_equity_long_term_realised():
    lots, realised = fifo([
        tx(A, "buy", 10, 100, D(2024, 1, 1), 1),
        tx(A, "buy", 10, 100, D(2026, 5, 1), 2),
        tx(A, "sell", 20, 600, D(2026, 6, 1), 3),
    ])
    report = tax_report(lots, realised, meta(), D(2026, 11, 16))
    assert report["realised"]["equity"] == {"short": 200.0, "long": 200.0, "unknown": 0.0}, report["realised"]
    assert report["exemption"] == {"limit": 125000, "used": 200.0, "remaining": 124800.0}
    other = tax_report(lots, realised, meta("listed_other"), D(2026, 11, 16))
    assert other["exemption"]["used"] == 0


def test_realised_outside_fy_ignored():
    lots, realised = fifo([tx(A, "buy", 10, 100, D(2024, 1, 1), 1), tx(A, "sell", 5, 100, D(2026, 3, 1), 2)])
    report = tax_report(lots, realised, meta(), D(2026, 11, 16))
    assert report["realised"] == {}


def test_upcoming_and_unrealised_terms():
    lots, _ = fifo([tx(A, "buy", 10, 100, D(2024, 1, 1), 1), tx(A, "buy", 10, 150, D(2025, 12, 20), 2)])
    report = tax_report(lots, [], meta(price=20.0), D(2026, 11, 16))
    assert report["unrealised"]["equity"] == {"short": 50.0, "long": 100.0, "unknown": 0.0}
    up = report["upcoming"]
    assert len(up) == 1 and up[0]["long_term_on"] == D(2026, 12, 21) and up[0]["days_left"] == 35, up
    assert up[0]["gain"] == 50.0


def test_tax_class_rules():
    cases = [
        (("stock", "equity", None), "equity"),
        (("etf", "equity", None), "equity"),
        (("etf", "gold", None), "listed_other"),
        (("etf", "silver", None), "listed_other"),
        (("etf", "debt", None), "debt"),
        (("mf", "equity", "Equity Scheme - Small Cap Fund"), "equity"),
        (("mf", "equity", "Index Funds - Equity Funds"), "equity"),
        (("mf", "equity", "Other Scheme - FoF Overseas"), "unlisted_other"),
        (("mf", "gold", "Other Scheme - Gold ETF"), "unlisted_other"),
        (("mf", "debt", "Income/Debt Oriented Schemes - Ultra Short Duration Fund"), "debt"),
        (("mf", "hybrid", "Hybrid Scheme - Arbitrage Fund"), "equity"),
        (("mf", "hybrid", "Hybrid Scheme - Balanced Advantage"), "equity"),
        (("mf", "hybrid", "Hybrid Scheme - Conservative Hybrid Fund"), "debt"),
        (("mf", "hybrid", "Hybrid Scheme - Multi Asset Allocation"), "unlisted_other"),
        (("mf", "other", None), "unlisted_other"),
    ]
    for args, want in cases:
        assert tax_class(*args) == want, (args, tax_class(*args))


if __name__ == "__main__":
    for name, t in list(globals().items()):
        if name.startswith("test_"):
            t()
            print(f"ok  {name}")
