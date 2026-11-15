import datetime as dt
import uuid
from typing import Literal

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from db import pool
from jobs import spawn_job
from holdings import DEFAULT_USER_ID, load_ledger, scheme_label
from services.exposure import ASSET_SECTOR, holding_asset
from services.sectors import clean
from services.ledger import positions

router = APIRouter()

MIN_HISTORY_ROWS = 30

def _validate_ledger(conn) -> None:
    try:
        positions(load_ledger(conn, "mf"))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/mf/search")
def search(q: str = Query(..., min_length=2, max_length=80), limit: int = Query(20, le=50)):
    terms = [t for t in q.split() if t]
    where = " AND ".join(["s.name ILIKE %s"] * len(terms))
    with pool.connection() as conn:
        return conn.execute(
            f"""
            SELECT s.code, s.name, s.amc, s.category, s.plan, s.option, s.nav, s.nav_date, s.asset_class,
                   EXISTS (SELECT 1 FROM mf_transactions t WHERE t.code = s.code) AS held
            FROM mf_schemes s
            WHERE {where}
            ORDER BY held DESC, (s.option = 'Growth') DESC NULLS LAST, (s.plan = 'Direct') DESC NULLS LAST, length(s.name), s.name
            LIMIT %s
            """,
            [*(f"%{t}%" for t in terms), limit],
        ).fetchall()


@router.get("/mf/{code}")
def get_fund(code: int):
    with pool.connection() as conn:
        scheme = conn.execute("SELECT * FROM mf_schemes WHERE code = %s", (code,)).fetchone()
        if scheme is None:
            raise HTTPException(status_code=404, detail="Unknown fund")
        navs = conn.execute("SELECT date, nav::float AS nav FROM mf_nav WHERE code = %s ORDER BY date", (code,)).fetchall()
        transactions = conn.execute(
            "SELECT id, broker, kind, units, amount, date, note FROM mf_transactions WHERE user_id = %s AND code = %s "
            "ORDER BY date NULLS FIRST, created_at",
            (DEFAULT_USER_ID, code),
        ).fetchall()
        holdings = conn.execute(
            """
            SELECT name, isin, holding_type, industry, pct_nav::float AS pct_nav FROM fund_portfolio_holdings
            WHERE portfolio_id = %s ORDER BY pct_nav DESC
            """,
            (scheme["portfolio_id"],),
        ).fetchall() if scheme["portfolio_id"] else []
    sectors: dict[str, float] = {}
    for h in holdings:
        asset = holding_asset(h["holding_type"], h["name"], h["isin"])
        key = (clean(h["industry"]) or "Other") if asset == "equity" else ASSET_SECTOR.get(asset, "Other")
        sectors[key] = sectors.get(key, 0.0) + h["pct_nav"]
    return {
        **scheme, "label": scheme_label(scheme), "navs": navs, "transactions": transactions,
        "top_holdings": holdings[:15], "holdings_count": len(holdings),
        "sectors": [{"sector": k, "pct": v} for k, v in sorted(sectors.items(), key=lambda kv: -kv[1])],
    }


class TransactionIn(BaseModel):
    code: int
    broker: str = Field(min_length=1, max_length=40)
    kind: Literal["buy", "sell"]
    units: float = Field(gt=0)
    amount: float = Field(ge=0)
    date: dt.date | None = None
    note: str | None = Field(None, max_length=500)


def _check_and_backfill(conn, code: int) -> None:
    _validate_ledger(conn)
    if conn.execute("SELECT count(*) AS n FROM mf_nav WHERE code = %s", (code,)).fetchone()["n"] < MIN_HISTORY_ROWS:
        spawn_job("refresh_mf", ["--codes", str(code)], trigger="auto")
    if conn.execute("SELECT portfolio_id FROM mf_schemes WHERE code = %s", (code,)).fetchone()["portfolio_id"] is None:
        spawn_job("refresh_fund_portfolios", ["--codes", str(code)], trigger="auto")


@router.post("/mf/transactions", status_code=201)
def add_transaction(tx: TransactionIn):
    with pool.connection() as conn:
        if not conn.execute("SELECT 1 FROM mf_schemes WHERE code = %s", (tx.code,)).fetchone():
            raise HTTPException(status_code=404, detail="Unknown fund")
        row = conn.execute(
            """
            INSERT INTO mf_transactions (user_id, code, broker, kind, units, amount, date, note)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s) RETURNING id
            """,
            (DEFAULT_USER_ID, tx.code, tx.broker.strip(), tx.kind, tx.units, tx.amount, tx.date, tx.note),
        ).fetchone()
        _check_and_backfill(conn, tx.code)
    return {"id": str(row["id"])}


@router.put("/mf/transactions/{tx_id}")
def update_transaction(tx_id: uuid.UUID, tx: TransactionIn):
    with pool.connection() as conn:
        result = conn.execute(
            """
            UPDATE mf_transactions SET code = %s, broker = %s, kind = %s, units = %s, amount = %s, date = %s, note = %s
            WHERE id = %s AND user_id = %s
            """,
            (tx.code, tx.broker.strip(), tx.kind, tx.units, tx.amount, tx.date, tx.note, str(tx_id), DEFAULT_USER_ID),
        )
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Entry not found")
        _check_and_backfill(conn, tx.code)
    return {"status": "updated"}


@router.delete("/mf/transactions/{tx_id}", status_code=204)
def delete_transaction(tx_id: uuid.UUID):
    with pool.connection() as conn:
        result = conn.execute("DELETE FROM mf_transactions WHERE id = %s AND user_id = %s", (str(tx_id), DEFAULT_USER_ID))
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Entry not found")
        _validate_ledger(conn)
