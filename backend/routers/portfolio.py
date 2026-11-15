import datetime as dt
import uuid
from typing import Literal

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field, model_validator

from db import pool
from holdings import DEFAULT_USER_ID, exposure_from_rows, growth, holding_rows, load_ledger
from jobs import spawn_job
from routers.securities import ensure_tracked
from services.ledger import positions
from services.portfolio import summarize

router = APIRouter()

Scope = Query("all", pattern="^(all|stocks|mf)$")


@router.get("/portfolio")
def get_portfolio(scope: str = Scope):
    with pool.connection() as conn:
        rows, overall = holding_rows(conn, scope)
        exposure = exposure_from_rows(conn, rows)
    summary = summarize(rows)
    summary["totals"].update(overall)
    summary["by_sector"] = exposure["sectors"]
    summary["by_asset_class"] = [{"asset_class": a["asset"], "value": a["value"], "weight_pct": a["weight_pct"]} for a in exposure["assets"]]
    return summary


@router.get("/portfolio/exposure")
def get_exposure(scope: str = Scope):
    with pool.connection() as conn:
        rows, _ = holding_rows(conn, scope)
        return exposure_from_rows(conn, rows)


@router.get("/portfolio/growth")
def get_growth(days: int = Query(365, ge=7, le=365 * 30), scope: str = Scope):
    with pool.connection() as conn:
        return growth(conn, scope, dt.date.today() - dt.timedelta(days=days))


class StockTxIn(BaseModel):
    symbol: str | None = None
    isin: str | None = None
    broker: str = Field(min_length=1, max_length=40)
    kind: Literal["buy", "sell"]
    quantity: float = Field(gt=0)
    price: float = Field(ge=0)
    date: dt.date | None = None
    note: str | None = Field(None, max_length=500)

    @model_validator(mode="after")
    def _needs_stock(self):
        if not (self.symbol or self.isin):
            raise ValueError("symbol or isin required")
        return self


def _validate_ledger(conn) -> None:
    try:
        positions(load_ledger(conn, "stocks"))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


def _etf_without_portfolio(conn, symbol: str) -> int | None:
    row = conn.execute(
        """
        SELECT s.code FROM companies c JOIN mf_schemes s ON s.isin = c.isin
        WHERE c.symbol = %s AND c.kind = 'etf' AND s.portfolio_id IS NULL
        """,
        (symbol,),
    ).fetchone()
    return row["code"] if row else None


@router.get("/stock-transactions")
def list_stock_transactions(symbol: str):
    with pool.connection() as conn:
        return conn.execute(
            """
            SELECT id, symbol, broker, kind, quantity, price, quantity * price AS amount, date, note
            FROM stock_transactions WHERE user_id = %s AND symbol = %s ORDER BY date NULLS FIRST, created_at
            """,
            (DEFAULT_USER_ID, symbol.upper()),
        ).fetchall()


@router.post("/stock-transactions", status_code=201)
def add_stock_transaction(tx: StockTxIn):
    with pool.connection() as conn:
        symbol, newly_tracked = ensure_tracked(conn, isin=tx.isin, symbol=tx.symbol)
        row = conn.execute(
            """
            INSERT INTO stock_transactions (user_id, symbol, broker, kind, quantity, price, date, note)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s) RETURNING id
            """,
            (DEFAULT_USER_ID, symbol, tx.broker.strip(), tx.kind, tx.quantity, tx.price, tx.date, tx.note),
        ).fetchone()
        _validate_ledger(conn)
        etf_code = _etf_without_portfolio(conn, symbol)
    if newly_tracked:
        spawn_job("onboard", ["--symbols", symbol], trigger="auto")
    if etf_code is not None:
        spawn_job("refresh_fund_portfolios", ["--codes", str(etf_code)], trigger="auto")
    return {"id": str(row["id"]), "symbol": symbol, "newly_tracked": newly_tracked}


@router.put("/stock-transactions/{tx_id}")
def update_stock_transaction(tx_id: uuid.UUID, tx: StockTxIn):
    with pool.connection() as conn:
        symbol, newly_tracked = ensure_tracked(conn, isin=tx.isin, symbol=tx.symbol)
        result = conn.execute(
            """
            UPDATE stock_transactions SET symbol = %s, broker = %s, kind = %s, quantity = %s, price = %s, date = %s, note = %s
            WHERE id = %s AND user_id = %s
            """,
            (symbol, tx.broker.strip(), tx.kind, tx.quantity, tx.price, tx.date, tx.note, str(tx_id), DEFAULT_USER_ID),
        )
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Entry not found")
        _validate_ledger(conn)
    if newly_tracked:
        spawn_job("onboard", ["--symbols", symbol], trigger="auto")
    return {"status": "updated"}


@router.delete("/stock-transactions/{tx_id}", status_code=204)
def delete_stock_transaction(tx_id: uuid.UUID):
    with pool.connection() as conn:
        result = conn.execute("DELETE FROM stock_transactions WHERE id = %s AND user_id = %s", (str(tx_id), DEFAULT_USER_ID))
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Entry not found")
        _validate_ledger(conn)
