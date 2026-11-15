from services.exposure import holding_asset, look_through


def fund_row(isin, name, kind, industry, pct):
    return {"isin": isin, "name": name, "holding_type": kind, "industry": industry, "pct_nav": pct}


PORTFOLIOS = {
    "F1": [fund_row("INE040A01034", "HDFC Bank", "equity", "Banks", 60.0),
           fund_row("INE154A01025", "ITC", "equity", "Diversified FMCG", 30.0),
           fund_row(None, "TREPS", "money_market", None, 10.0)],
    "F2": [fund_row("INE040A01034", "HDFC Bank", "equity", "Banks", 50.0),
           fund_row("INE002A01018", "Reliance", "equity", "Petroleum Products", 50.0)],
}
ITEMS = [
    {"label": "HDFC Bank", "kind": "stock", "isin": "INE040A01034", "value": 1000.0, "portfolio": None, "sector": "Financial Services", "asset_class": "equity"},
    {"label": "Fund One", "kind": "mf", "isin": None, "value": 2000.0, "portfolio": "F1", "sector": None, "asset_class": "equity"},
    {"label": "Fund Two", "kind": "mf", "isin": None, "value": 1000.0, "portfolio": "F2", "sector": None, "asset_class": "equity"},
    {"label": "Mystery Fund", "kind": "mf", "isin": None, "value": 500.0, "portfolio": None, "sector": None, "asset_class": "debt"},
]


def close(a, b):
    return abs(a - b) < 1e-6


def test_companies_combine_direct_and_fund_exposure():
    r = look_through(ITEMS, PORTFOLIOS, {"INE040A01034": "Banks"})
    top = r["companies"][0]
    assert (top["isin"], top["direct"], top["total"]) == ("INE040A01034", 1000.0, 1000.0 + 1200.0 + 500.0), top
    assert sorted((v["label"], v["value"]) for v in top["via"]) == [("Fund One", 1200.0), ("Fund Two", 500.0)], top
    assert close(top["weight_pct"], 2700.0 / 4500.0 * 100)


def test_sectors_use_fund_industries_for_direct_stocks_and_mark_unknown_funds():
    sectors = {s["sector"]: s["value"] for s in look_through(ITEMS, PORTFOLIOS, {"INE040A01034": "Banks"})["sectors"]}
    assert sectors == {"Banks": 2700.0, "Diversified FMCG": 600.0, "Petroleum Products": 500.0,
                       "Debt & money market": 200.0, "Not broken down": 500.0}, sectors


def test_assets_split_by_holding_type():
    assets = {a["asset"]: a["value"] for a in look_through(ITEMS, PORTFOLIOS, {})["assets"]}
    assert assets == {"equity": 3800.0, "debt": 700.0}, assets


def test_overlap_between_funds_is_sum_of_common_minimum_weights():
    r = look_through(ITEMS, PORTFOLIOS, {})
    assert r["overlap"] == [{"a": "Fund One", "b": "Fund Two", "pct": 50.0}], r["overlap"]
    assert close(r["coverage_pct"], 3000.0 / 3500.0 * 100)


def test_holding_asset_mapping():
    assert [holding_asset(t, n) for t, n in [
        ("equity", "x"), ("money_market", "x"), ("debt", "x"), ("cash", "x"), ("gold", "x"),
        ("fund_unit", "Nippon India Silver ETF"), ("reit", "x"), ("weird", "x"),
        ("commodity", "Gold 995 1KG BAR"), ("fund_unit", "JPMorgan US Technology Fund"), ("fund_unit", "Some Liquid Fund"),
        ("equity", "Senco Gold Limited")]] == [
        "equity", "debt", "debt", "cash", "gold", "silver", "other", "other",
        "gold", "equity", "debt", "equity"]


def test_holdings_of_a_silver_etf_count_as_silver_even_if_mislabelled():
    portfolios = {"S": [fund_row("INE000X01010", "Silver", "equity", None, 97.0), fund_row(None, "TREPS", "cash", None, 3.0)]}
    items = [{"label": "TATSILV", "kind": "etf", "isin": None, "value": 1000.0, "portfolio": "S", "sector": None, "asset_class": "silver"}]
    r = look_through(items, portfolios, {})
    assert {a["asset"]: a["value"] for a in r["assets"]} == {"silver": 970.0, "cash": 30.0}, r["assets"]
    assert r["companies"] == [] and {s["sector"] for s in r["sectors"]} == {"Silver", "Cash"}, r


def test_overseas_fund_units_are_equity_in_an_overseas_sector():
    portfolios = {"U": [fund_row("LU0159052710", "JPMorgan US Technology Fund", "fund_unit", None, 100.0)]}
    items = [{"label": "US Tech FoF", "kind": "mf", "isin": None, "value": 500.0, "portfolio": "U", "sector": None, "asset_class": "equity"}]
    r = look_through(items, portfolios, {})
    assert {a["asset"]: a["value"] for a in r["assets"]} == {"equity": 500.0}
    assert {s["sector"]: s["value"] for s in r["sectors"]} == {"Overseas funds": 500.0}


if __name__ == "__main__":
    for name, t in list(globals().items()):
        if name.startswith("test_"):
            t()
            print(f"ok  {name}")
