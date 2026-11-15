"""Self-check for securities.parse_security_master. Run: python -m pipeline.test_securities
Fixture rows follow the real SecurityMaster.zip format (quoted CSV, a space after
each comma, header row), trimmed to the columns the parser reads."""
from pipeline.securities import clean_name, parse_security_master

NSE = '''"Token", "ShortName", "Series", "CompanyName", "DateOfDeListing", "ISINCode", "ExchangeCode"
"2885","RELIND","EQ","RELIANCE INDUSTRIES","","INE002A01018","RELIANCE"
"2886","RELIND","BL","RELIANCE INDUSTRIES","","INE002A01018","RELIANCE"
"100","ACRTEC","BE","ACROPETAL TECHNOLOGIES LIMITED","","INE055L01013","ACROPETAL"
"200","GONE","EQ","DELISTED CO LTD","01-Jan-2024","INE999Z01011","GONECO"
"300","GSEC","GS","GOVT BOND 2030","","IN0020200012","GS2030"
"400","OLDSER","N1","SOME NCD","","INE123A07015","SOMENCD"
'''

BSE = '''"Token", "ShortName", "Series", "CompanyName", "ScripCode", "ScripID", "DateOfDeListing", "ISINCode", "ExchangeCode"
"500325","RELIND","DR","RELIANCE INDUSTRIES","500325","RELIANCE","","INE002A01018","RELIANCE"
"543210","BSEONL","DR","BSE ONLY TRADERS LTD","543210","BSEONLY","","INE777B01012","BSEONLY"
"800078","03D001","DR","11.10% GOI LOAN","800078","CG1110S9803","","INY019980013","CG1110S9803"
'''


def by_isin():
    return {r["isin"]: r for r in parse_security_master(NSE, BSE)}


def test_merges_nse_and_bse_listings_by_isin():
    r = by_isin()["INE002A01018"]
    assert r == {
        "isin": "INE002A01018", "name": "Reliance Industries", "nse_symbol": "RELIANCE",
        "breeze_code": "RELIND", "nse_series": "EQ", "bse_code": "500325", "bse_symbol": "RELIANCE",
    }, r


def test_be_series_counts_as_nse_listing():
    r = by_isin()["INE055L01013"]
    assert (r["nse_symbol"], r["nse_series"], r["bse_code"]) == ("ACROPETAL", "BE", None), r


def test_bse_only_stock_has_no_nse_symbol():
    r = by_isin()["INE777B01012"]
    assert (r["nse_symbol"], r["breeze_code"], r["bse_code"], r["name"]) == (None, None, "543210", "BSE Only Traders"), r


def test_skips_non_equity_and_delisted():
    isins = set(by_isin())
    assert isins == {"INE002A01018", "INE055L01013", "INE777B01012"}, isins


def test_clean_name_keeps_acronyms_and_drops_limited():
    assert clean_name("HDFC BANK LIMITED") == "HDFC Bank"
    assert clean_name("STATE BANK OF INDIA") == "State Bank of India"
    assert clean_name("ITC LTD.") == "ITC"
    assert clean_name("MAHINDRA & MAHINDRA LIMITED") == "Mahindra & Mahindra"
    assert clean_name("  ACROPETAL TECHNOLOGIES LIMITED ") == "Acropetal Technologies"


if __name__ == "__main__":
    for t in (test_clean_name_keeps_acronyms_and_drops_limited, test_merges_nse_and_bse_listings_by_isin, test_be_series_counts_as_nse_listing,
              test_bse_only_stock_has_no_nse_symbol, test_skips_non_equity_and_delisted):
        t()
        print(f"ok  {t.__name__}")
