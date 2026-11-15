from fastapi import APIRouter, Query

from db import pool

router = APIRouter()

SORTABLE_COLUMNS = {"pe", "pb", "roe", "debt_to_equity", "dividend_yield", "rev_cagr_3y", "market_cap", "symbol"}

QUERY = """
WITH latest_fundamentals AS (
    SELECT DISTINCT ON (symbol)
        symbol, snapshot_date, pe, pb, roe, debt_to_equity, dividend_yield, rev_cagr_3y, market_cap
    FROM fundamentals
    ORDER BY symbol, snapshot_date DESC
),
latest_prices AS (
    SELECT DISTINCT ON (symbol) symbol, close
    FROM daily_prices
    ORDER BY symbol, date DESC
)
SELECT c.symbol, c.name, c.sector, lf.pe, lf.pb, lf.roe, lf.debt_to_equity,
       lf.dividend_yield, lf.rev_cagr_3y, lf.market_cap, lp.close AS latest_close
FROM companies c
LEFT JOIN latest_fundamentals lf ON lf.symbol = c.symbol
LEFT JOIN latest_prices lp ON lp.symbol = c.symbol
WHERE c.is_active
  AND (%(pe_max)s::numeric IS NULL OR lf.pe <= %(pe_max)s::numeric)
  AND (%(pe_min)s::numeric IS NULL OR lf.pe >= %(pe_min)s::numeric)
  AND (%(pb_max)s::numeric IS NULL OR lf.pb <= %(pb_max)s::numeric)
  AND (%(roe_min)s::numeric IS NULL OR lf.roe >= %(roe_min)s::numeric)
  AND (%(de_max)s::numeric IS NULL OR lf.debt_to_equity <= %(de_max)s::numeric)
  AND (%(div_yield_min)s::numeric IS NULL OR lf.dividend_yield >= %(div_yield_min)s::numeric)
  AND (%(rev_cagr_3y_min)s::numeric IS NULL OR lf.rev_cagr_3y >= %(rev_cagr_3y_min)s::numeric)
  AND (%(sector)s::text IS NULL OR c.sector = %(sector)s::text)
ORDER BY {order_clause}
LIMIT %(limit)s::int
"""


@router.get("/screen")
def screen(
    pe_max: float | None = None,
    pe_min: float | None = None,
    pb_max: float | None = None,
    roe_min: float | None = None,
    de_max: float | None = None,
    div_yield_min: float | None = None,
    rev_cagr_3y_min: float | None = None,
    sector: str | None = None,
    sort_by: str = "market_cap",
    order: str = "desc",
    limit: int = Query(50, le=500),
):
    sort_col = sort_by if sort_by in SORTABLE_COLUMNS else "market_cap"
    sort_dir = "ASC" if order.lower() == "asc" else "DESC"
    order_clause = f"lf.{sort_col} {sort_dir} NULLS LAST" if sort_col != "symbol" else f"c.symbol {sort_dir}"

    with pool.connection() as conn:
        rows = conn.execute(
            QUERY.format(order_clause=order_clause),
            {
                "pe_max": pe_max, "pe_min": pe_min, "pb_max": pb_max, "roe_min": roe_min,
                "de_max": de_max, "div_yield_min": div_yield_min, "rev_cagr_3y_min": rev_cagr_3y_min,
                "sector": sector, "limit": limit,
            },
        ).fetchall()

    return rows
