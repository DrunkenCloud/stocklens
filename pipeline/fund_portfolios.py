DATA_REPO = "https://raw.githubusercontent.com/kushagra-agarwal-a/fund-holdings-data/main"
CATALOG_URL = f"{DATA_REPO}/catalog/amfi-lookup.json"


def portfolio_url(as_of: str, portfolio_id: str) -> str:
    return f"{DATA_REPO}/portfolios/asof/{as_of}/{portfolio_id}.json"


def portfolio_rows(doc: dict) -> list[dict]:
    rows = []
    for position, h in enumerate(doc.get("holdings", [])):
        if h.get("pct_nav") in (None, ""):
            continue
        rows.append({
            "position": position,
            "isin": h.get("isin") or None,
            "name": (h.get("instrument") or "").strip(),
            "holding_type": h.get("holding_type") or None,
            "industry": h.get("industry") or None,
            "pct_nav": float(h["pct_nav"]),
        })
    return rows
