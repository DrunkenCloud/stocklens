from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from db import pool
from jobs import spawn_job

router = APIRouter()

SEARCH_SQL = """
SELECT s.isin, s.name, s.nse_symbol, s.bse_code, s.bse_symbol, s.kind, s.asset_class, (c.symbol IS NOT NULL) AS tracked
FROM securities s
LEFT JOIN companies c ON c.isin = s.isin AND c.is_active
WHERE s.nse_symbol ILIKE %(prefix)s OR s.bse_symbol ILIKE %(prefix)s OR s.bse_code = %(q)s OR s.isin = upper(%(q)s)
   OR s.name ILIKE %(contains)s
ORDER BY
    CASE WHEN upper(s.nse_symbol) = upper(%(q)s) OR upper(s.bse_symbol) = upper(%(q)s) OR s.bse_code = %(q)s
              OR s.isin = upper(%(q)s) THEN 0
         WHEN s.nse_symbol ILIKE %(prefix)s OR s.bse_symbol ILIKE %(prefix)s THEN 1
         WHEN s.name ILIKE %(prefix)s THEN 2
         ELSE 3 END,
    (s.nse_symbol IS NULL),
    length(s.name), s.name
LIMIT %(limit)s
"""


def _like_escape(q: str) -> str:
    return q.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def _exchanges(row: dict) -> list[str]:
    return [ex for ex, key in (("NSE", "nse_symbol"), ("BSE", "bse_code")) if row[key]]


@router.get("/securities/search")
def search(q: str = Query(..., min_length=1, max_length=60), limit: int = Query(20, le=50)):
    q = q.strip()
    esc = _like_escape(q)
    with pool.connection() as conn:
        rows = conn.execute(SEARCH_SQL, {"q": q, "prefix": f"{esc}%", "contains": f"%{esc}%", "limit": limit}).fetchall()
    return [{**r, "exchanges": _exchanges(r)} for r in rows]


def ensure_tracked(conn, *, isin: str | None = None, symbol: str | None = None) -> tuple[str, bool]:
    if isin:
        sec = conn.execute("SELECT * FROM securities WHERE isin = %s", (isin,)).fetchone()
    else:
        symbol = (symbol or "").strip().upper()
        existing = conn.execute("SELECT symbol, is_active FROM companies WHERE symbol = %s", (symbol,)).fetchone()
        if existing and existing["is_active"]:
            return symbol, False
        sec = conn.execute(
            "SELECT * FROM securities WHERE nse_symbol = %s OR (nse_symbol IS NULL AND bse_symbol = %s) ORDER BY nse_symbol NULLS LAST LIMIT 1",
            (symbol, symbol),
        ).fetchone()
    if sec is None:
        raise HTTPException(status_code=404, detail="Stock not found in the NSE/BSE list")

    on_nse = sec["nse_symbol"] is not None
    row = {
        "symbol": sec["nse_symbol"] if on_nse else sec["bse_symbol"],
        "name": sec["name"],
        "isin": sec["isin"],
        "breeze_code": sec["breeze_code"] if on_nse else sec["bse_breeze_code"],
        "exchange": "NSE" if on_nse else "BSE",
        "kind": sec["kind"],
        "asset_class": sec["asset_class"],
    }
    created = conn.execute(
        """
        INSERT INTO companies (symbol, name, isin, breeze_code, exchange, kind, asset_class)
        VALUES (%(symbol)s, %(name)s, %(isin)s, %(breeze_code)s, %(exchange)s, %(kind)s, %(asset_class)s)
        ON CONFLICT (symbol) DO UPDATE SET is_active = TRUE, isin = EXCLUDED.isin, breeze_code = EXCLUDED.breeze_code,
            exchange = EXCLUDED.exchange, kind = EXCLUDED.kind, asset_class = EXCLUDED.asset_class
        WHERE NOT companies.is_active
        RETURNING symbol
        """,
        row,
    ).fetchone()
    return row["symbol"], created is not None


@router.get("/companies")
def list_companies():
    with pool.connection() as conn:
        return conn.execute(
            """
            SELECT c.symbol, c.name, c.sector, c.isin, lp.date AS price_date, lp.close
            FROM companies c
            LEFT JOIN LATERAL (
                SELECT date, close FROM daily_prices p WHERE p.symbol = c.symbol ORDER BY date DESC LIMIT 1
            ) lp ON TRUE
            WHERE c.is_active ORDER BY c.name
            """
        ).fetchall()


class TrackIn(BaseModel):
    isin: str


@router.post("/companies", status_code=201)
def track(body: TrackIn):
    with pool.connection() as conn:
        symbol, created = ensure_tracked(conn, isin=body.isin)
    if not created:
        raise HTTPException(status_code=409, detail=f"{symbol} is already tracked")
    return {"symbol": symbol, "run_id": spawn_job("onboard", ["--symbols", symbol], trigger="auto")}
