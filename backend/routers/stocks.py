from fastapi import APIRouter, HTTPException, Query

from db import pool

router = APIRouter()

FUNDAMENTALS_COLUMNS = [
    "pe", "pb", "roe", "op_margin", "rev_ttm", "rev_growth_1y",
    "rev_cagr_3y", "debt_to_equity", "dividend_yield", "market_cap",
]


def _row_to_fundamentals(row) -> dict:
    snapshot_date, *values = row
    return {
        "snapshot_date": snapshot_date,
        **{c: (float(v) if v is not None else None) for c, v in zip(FUNDAMENTALS_COLUMNS, values)},
    }


@router.get("/stocks/{symbol}")
def get_stock(symbol: str):
    with pool.connection() as conn:
        company = conn.execute(
            "SELECT symbol, name, sector, is_active FROM companies WHERE symbol = %s", (symbol,)
        ).fetchone()
        if not company:
            raise HTTPException(status_code=404, detail=f"unknown symbol {symbol}")

        latest_fundamentals = conn.execute(
            f"""
            SELECT snapshot_date, {", ".join(FUNDAMENTALS_COLUMNS)}
            FROM fundamentals WHERE symbol = %s ORDER BY snapshot_date DESC LIMIT 1
            """,
            (symbol,),
        ).fetchone()

        latest_price = conn.execute(
            "SELECT date, close FROM daily_prices WHERE symbol = %s ORDER BY date DESC LIMIT 1",
            (symbol,),
        ).fetchone()

    return {
        "symbol": company[0],
        "name": company[1],
        "sector": company[2],
        "is_active": company[3],
        "fundamentals": _row_to_fundamentals(latest_fundamentals) if latest_fundamentals else None,
        "latest_price": {"date": latest_price[0], "close": float(latest_price[1])} if latest_price else None,
    }


@router.get("/stocks/{symbol}/fundamentals")
def get_fundamentals(symbol: str, history: bool = Query(False)):
    query = f"SELECT snapshot_date, {', '.join(FUNDAMENTALS_COLUMNS)} FROM fundamentals WHERE symbol = %s ORDER BY snapshot_date"
    if not history:
        query += " DESC LIMIT 1"

    with pool.connection() as conn:
        rows = conn.execute(query, (symbol,)).fetchall()

    if not rows:
        raise HTTPException(status_code=404, detail=f"no fundamentals for {symbol}")

    result = [_row_to_fundamentals(r) for r in rows]
    return result if history else result[0]
