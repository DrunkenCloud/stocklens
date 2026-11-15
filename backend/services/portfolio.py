def _f(v) -> float | None:
    return None if v is None else float(v)


def _pct(part: float | None, whole: float | None) -> float | None:
    return None if part is None or not whole else part / whole * 100


def summarize(rows: list[dict]) -> dict:
    holdings = []
    for r in rows:
        qty, invested, close, prev = _f(r["quantity"]), _f(r["invested"]), _f(r["close"]), _f(r["prev_close"])
        value = qty * close if close is not None else None
        day_change = qty * (close - prev) if close is not None and prev is not None else None
        holdings.append({
            **r, "quantity": qty, "invested": invested, "close": close, "prev_close": prev,
            "avg_cost": invested / qty,
            "value": value,
            "pnl": value - invested if value is not None else None,
            "pnl_pct": _pct(value - invested, invested) if value is not None else None,
            "day_change": day_change,
            "day_change_pct": _pct(day_change, qty * prev) if day_change is not None else None,
        })

    priced = [x for x in holdings if x["value"] is not None]
    total_value = sum(x["value"] for x in priced)
    priced_invested = sum(x["invested"] for x in priced)
    for x in holdings:
        x["weight_pct"] = _pct(x["value"], total_value) if x["value"] is not None else None

    with_prev = [x for x in priced if x["day_change"] is not None]
    day_change = sum(x["day_change"] for x in with_prev)
    prev_value = sum(x["quantity"] * x["prev_close"] for x in with_prev)
    pnl = total_value - priced_invested if priced else None

    brokers: dict[str, dict] = {}
    for x in holdings:
        b = brokers.setdefault(x["broker"], {"broker": x["broker"], "invested": 0.0, "value": 0.0, "priced_invested": 0.0, "count": 0})
        b["invested"] += x["invested"]
        b["count"] += 1
        if x["value"] is not None:
            b["value"] += x["value"]
            b["priced_invested"] += x["invested"]
    by_broker = []
    for b in sorted(brokers.values(), key=lambda b: -b["invested"]):
        b_pnl = b["value"] - b["priced_invested"] if b["priced_invested"] else None
        by_broker.append({"broker": b["broker"], "invested": b["invested"], "value": b["value"],
                          "pnl": b_pnl, "pnl_pct": _pct(b_pnl, b["priced_invested"]), "count": b["count"]})

    sectors: dict[str, float] = {}
    for x in priced:
        sectors[x["sector"] or "Other"] = sectors.get(x["sector"] or "Other", 0.0) + x["value"]
    by_sector = [{"sector": s, "value": v, "weight_pct": _pct(v, total_value)}
                 for s, v in sorted(sectors.items(), key=lambda kv: -kv[1])]

    classes: dict[str, float] = {}
    for x in priced:
        key = x.get("asset_class") or "equity"
        classes[key] = classes.get(key, 0.0) + x["value"]
    by_asset_class = [{"asset_class": k, "value": v, "weight_pct": _pct(v, total_value)}
                      for k, v in sorted(classes.items(), key=lambda kv: -kv[1])]

    return {
        "holdings": holdings,
        "totals": {
            "invested": sum(x["invested"] for x in holdings),
            "priced_invested": priced_invested,
            "value": total_value,
            "pnl": pnl,
            "pnl_pct": _pct(pnl, priced_invested),
            "day_change": day_change,
            "day_change_pct": _pct(day_change, prev_value) if with_prev else None,
        },
        "by_broker": by_broker,
        "by_sector": by_sector,
        "by_asset_class": by_asset_class,
    }
