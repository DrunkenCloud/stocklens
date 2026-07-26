import datetime as dt
import uuid

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from db import pool

router = APIRouter()

# v1 is single-user, no auth (06_DECISIONS.md D9). Seeded in db/seed.sql.
DEFAULT_USER_ID = "00000000-0000-0000-0000-000000000001"


class HoldingIn(BaseModel):
    symbol: str
    quantity: float
    avg_cost: float
    buy_date: dt.date | None = None
    account: str | None = None
    note: str | None = None


def _holding_with_returns(row) -> dict:
    id_, symbol, quantity, avg_cost, buy_date, account, note, latest_close = row
    quantity = float(quantity)
    avg_cost = float(avg_cost)
    latest_close = float(latest_close) if latest_close is not None else None
    cost_basis = avg_cost * quantity
    current_value = latest_close * quantity if latest_close is not None else None
    gain = current_value - cost_basis if current_value is not None else None
    gain_pct = (latest_close - avg_cost) / avg_cost * 100 if latest_close is not None else None
    return {
        "id": str(id_), "symbol": symbol, "quantity": quantity, "avg_cost": avg_cost,
        "buy_date": buy_date, "account": account, "note": note,
        "latest_close": latest_close, "cost_basis": cost_basis,
        "current_value": current_value, "gain": gain, "gain_pct": gain_pct,
    }


def _require_known_symbol(conn, symbol: str) -> None:
    if not conn.execute("SELECT 1 FROM companies WHERE symbol = %s", (symbol,)).fetchone():
        raise HTTPException(status_code=400, detail=f"unknown symbol {symbol}")


@router.get("/portfolio")
def get_portfolio():
    with pool.connection() as conn:
        rows = conn.execute(
            """
            SELECT h.id, h.symbol, h.quantity, h.avg_cost, h.buy_date, h.account, h.note, lp.close
            FROM holdings h
            LEFT JOIN LATERAL (
                SELECT close FROM daily_prices dp WHERE dp.symbol = h.symbol ORDER BY dp.date DESC LIMIT 1
            ) lp ON true
            WHERE h.user_id = %s
            ORDER BY h.created_at
            """,
            (DEFAULT_USER_ID,),
        ).fetchall()

    holdings = [_holding_with_returns(r) for r in rows]
    total_cost = sum(h["cost_basis"] for h in holdings)
    total_value = sum(h["current_value"] for h in holdings if h["current_value"] is not None)
    total_gain = total_value - total_cost if holdings else 0.0
    total_gain_pct = (total_gain / total_cost * 100) if total_cost else None

    return {
        "holdings": holdings,
        "total_cost_basis": total_cost,
        "total_current_value": total_value,
        "total_gain": total_gain,
        "total_gain_pct": total_gain_pct,
    }


@router.post("/portfolio", status_code=201)
def add_holding(holding: HoldingIn):
    with pool.connection() as conn:
        _require_known_symbol(conn, holding.symbol)
        row = conn.execute(
            """
            INSERT INTO holdings (user_id, symbol, quantity, avg_cost, buy_date, account, note)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING id
            """,
            (DEFAULT_USER_ID, holding.symbol, holding.quantity, holding.avg_cost,
             holding.buy_date, holding.account, holding.note),
        ).fetchone()
        conn.commit()
    return {"id": str(row[0])}


@router.put("/portfolio/{holding_id}")
def update_holding(holding_id: uuid.UUID, holding: HoldingIn):
    with pool.connection() as conn:
        _require_known_symbol(conn, holding.symbol)
        result = conn.execute(
            """
            UPDATE holdings SET symbol = %s, quantity = %s, avg_cost = %s, buy_date = %s, account = %s, note = %s
            WHERE id = %s AND user_id = %s
            """,
            (holding.symbol, holding.quantity, holding.avg_cost, holding.buy_date,
             holding.account, holding.note, str(holding_id), DEFAULT_USER_ID),
        )
        conn.commit()
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="holding not found")
    return {"status": "updated"}


@router.delete("/portfolio/{holding_id}", status_code=204)
def delete_holding(holding_id: uuid.UUID):
    with pool.connection() as conn:
        result = conn.execute(
            "DELETE FROM holdings WHERE id = %s AND user_id = %s", (str(holding_id), DEFAULT_USER_ID)
        )
        conn.commit()
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="holding not found")
