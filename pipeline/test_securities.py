from pipeline.securities import clean_name, etf_asset_class, parse_security_master

NSE = '''"Token", "ShortName", "Series", "CompanyName", "DateOfDeListing", "ISINCode", "ExchangeCode"
"2885","RELIND","EQ","RELIANCE INDUSTRIES","","INE002A01018","RELIANCE"
"2886","RELIND","BL","RELIANCE INDUSTRIES","","INE002A01018","RELIANCE"
"100","ACRTEC","BE","ACROPETAL TECHNOLOGIES LIMITED","","INE055L01013","ACROPETAL"
"200","GONE","EQ","DELISTED CO LTD","01-Jan-2024","INE999Z01011","GONECO"
"300","GSEC","GS","GOVT BOND 2030","","IN0020200012","GS2030"
"400","OLDSER","N1","SOME NCD","","INE123A07015","SOMENCD"
"500","GOLDEX","EQ","NIPPON INDIA ETF GOLD BEES","","INF204KB17I5","GOLDBEES"
"600","SOMEMF","MF","SOME LISTED MF UNITS","","INF999X01AA1","SOMEMF"
'''

BSE = '''"Token", "ShortName", "Series", "CompanyName", "ScripCode", "ScripID", "DateOfDeListing", "ISINCode", "ExchangeCode"
"500325","RELIND","DR","RELIANCE INDUSTRIES","500325","RELIANCE","","INE002A01018","RELIANCE"
"543210","BSEONL","DR","BSE ONLY TRADERS LTD","543210","BSEONLY","","INE777B01012","BSEONLY"
"800078","03D001","DR","11.10% GOI LOAN","800078","CG1110S9803","","INY019980013","CG1110S9803"
"590095","GOLDBE","DR","NIPPON INDIA ETF GOLD BEES","590095","GOLDBEES","","INF204KB17I5","GOLDBEES"
"700001","BSEMF","DR","BSE ONLY MF UNITS","700001","BSEMF","","INF888Y01BB2","BSEMF"
'''


def by_isin():
    return {r["isin"]: r for r in parse_security_master(NSE, BSE)}


def test_merges_nse_and_bse_listings_by_isin():
    r = by_isin()["INE002A01018"]
    assert r == {
        "isin": "INE002A01018", "name": "Reliance Industries", "nse_symbol": "RELIANCE",
        "breeze_code": "RELIND", "nse_series": "EQ", "bse_code": "500325", "bse_symbol": "RELIANCE",
        "bse_breeze_code": "RELIND", "kind": "stock", "asset_class": "equity",
    }, r


def test_be_series_counts_as_nse_listing():
    r = by_isin()["INE055L01013"]
    assert (r["nse_symbol"], r["nse_series"], r["bse_code"]) == ("ACROPETAL", "BE", None), r


def test_bse_only_stock_has_no_nse_symbol():
    r = by_isin()["INE777B01012"]
    assert (r["nse_symbol"], r["breeze_code"], r["bse_code"], r["name"]) == (None, None, "543210", "BSE Only Traders"), r
    assert r["bse_breeze_code"] == "BSEONL", r


def test_nse_listed_etf_is_kept_as_etf():
    r = by_isin()["INF204KB17I5"]
    assert (r["nse_symbol"], r["breeze_code"], r["kind"], r["bse_code"], r["asset_class"]) == ("GOLDBEES", "GOLDEX", "etf", "590095", "gold"), r


def test_fund_units_outside_nse_eq_series_are_dropped():
    assert "INF999X01AA1" not in by_isin() and "INF888Y01BB2" not in by_isin()


def test_etf_asset_class_from_name():
    assert etf_asset_class("NIPPON INDIA ETF GOLD BEES") == "gold"
    assert etf_asset_class("TATA SILVER ETF") == "silver"
    assert etf_asset_class("GROWW NIFTY 1D RATE LIQUID ETF") == "debt"
    assert etf_asset_class("BHARAT BOND ETF APRIL 2030") == "debt"
    assert etf_asset_class("ZERODHA NIFTY SMALLCAP 100 ETF") == "equity"


def test_skips_non_equity_and_delisted():
    isins = set(by_isin())
    assert isins == {"INE002A01018", "INE055L01013", "INE777B01012", "INF204KB17I5"}, isins


def test_clean_name_keeps_acronyms_and_drops_limited():
    assert clean_name("HDFC BANK LIMITED") == "HDFC Bank"
    assert clean_name("STATE BANK OF INDIA") == "State Bank of India"
    assert clean_name("ITC LTD.") == "ITC"
    assert clean_name("MAHINDRA & MAHINDRA LIMITED") == "Mahindra & Mahindra"
    assert clean_name("  ACROPETAL TECHNOLOGIES LIMITED ") == "Acropetal Technologies"


if __name__ == "__main__":
    for t in (test_clean_name_keeps_acronyms_and_drops_limited, test_merges_nse_and_bse_listings_by_isin, test_be_series_counts_as_nse_listing,
              test_bse_only_stock_has_no_nse_symbol, test_skips_non_equity_and_delisted,
              test_nse_listed_etf_is_kept_as_etf, test_fund_units_outside_nse_eq_series_are_dropped, test_etf_asset_class_from_name):
        t()
        print(f"ok  {t.__name__}")
