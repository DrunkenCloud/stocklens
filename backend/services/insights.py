import bisect
import datetime as dt


def month_movers(txs: list[dict], prices: dict, today: dt.date) -> list[dict]:
    month_start = today.replace(day=1)
    keys: dict = {}
    for t in txs:
        k = keys.setdefault(t["key"], {"start_units": 0.0, "units": 0.0, "net_in": 0.0})
        sign = 1 if t["kind"] == "buy" else -1
        units = float(t["units"]) * sign
        k["units"] += units
        if t["date"] is None or t["date"] < month_start:
            k["start_units"] += units
        elif t["date"] <= today:
            k["net_in"] += float(t["amount"]) * sign
    out = []
    for key, k in keys.items():
        series = prices.get(key, [])
        before = [p for p in series if p[0] < month_start]
        if not series or (k["start_units"] > 1e-9 and not before):
            continue
        start_value = k["start_units"] * before[-1][1] if before else 0.0
        if abs(k["start_units"]) < 1e-9 and abs(k["net_in"]) < 1e-9:
            continue
        out.append({"key": key, "change": k["units"] * series[-1][1] - start_value - k["net_in"]})
    return out


def drawdown(series: list[dict], flows: list[tuple[dt.date, float]]) -> dict | None:
    if len(series) < 2:
        return None
    dates = [p["date"] for p in series]
    flow_on = [0.0] * len(series)
    for day, amount in flows:
        i = bisect.bisect_left(dates, day)
        if 0 < i < len(series):
            flow_on[i] += amount
    index, peak, peak_date, worst = 1.0, 1.0, dates[0], 0.0
    for i in range(1, len(series)):
        prev = series[i - 1]["value"]
        if prev > 0:
            index *= (series[i]["value"] - flow_on[i]) / prev
        if index >= peak:
            peak, peak_date = index, dates[i]
        worst = min(worst, (index / peak - 1) * 100)
    return {"current_pct": (index / peak - 1) * 100, "peak_date": peak_date, "max_pct": worst}
