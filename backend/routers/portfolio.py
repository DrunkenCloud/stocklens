import datetime as dt
import uuid

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field, model_validator

from db import pool
from jobs import spawn_job
from routers.mf import mf_history, mf_rows
from routers.securities import ensure_tracked
from services.portfolio import summarize

router = APIRouter()

DEFAULT_USER_ID = "00000000-0000-0000-0000-000000000001"

HOLDINGS_SQL = """
SELECT h.id, h.symbol, c.name, c.sector, c.kind, c.asset_class, c.exchange, h.quantity, h.invested, h.broker, h.source, h.buy_date, h.note,
       p.close, p.prev_close, p.price_date
FROM holdings h
JOIN companies c ON c.symbol = h.symbol
LEFT JOIN LATERAL (
    SELECT (array_agg(close ORDER BY date DESC))[1] AS close,
           (array_agg(close ORDER BY date DESC))[2] AS prev_close,
           max(date) AS price_date
    FROM (SELECT date, close FROM daily_prices dp WHERE dp.symbol = h.symbol ORDER BY date DESC LIMIT 2) last2
) p ON TRUE
WHERE h.user_id = %s
ORDER BY h.created_at
"""


class HoldingIn(BaseModel):
    symbol: str | None = None
    isin: str | None = None
    quantity: float = Field(gt=0)
    invested: float = Field(gt=0)
    broker: str = Field(min_length=1, max_length=40)
    buy_date: dt.date | None = None
    note: str | None = Field(None, max_length=500)

    @model_validator(mode="after")
    def _needs_stock(self):
        if not (self.symbol or self.isin):
            raise ValueError("symbol or isin required")
        return self


SPARK_SQL = """
SELECT symbol, array_agg(close::float ORDER BY date) AS closes
FROM (
    SELECT symbol, date, close, row_number() OVER (PARTITION BY symbol ORDER BY date DESC) AS rn
    FROM daily_prices WHERE symbol = ANY(%s)
) recent
WHERE rn <= %s
GROUP BY symbol
"""

HISTORY_SQL = """
WITH held AS (
    SELECT symbol, sum(quantity) AS qty FROM holdings h
    WHERE user_id = %(user)s AND EXISTS (SELECT 1 FROM daily_prices dp WHERE dp.symbol = h.symbol)
    GROUP BY symbol
),
days AS (
    SELECT DISTINCT date FROM daily_prices
    WHERE date >= %(since)s AND symbol IN (SELECT symbol FROM held)
)
SELECT d.date, sum(h.qty * p.close)::float AS value
FROM days d
CROSS JOIN held h
JOIN LATERAL (
    SELECT close FROM daily_prices dp WHERE dp.symbol = h.symbol AND dp.date <= d.date ORDER BY dp.date DESC LIMIT 1
) p ON TRUE
GROUP BY d.date
HAVING count(*) = (SELECT count(*) FROM held)
ORDER BY d.date
"""
SPARK_DAYS = 30


Scope = Query("all", pattern="^(all|stocks|mf)$")


@router.get("/portfolio")
def get_portfolio(scope: str = Scope):
    with pool.connection() as conn:
        rows = conn.execute(HOLDINGS_SQL, (DEFAULT_USER_ID,)).fetchall() if scope != "mf" else []
        sparks = {
            r["symbol"]: r["closes"]
            for r in conn.execute(SPARK_SQL, (list({r["symbol"] for r in rows}), SPARK_DAYS))
        }
        funds = mf_rows(conn) if scope != "stocks" else []
    summary = summarize(rows + funds)
    for h in summary["holdings"]:
        if h.get("kind") != "mf":
            h["spark"] = sparks.get(h["symbol"], [])
    return summary


@router.get("/portfolio/history")
def get_history(days: int = Query(365, ge=7, le=365 * 12), scope: str = Scope):
    since = dt.date.today() - dt.timedelta(days=days)
    with pool.connection() as conn:
        stocks = (
            {r["date"]: r["value"] for r in conn.execute(HISTORY_SQL, {"user": DEFAULT_USER_ID, "since": since})}
            if scope != "mf" else {}
        )
        funds = mf_history(conn, since) if scope != "stocks" else {}
    if stocks and funds:
        dates = sorted(stocks.keys() & funds.keys())
    else:
        dates = sorted(stocks or funds)
    return [{"date": d, "value": stocks.get(d, 0.0) + funds.get(d, 0.0)} for d in dates]


def _resolve(conn, holding: HoldingIn) -> tuple[str, bool]:
    return ensure_tracked(conn, isin=holding.isin, symbol=holding.symbol)


def _require_manual(conn, holding_id: uuid.UUID) -> None:
    row = conn.execute(
        "SELECT source FROM holdings WHERE id = %s AND user_id = %s", (str(holding_id), DEFAULT_USER_ID)
    ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="holding not found")
    if row["source"] == "icici_sync":
        raise HTTPException(status_code=409, detail="Synced from ICICI - it's replaced on every sync, so edit it there")


@router.post("/portfolio", status_code=201)
def add_holding(holding: HoldingIn):
    with pool.connection() as conn:
        symbol, newly_tracked = _resolve(conn, holding)
        row = conn.execute(
            """
            INSERT INTO holdings (user_id, symbol, quantity, invested, broker, buy_date, note)
            VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id
            """,
            (DEFAULT_USER_ID, symbol, holding.quantity, holding.invested, holding.broker.strip(), holding.buy_date, holding.note),
        ).fetchone()
    if newly_tracked:
        spawn_job("onboard", ["--symbols", symbol], trigger="auto")
    return {"id": str(row["id"]), "symbol": symbol, "newly_tracked": newly_tracked}


@router.put("/portfolio/{holding_id}")
def update_holding(holding_id: uuid.UUID, holding: HoldingIn):
    with pool.connection() as conn:
        _require_manual(conn, holding_id)
        symbol, newly_tracked = _resolve(conn, holding)
        conn.execute(
            """
            UPDATE holdings SET symbol = %s, quantity = %s, invested = %s, broker = %s, buy_date = %s, note = %s
            WHERE id = %s AND user_id = %s
            """,
            (symbol, holding.quantity, holding.invested, holding.broker.strip(), holding.buy_date, holding.note,
             str(holding_id), DEFAULT_USER_ID),
        )
    if newly_tracked:
        spawn_job("onboard", ["--symbols", symbol], trigger="auto")
    return {"status": "updated"}


@router.delete("/portfolio/{holding_id}", status_code=204)
def delete_holding(holding_id: uuid.UUID):
    with pool.connection() as conn:
        _require_manual(conn, holding_id)
        conn.execute("DELETE FROM holdings WHERE id = %s AND user_id = %s", (str(holding_id), DEFAULT_USER_ID))
