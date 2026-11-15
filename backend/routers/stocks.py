from fastapi import APIRouter, HTTPException, Query

from db import pool

router = APIRouter()

FUNDAMENTALS_COLUMNS = "snapshot_date, pe, pb, roe, op_margin, rev_ttm, rev_growth_1y, rev_cagr_3y, debt_to_equity, dividend_yield, market_cap"


@router.get("/stocks/{symbol}")
def get_stock(symbol: str):
    with pool.connection() as conn:
        company = conn.execute(
            """
            SELECT c.symbol, c.name, c.sector, c.is_active, c.isin, s.bse_code
            FROM companies c LEFT JOIN securities s ON s.isin = c.isin
            WHERE c.symbol = %s
            """,
            (symbol,),
        ).fetchone()
        if not company:
            raise HTTPException(status_code=404, detail=f"{symbol} isn't tracked")

        fundamentals = conn.execute(
            f"SELECT {FUNDAMENTALS_COLUMNS} FROM fundamentals WHERE symbol = %s ORDER BY snapshot_date DESC LIMIT 1",
            (symbol,),
        ).fetchone()
        last2 = conn.execute(
            "SELECT date, close FROM daily_prices WHERE symbol = %s ORDER BY date DESC LIMIT 2", (symbol,)
        ).fetchall()

    latest_price = None
    if last2:
        latest_price = {**last2[0], "prev_close": last2[1]["close"] if len(last2) > 1 else None}
    return {
        **company,
        "exchanges": ["NSE"] + (["BSE"] if company.pop("bse_code") else []),
        "fundamentals": fundamentals,
        "latest_price": latest_price,
    }


@router.get("/stocks/{symbol}/fundamentals")
def get_fundamentals(symbol: str, history: bool = Query(False)):
    query = f"SELECT {FUNDAMENTALS_COLUMNS} FROM fundamentals WHERE symbol = %s ORDER BY snapshot_date"
    if not history:
        query += " DESC LIMIT 1"
    with pool.connection() as conn:
        rows = conn.execute(query, (symbol,)).fetchall()
    if not rows:
        raise HTTPException(status_code=404, detail=f"no fundamentals for {symbol}")
    return rows if history else rows[0]
