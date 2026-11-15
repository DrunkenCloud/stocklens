EQUITY_EXCHANGES = {"NSE", "BSE", ""}
REQUIRED = ("stock_code", "quantity", "average_price")


def parse_portfolio_holdings(resp) -> list[tuple[str, float, float]]:
    rows = resp.get("Success") if isinstance(resp, dict) else None
    if not isinstance(rows, list):
        error = resp.get("Error") if isinstance(resp, dict) else None
        raise ValueError(f"unexpected holdings response (Error={error!r}): {str(resp)[:300]}")

    merged: dict[str, tuple[float, float]] = {}
    for r in rows:
        missing = [k for k in REQUIRED if k not in r]
        if missing:
            raise ValueError(f"holdings row missing {missing}; got fields {sorted(r)}")
        if (r.get("exchange_code") or "").upper() not in EQUITY_EXCHANGES:
            continue
        qty = float(r["quantity"] or 0)
        if qty <= 0:
            continue
        code = r["stock_code"].strip()
        prev_qty, prev_cost = merged.get(code, (0.0, 0.0))
        merged[code] = (prev_qty + qty, prev_cost + qty * float(r["average_price"]))

    return [(code, qty, cost / qty) for code, (qty, cost) in sorted(merged.items())]
