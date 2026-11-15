from itertools import combinations

from services.sectors import OVERSEAS, UNCLASSIFIED, classify

ASSET_SECTOR = {"debt": "Debt & money market", "cash": "Cash", "gold": "Gold", "silver": "Silver", "other": "Other"}
_DEBT_WORDS = ("debt", "money", "bond", "gov", "treasury", "t-bill", "tbill", "gilt", "sdl", "commercial_paper", "certificate", "ncd")
_CASH_WORDS = ("cash", "treps", "net_current", "receivable", "reverse_repo")


_FUND_DEBT_WORDS = ("liquid", "debt", "bond", "gilt", "money market", "overnight")


def holding_asset(holding_type: str | None, name: str, isin: str | None = None) -> str:
    t = (holding_type or "").lower()
    n = name.lower()
    if t == "equity" or "derivative" in t or "future" in t or (isin and isin.startswith("INE") and isin[7:9] == "01"):
        return "equity"
    if any(w in t for w in _DEBT_WORDS):
        return "debt"
    if any(w in t for w in _CASH_WORDS):
        return "cash"
    if "gold" in t or (t in ("fund_unit", "etf", "commodity") and "gold" in n):
        return "gold"
    if "silver" in t or (t in ("fund_unit", "etf", "commodity") and "silver" in n):
        return "silver"
    if t in ("fund_unit", "etf"):
        return "debt" if any(w in n for w in _FUND_DEBT_WORDS) else "equity"
    return "other"


def _equity_sector(row: dict) -> tuple[str, str]:
    if not row["industry"] and (row["holding_type"] or "").lower() in ("fund_unit", "etf"):
        if row["isin"] and not row["isin"].startswith("IN"):
            return OVERSEAS, "Overseas fund units"
        return UNCLASSIFIED, "Fund units"
    return classify(row["industry"])


def _pct(part: float, whole: float) -> float | None:
    return part / whole * 100 if whole else None


def _group_sectors(industries: dict[tuple[str, str], float]) -> list[dict]:
    equity = sum(industries.values())
    grouped: dict[str, dict[str, float]] = {}
    for (macro, industry), value in industries.items():
        grouped.setdefault(macro, {})[industry] = grouped.get(macro, {}).get(industry, 0.0) + value
    out = []
    for macro, inner in grouped.items():
        value = sum(inner.values())
        if value <= 0:
            continue
        out.append({
            "sector": macro,
            "value": value,
            "weight_pct": _pct(value, equity),
            "industries": [
                {"industry": k, "value": v, "weight_pct": _pct(v, equity)}
                for k, v in sorted(inner.items(), key=lambda kv: -kv[1]) if v > 0
            ],
        })
    return sorted(out, key=lambda x: -x["value"])


def look_through(items: list[dict], portfolios: dict[str, list[dict]], industry_by_isin: dict[str, str]) -> dict:
    total = sum(i["value"] for i in items)
    companies: dict[str, dict] = {}
    sectors: dict[tuple[str, str], float] = {}
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
            add(sectors, classify(industry_by_isin.get(item["isin"]) or item.get("sector")), value)
            add(assets, "equity", value)
            continue

        fund_value += value
        rows = portfolios.get(item["portfolio"]) if item.get("portfolio") else None
        if not rows:
            asset = item.get("asset_class") or "other"
            add(assets, asset, value)
            if asset == "equity":
                add(sectors, (UNCLASSIFIED, "Funds without a published portfolio"), value)
            continue

        covered_value += value
        weights = fund_weights.setdefault(item["portfolio"], {"label": item["label"], "equity": {}})
        commodity = item.get("asset_class") if item.get("asset_class") in ("gold", "silver") else None
        for row in rows:
            share = value * row["pct_nav"] / 100
            asset = holding_asset(row["holding_type"], row["name"], row["isin"])
            if commodity and asset != "cash":
                asset = commodity
            add(assets, asset, share)
            if asset == "equity":
                add(sectors, _equity_sector(row), share)
                c = company(row["isin"], row["name"])
                c["total"] += share
                add(c["via"], item["label"], share)
                if row["isin"]:
                    weights["equity"][row["isin"]] = weights["equity"].get(row["isin"], 0.0) + row["pct_nav"]

    overlap = []
    for a, b in combinations(fund_weights.values(), 2):
        common = a["equity"].keys() & b["equity"].keys()
        pct = sum(min(a["equity"][i], b["equity"][i]) for i in common)
        if pct > 0:
            overlap.append({"a": a["label"], "b": b["label"], "pct": round(pct, 2)})
    overlap.sort(key=lambda o: -o["pct"])

    by_kind: dict[str, float] = {}
    for item in items:
        add(by_kind, item["kind"], item["value"])

    ranked = sorted(companies.values(), key=lambda c: -c["total"])
    return {
        "total": total,
        "companies": [
            {**c, "via": sorted(({"label": k, "value": v} for k, v in c["via"].items()), key=lambda v: -v["value"]),
             "weight_pct": _pct(c["total"], total)}
            for c in ranked
        ],
        "sectors": _group_sectors(sectors),
        "equity_total": sum(sectors.values()),
        "assets": [{"asset": a, "value": v, "weight_pct": _pct(v, total)} for a, v in sorted(assets.items(), key=lambda kv: -kv[1])],
        "overlap": overlap,
        "coverage_pct": _pct(covered_value, fund_value),
        "by_kind": by_kind,
    }
