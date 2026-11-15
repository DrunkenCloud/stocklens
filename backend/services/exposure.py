from itertools import combinations

ASSET_SECTOR = {"debt": "Debt & money market", "cash": "Cash", "gold": "Gold", "silver": "Silver", "other": "Other"}
UNKNOWN_SECTOR = "Not broken down"
_DEBT_WORDS = ("debt", "money", "bond", "gov", "treasury", "t-bill", "tbill", "gilt", "sdl", "commercial_paper", "certificate", "ncd")
_CASH_WORDS = ("cash", "treps", "net_current", "receivable", "reverse_repo")


def holding_asset(holding_type: str | None, name: str) -> str:
    t = (holding_type or "").lower()
    n = name.lower()
    if t == "equity":
        return "equity"
    if any(w in t for w in _DEBT_WORDS):
        return "debt"
    if any(w in t for w in _CASH_WORDS):
        return "cash"
    if "gold" in t or (t in ("fund_unit", "etf", "commodity") and "gold" in n):
        return "gold"
    if "silver" in t or (t in ("fund_unit", "etf", "commodity") and "silver" in n):
        return "silver"
    return "other"


def _pct(part: float, whole: float) -> float | None:
    return part / whole * 100 if whole else None


def look_through(items: list[dict], portfolios: dict[str, list[dict]], industry_by_isin: dict[str, str]) -> dict:
    total = sum(i["value"] for i in items)
    companies: dict[str, dict] = {}
    sectors: dict[str, float] = {}
    assets: dict[str, float] = {}
    fund_value = covered_value = 0.0
    fund_weights: dict[str, dict] = {}

    def add(bucket: dict, key: str, value: float) -> None:
        bucket[key] = bucket.get(key, 0.0) + value

    def company(isin: str | None, name: str) -> dict:
        key = isin or name
        return companies.setdefault(key, {"isin": isin, "name": name, "direct": 0.0, "via": {}, "total": 0.0})

    for item in items:
        value = item["value"]
        if item["kind"] == "stock":
            c = company(item["isin"], item["label"])
            c["direct"] += value
            c["total"] += value
            add(sectors, industry_by_isin.get(item["isin"]) or item.get("sector") or "Other", value)
            add(assets, "equity", value)
            continue

        fund_value += value
        rows = portfolios.get(item["portfolio"]) if item.get("portfolio") else None
        if not rows:
            add(sectors, UNKNOWN_SECTOR, value)
            add(assets, item.get("asset_class") or "other", value)
            continue

        covered_value += value
        weights = fund_weights.setdefault(item["portfolio"], {"label": item["label"], "equity": {}})
        for row in rows:
            share = value * row["pct_nav"] / 100
            asset = holding_asset(row["holding_type"], row["name"])
            add(assets, asset, share)
            if asset == "equity":
                add(sectors, row["industry"] or "Other", share)
                c = company(row["isin"], row["name"])
                c["total"] += share
                add(c["via"], item["label"], share)
                if row["isin"]:
                    weights["equity"][row["isin"]] = weights["equity"].get(row["isin"], 0.0) + row["pct_nav"]
            else:
                add(sectors, ASSET_SECTOR.get(asset, "Other"), share)

    overlap = []
    for a, b in combinations(fund_weights.values(), 2):
        common = a["equity"].keys() & b["equity"].keys()
        pct = sum(min(a["equity"][i], b["equity"][i]) for i in common)
        if pct > 0:
            overlap.append({"a": a["label"], "b": b["label"], "pct": round(pct, 2)})
    overlap.sort(key=lambda o: -o["pct"])

    ranked = sorted(companies.values(), key=lambda c: -c["total"])
    return {
        "total": total,
        "companies": [
            {**c, "via": sorted(({"label": k, "value": v} for k, v in c["via"].items()), key=lambda v: -v["value"]),
             "weight_pct": _pct(c["total"], total)}
            for c in ranked
        ],
        "sectors": [{"sector": s, "value": v, "weight_pct": _pct(v, total)} for s, v in sorted(sectors.items(), key=lambda kv: -kv[1])],
        "assets": [{"asset": a, "value": v, "weight_pct": _pct(v, total)} for a, v in sorted(assets.items(), key=lambda kv: -kv[1])],
        "overlap": overlap,
        "coverage_pct": _pct(covered_value, fund_value),
    }
