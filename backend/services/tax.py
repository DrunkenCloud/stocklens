import datetime as dt

from services.benchmark import months_back

EXEMPTION = 125000
UPCOMING_DAYS = 90
DEBT_CUTOFF = dt.date(2023, 4, 1)
HOLD_MONTHS = {"equity": 12, "listed_other": 12, "unlisted_other": 24, "debt": 24}
EQUITY_HYBRIDS = ("arbitrage", "equity savings", "aggressive", "balanced advantage", "dynamic asset")


def tax_class(kind: str, asset_class: str | None, category: str | None) -> str:
    cat = (category or "").lower()
    if kind == "etf":
        return {"equity": "equity", "gold": "listed_other", "silver": "listed_other", "debt": "debt"}.get(asset_class or "", "listed_other")
    if kind != "mf":
        return "equity"
    if "fof" in cat or "fund of funds" in cat:
        return "unlisted_other"
    if asset_class == "equity":
        return "equity"
    if asset_class == "debt":
        return "debt"
    if asset_class == "hybrid":
        if any(h in cat for h in EQUITY_HYBRIDS):
            return "equity"
        if "conservative" in cat:
            return "debt"
    return "unlisted_other"


def long_term_on(buy: dt.date, cls: str) -> dt.date | None:
    if cls == "debt" and buy >= DEBT_CUTOFF:
        return None
    return months_back(buy, -HOLD_MONTHS[cls]) + dt.timedelta(days=1)


def fy_bounds(today: dt.date) -> tuple[dt.date, dt.date]:
    start = today.year if today.month >= 4 else today.year - 1
    return dt.date(start, 4, 1), dt.date(start + 1, 3, 31)


def fifo(txs: list[dict]) -> tuple[list[dict], list[dict]]:
    ordered = sorted(txs, key=lambda t: (t["date"] or dt.date.min, t["created_at"]))
    open_lots: dict = {}
    realised = []
    for t in ordered:
        units, amount = float(t["units"]), float(t["amount"])
        queue = open_lots.setdefault(t["key"], [])
        if t["kind"] == "buy":
            queue.append({"key": t["key"], "date": t["date"], "units": units, "cost": amount})
            continue
        left = units
        while left > 1e-9 and queue:
            lot = queue[0]
            take = min(left, lot["units"])
            cost = lot["cost"] * take / lot["units"]
            realised.append({"key": t["key"], "buy_date": lot["date"], "sell_date": t["date"], "units": take,
                             "cost": cost, "proceeds": amount * take / units})
            lot["units"] -= take
            lot["cost"] -= cost
            left -= take
            if lot["units"] <= 1e-9:
                queue.pop(0)
    return [l for q in open_lots.values() for l in q], realised


def _term(buy: dt.date | None, cls: str, on: dt.date | None) -> str:
    if buy is None or on is None:
        return "unknown"
    lt = long_term_on(buy, cls)
    if lt is None:
        return "always_short"
    return "long" if on >= lt else "short"


def _bucket(totals: dict, cls: str, term: str, gain: float) -> None:
    b = totals.setdefault(cls, {"short": 0.0, "long": 0.0, "unknown": 0.0})
    b["long" if term == "long" else "unknown" if term == "unknown" else "short"] += gain


def tax_report(lots: list[dict], realised: list[dict], meta: dict, today: dt.date) -> dict:
    fy_start, fy_end = fy_bounds(today)
    realised_totals: dict = {}
    for r in realised:
        if r["sell_date"] is None or not fy_start <= r["sell_date"] <= fy_end:
            continue
        cls = meta[r["key"]]["tax_class"]
        _bucket(realised_totals, cls, _term(r["buy_date"], cls, r["sell_date"]), r["proceeds"] - r["cost"])

    unrealised: dict = {}
    out_lots, upcoming = [], []
    for lot in lots:
        m = meta[lot["key"]]
        cls = m["tax_class"]
        value = lot["units"] * m["price"] if m["price"] is not None else None
        gain = value - lot["cost"] if value is not None else None
        lt = long_term_on(lot["date"], cls) if lot["date"] else None
        term = _term(lot["date"], cls, today)
        row = {"name": m["name"], "symbol": m["symbol"], "kind": m["kind"], "broker": m["broker"], "tax_class": cls,
               "date": lot["date"], "units": lot["units"], "cost": lot["cost"], "value": value, "gain": gain,
               "term": term, "long_term_on": lt}
        out_lots.append(row)
        if gain is not None:
            _bucket(unrealised, cls, term, gain)
        if lt and today < lt <= today + dt.timedelta(days=UPCOMING_DAYS):
            upcoming.append({**row, "days_left": (lt - today).days})

    used = min(EXEMPTION, max(0.0, realised_totals.get("equity", {}).get("long", 0.0)))
    return {
        "fy": {"start": fy_start, "end": fy_end},
        "exemption": {"limit": EXEMPTION, "used": used, "remaining": EXEMPTION - used},
        "realised": realised_totals,
        "unrealised": unrealised,
        "upcoming": sorted(upcoming, key=lambda r: r["long_term_on"]),
        "lots": sorted(out_lots, key=lambda r: (r["name"], r["broker"], r["date"] or dt.date.min)),
    }
