from pipeline.mf import category_asset_class, parse_navall

SAMPLE = """Scheme Code;ISIN Div Payout/ ISIN Growth;ISIN Div Reinvestment;Scheme Name;Plan;Option;Net Asset Value;Date
 
Open Ended Schemes(Equity Scheme - Small Cap Fund)
 
Bandhan Mutual Fund
 
147944;INF194KB1AL4;-;Bandhan Small Cap Fund;Regular Plan;Growth Option;58.1234;13-Nov-2026
147946;INF194KB1AM2;INF194KB1AN0;Bandhan Small Cap Fund;Regular Plan;IDCW Option;30.5;13-Nov-2026
 
Open Ended Schemes(Income/Debt Oriented Schemes - Ultra Short to Short Term Fund)
 
ICICI Prudential Mutual Fund
 
120505;INF109K01VQ1;-;ICICI Prudential Ultra Short to Short Term Fund;Regular Plan;Growth Option;28.4;13-Nov-2026
999999;-;-;Broken Fund;Direct Plan;Growth Option;N.A.;13-Nov-2026
152684;INF209KC1118;-;Aditya Birla Sun Life Quant Fund;Direct Plan;GROWTH;10.56;13-Nov-2026
152651;INF247L01CL8;-;Motilal Oswal Multi Cap Fund;;;16.2650;13-Nov-2026
"""


def test_parses_schemes_with_category_and_amc():
    rows = {r["code"]: r for r in parse_navall(SAMPLE)}
    assert set(rows) == {147944, 147946, 120505, 152684, 152651}, rows
    assert (rows[152684]["plan"], rows[152684]["option"]) == ("Direct", "Growth")
    assert (rows[152651]["plan"], rows[152651]["option"]) == (None, None)
    r = rows[147944]
    assert (r["name"], r["amc"], r["category"], r["plan"], r["option"], r["isin"], r["nav"], r["nav_date"].isoformat()) == (
        "Bandhan Small Cap Fund", "Bandhan Mutual Fund", "Equity Scheme - Small Cap Fund", "Regular", "Growth",
        "INF194KB1AL4", 58.1234, "2026-11-13"), r
    assert rows[147946]["isin_reinvest"] == "INF194KB1AN0" and rows[147946]["option"] == "IDCW"
    assert rows[120505]["asset_class"] == "debt" and rows[147944]["asset_class"] == "equity"


def test_category_asset_class():
    cases = {
        ("Equity Scheme - Flexi Cap Fund", "x"): "equity",
        ("Other Scheme - Index Funds", "Groww Nifty Total Market Index Fund"): "equity",
        ("Income/Debt Oriented Schemes - Liquid Fund", "x"): "debt",
        ("Hybrid Schemes - Arbitrage Fund", "x"): "hybrid",
        ("Other Scheme - Gold ETF", "x"): "gold",
        ("Other Scheme - FoF Domestic", "Some Silver Fund of Fund"): "silver",
        ("Other Scheme - FoF Overseas", "Edelweiss US Technology Equity Fund of Fund"): "equity",
        ("Solution Oriented Scheme - Retirement Fund", "x"): "hybrid",
    }
    for (category, name), expected in cases.items():
        assert category_asset_class(category, name) == expected, (category, name)


if __name__ == "__main__":
    for t in (test_parses_schemes_with_category_and_amc, test_category_asset_class):
        t()
        print(f"ok  {t.__name__}")
