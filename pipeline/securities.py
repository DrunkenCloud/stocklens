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


def parse_security_master(nse_text: str, bse_text: str) -> list[dict]:
    out: dict[str, dict] = {}

    for r in _rows(nse_text):
        isin, series = r["ISINCode"].strip(), r["Series"].strip()
        if not _is_equity(isin) or series not in NSE_SERIES_PRIORITY or r.get("DateOfDeListing", "").strip():
            continue
        current = out.get(isin)
        if current and NSE_SERIES_PRIORITY.index(current["nse_series"]) <= NSE_SERIES_PRIORITY.index(series):
            continue
        out[isin] = {
            "isin": isin, "name": clean_name(r["CompanyName"]), "nse_symbol": r["ExchangeCode"].strip(),
            "breeze_code": r["ShortName"].strip(), "nse_series": series, "bse_code": None, "bse_symbol": None,
        }

    for r in _rows(bse_text):
        isin = r["ISINCode"].strip()
        if not _is_equity(isin) or r.get("DateOfDeListing", "").strip():
            continue
        row = out.setdefault(isin, {
            "isin": isin, "name": clean_name(r["CompanyName"]), "nse_symbol": None,
            "breeze_code": None, "nse_series": None, "bse_code": None, "bse_symbol": None,
        })
        row["bse_code"] = r["ScripCode"].strip()
        row["bse_symbol"] = r["ScripID"].strip()

    return list(out.values())
