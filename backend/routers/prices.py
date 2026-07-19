import datetime as dt

from fastapi import APIRouter, HTTPException, Query

from db import pool
from services.returns import compute_returns

router = APIRouter()


@router.get("/prices/{symbol}")
def get_prices(
    symbol: str,
    from_: dt.date | None = Query(None, alias="from"),
    to: dt.date | None = None,
):
    query = "SELECT date, open, high, low, close, volume FROM daily_prices WHERE symbol = %s"
    params: list = [symbol]
    if from_:
        query += " AND date >= %s"
        params.append(from_)
    if to:
        query += " AND date <= %s"
        params.append(to)
    query += " ORDER BY date"

    with pool.connection() as conn:
        rows = conn.execute(query, params).fetchall()

    if not rows:
        raise HTTPException(status_code=404, detail=f"no price data for {symbol}")

    return [
        {
            "date": r[0],
            "open": float(r[1]) if r[1] is not None else None,
            "high": float(r[2]) if r[2] is not None else None,
            "low": float(r[3]) if r[3] is not None else None,
            "close": float(r[4]),
            "volume": r[5],
        }
        for r in rows
    ]


@router.get("/prices/{symbol}/returns")
def get_returns(
    symbol: str,
    from_: dt.date = Query(..., alias="from"),
    amount: float = 100000,
):
    with pool.connection() as conn:
        rows = conn.execute(
            "SELECT date, close FROM daily_prices WHERE symbol = %s AND date >= %s ORDER BY date",
            (symbol, from_),
        ).fetchall()

    if not rows:
        raise HTTPException(status_code=404, detail=f"no price data for {symbol} from {from_}")

    dates = [r[0] for r in rows]
    closes = [float(r[1]) for r in rows]
    result = compute_returns(dates, closes, amount)
    result["is_price_return_only"] = True  # not dividend-adjusted (05_SCHEMA_AND_API.md honesty note)
    return result
