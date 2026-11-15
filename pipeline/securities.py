import csv
import io
import re

NSE_SERIES_PRIORITY = ["EQ", "BE", "BZ", "SM", "ST"]
_SMALL_WORDS = {"OF", "AND", "THE", "FOR", "IN", "ON", "AT", "TO"}
_SUFFIX = re.compile(r"\s+(LIMITED|LTD\.?)$")


def clean_name(raw: str) -> str:
    name = _SUFFIX.sub("", raw.strip().upper())
    words = []
    for i, w in enumerate(name.split()):
        if w in _SMALL_WORDS and i > 0:
            words.append(w.lower())
        elif len(w) <= 3 or not w.isalpha() or not re.search("[AEIOU]", w):
            words.append(w)
        else:
            words.append(w.capitalize())
    return " ".join(words)


def _rows(text: str) -> list[dict]:
    reader = csv.reader(io.StringIO(text), skipinitialspace=True)
    header = [h.strip() for h in next(reader)]
    return [dict(zip(header, row)) for row in reader if row]


def _is_equity(isin: str) -> bool:
    return isin.startswith("INE") and isin[7:9] == "01"


def _is_etf(isin: str, series: str) -> bool:
    return isin.startswith("INF") and series == "EQ"


def etf_asset_class(name: str) -> str:
    upper = name.upper()
    if "GOLD" in upper:
        return "gold"
    if "SILVER" in upper:
        return "silver"
    if any(w in upper for w in ("LIQUID", "BOND", "GILT", "1D RATE", "G-SEC", "GSEC", "SDL", "MONEY MARKET")):
        return "debt"
    return "equity"


def parse_security_master(nse_text: str, bse_text: str) -> list[dict]:
    out: dict[str, dict] = {}

    for r in _rows(nse_text):
        isin, series = r["ISINCode"].strip(), r["Series"].strip()
        if r.get("DateOfDeListing", "").strip():
            continue
        etf = _is_etf(isin, series)
        if not etf and (not _is_equity(isin) or series not in NSE_SERIES_PRIORITY):
            continue
        current = out.get(isin)
        if current and NSE_SERIES_PRIORITY.index(current["nse_series"]) <= NSE_SERIES_PRIORITY.index(series):
            continue
        out[isin] = {
            "isin": isin, "name": r["CompanyName"].strip() if etf else clean_name(r["CompanyName"]),
            "nse_symbol": r["ExchangeCode"].strip(), "breeze_code": r["ShortName"].strip(), "nse_series": series,
            "bse_code": None, "bse_symbol": None, "bse_breeze_code": None, "kind": "etf" if etf else "stock",
            "asset_class": etf_asset_class(r["CompanyName"]) if etf else "equity",
        }

    for r in _rows(bse_text):
        isin = r["ISINCode"].strip()
        if r.get("DateOfDeListing", "").strip():
            continue
        if not _is_equity(isin) and isin not in out:
            continue
        row = out.setdefault(isin, {
            "isin": isin, "name": clean_name(r["CompanyName"]), "nse_symbol": None, "breeze_code": None,
            "nse_series": None, "bse_code": None, "bse_symbol": None, "bse_breeze_code": None, "kind": "stock",
            "asset_class": "equity",
        })
        row["bse_code"] = r["ScripCode"].strip()
        row["bse_symbol"] = r["ScripID"].strip()
        row["bse_breeze_code"] = r["ShortName"].strip()

    return list(out.values())
