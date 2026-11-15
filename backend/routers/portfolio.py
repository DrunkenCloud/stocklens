"""Holdings across brokers. ICICI rows (source='icici_sync') are replaced on each
sync and read-only here; Zerodha/Groww/other rows are entered by hand as
quantity + total invested. Adding a holding for an untracked stock tracks it."""
import datetime as dt
import uuid

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, model_validator

from db import pool
from jobs import spawn_job
from routers.securities import ensure_tracked
from services.portfolio import summarize

router = APIRouter()

DEFAULT_USER_ID = "00000000-0000-0000-0000-000000000001"  # single-user app, seeded by migration 001

HOLDINGS_SQL = """
SELECT h.id, h.symbol, c.name, c.sector, h.quantity, h.invested, h.broker, h.source, h.buy_date, h.note,
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


@router.get("/portfolio")
def get_portfolio():
    with pool.connection() as conn:
        rows = conn.execute(HOLDINGS_SQL, (DEFAULT_USER_ID,)).fetchall()
    return summarize(rows)


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
