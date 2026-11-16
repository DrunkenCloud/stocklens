import datetime as dt

from pipeline.jobs.daily_report import inr, pct, render, should_send

D = dt.date(2026, 11, 16)


def h(name, kind, change, value, date="2026-11-16"):
    return {"name": name, "kind": kind, "day_change": change, "day_change_pct": change / value * 100, "value": value, "price_date": date, "broker": "Groww"}


DATA = {
    "status": {"prices_as_of": "2026-11-16"},
    "portfolio": {
        "totals": {"value": 263179.43, "day_change": -1599.05, "day_change_pct": -0.6039, "xirr": 21.41},
        "holdings": [h("Lalithaa", "stock", -540.0, 26556), h("Ather", "stock", 180.0, 5818), h("Fund X", "mf", 900.0, 60000, "2026-11-13")],
    },
    "benchmarks": {"indices": [{"name": "Nifty 50", "day_pct": 0.58, "xirr": 9.2}, {"name": "Sensex", "day_pct": -0.31, "xirr": 8.8}]},
    "tax": {"upcoming": [{"name": "Tata Steel", "broker": "Zerodha", "long_term_on": "2026-11-21", "days_left": 5, "gain": 820.0},
                        {"name": "Far", "broker": "Groww", "long_term_on": "2027-01-30", "days_left": 75, "gain": 10.0}]},
    "insights": {"movers": {"up": [{"name": "BEL", "broker": "Groww", "change": 1200.0}], "down": []}},
}


def test_inr_and_pct():
    assert inr(263179.43) == "₹2,63,179"
    assert inr(-1599.05) == "−₹1,599"
    assert inr(1599.05, sign=True) == "+₹1,599"
    assert inr(12345678) == "₹1,23,45,678"
    assert inr(950) == "₹950"
    assert pct(-0.6039) == "−0.6%" and pct(0.58) == "+0.6%" and pct(None) == "–"


def test_should_send():
    assert should_send({"prices_as_of": "2026-11-16"}, D, sent_today=False)
    assert not should_send({"prices_as_of": "2026-11-13"}, D, sent_today=False)
    assert not should_send({"prices_as_of": "2026-11-16"}, D, sent_today=True)


def test_render_contains_value_and_sign():
    subject, text, html = render(DATA, D)
    assert subject == "StockLens · Mon 16 Nov · ₹2,63,179 (−0.6%)", subject
    for s in ("−₹1,599", "Nifty 50 +0.6%", "Sensex −0.3%", "Ather", "Lalithaa", "Tata Steel", "21 Nov", "BEL", "XIRR 21.4%"):
        assert s in text, (s, text)
        assert s in html, (s, html)
    assert "Fund X" not in text.split("This month")[0]
    assert "Far" not in text


def test_empty_sections_omitted():
    data = {**DATA, "tax": {"upcoming": []}, "insights": {"movers": {"up": [], "down": []}}}
    _, text, _ = render(data, D)
    assert "long-term" not in text and "This month" not in text, text


if __name__ == "__main__":
    for name, t in list(globals().items()):
        if name.startswith("test_"):
            t()
            print(f"ok  {name}")
