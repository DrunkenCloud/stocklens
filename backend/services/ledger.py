import bisect
import datetime as dt
from typing import Hashable

EPSILON = 1e-6


def _ordered(transactions: list[dict]) -> list[dict]:
    return sorted(transactions, key=lambda t: (t["date"] or dt.date.min, t["created_at"]))


def _apply(book: dict, t: dict) -> None:
    pos = book.setdefault(t["key"], {"units": 0.0, "invested": 0.0, "realized": 0.0})
    units, amount = float(t["units"]), float(t["amount"])
    if t["kind"] == "buy":
        pos["units"] += units
        pos["invested"] += amount
        return
    if units > pos["units"] + EPSILON:
        raise ValueError(f"sell of {units:g} units is more units than held ({pos['units']:.4f})")
    cost = pos["invested"] * units / pos["units"]
    pos["invested"] -= cost
    pos["realized"] += amount - cost
    pos["units"] -= units


def positions(transactions: list[dict]) -> dict[Hashable, dict]:
    book: dict = {}
    for t in _ordered(transactions):
        _apply(book, t)
    return {
        key: {k: round(v, 6) for k, v in pos.items()}
        for key, pos in book.items()
        if pos["units"] > EPSILON
    }


def xirr(flows: list[tuple[dt.date, float]]) -> float | None:
    if not flows or not any(a < 0 for _, a in flows) or not any(a > 0 for _, a in flows):
        return None
    start = min(d for d, _ in flows)
    years = [((d - start).days / 365.0, a) for d, a in flows]

    def npv(rate: float) -> float:
        return sum(a / (1 + rate) ** y for y, a in years)

    low, high = -0.9999, 10.0
    if npv(low) * npv(high) > 0:
        return None
    for _ in range(200):
        mid = (low + high) / 2
        if npv(low) * npv(mid) <= 0:
            high = mid
        else:
            low = mid
    return round((low + high) / 2 * 100, 4)


def growth_series(transactions: list[dict], prices: dict[Hashable, list[tuple[dt.date, float]]]) -> list[dict]:
    dated = [t for t in _ordered(transactions) if t["date"] is not None]
    if not dated:
        return []
    first = dated[0]["date"]
    calendar = sorted({d for series in prices.values() for d, _ in series if d >= first})
    price_dates = {k: [d for d, _ in v] for k, v in prices.items()}
    price_values = {k: [p for _, p in v] for k, v in prices.items()}
    last_trade_price: dict = {}
    book: dict = {}
    out, i = [], 0
    for day in calendar:
        while i < len(dated) and dated[i]["date"] <= day:
            t = dated[i]
            _apply(book, t)
            last_trade_price[t["key"]] = float(t["amount"]) / float(t["units"])
            i += 1
        value = 0.0
        for key, pos in book.items():
            if pos["units"] <= EPSILON:
                continue
            j = bisect.bisect_right(price_dates.get(key, []), day) - 1
            price = price_values[key][j] if j >= 0 else last_trade_price[key]
            value += pos["units"] * price
        invested = sum(p["invested"] for p in book.values() if p["units"] > EPSILON)
        out.append({"date": day, "invested": round(invested, 2), "value": round(value, 2)})
    return out
