import datetime as dt
import uuid
from typing import Literal

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from db import pool
from jobs import spawn_job
from services.mf import mf_positions

router = APIRouter()

DEFAULT_USER_ID = "00000000-0000-0000-0000-000000000001"
MF_SECTOR = "Mutual funds"
SPARK_POINTS = 30
MIN_HISTORY_ROWS = 30

TX_SQL = """
SELECT id, code, broker, kind, units, amount, date, note, created_at
FROM mf_transactions WHERE user_id = %s ORDER BY date NULLS FIRST, created_at
"""


def scheme_label(s: dict) -> str:
    return f"{s['name']} ({s['plan']})" if s.get("plan") else s["name"]


def _positions_or_400(transactions: list[dict]) -> dict:
    try:
        return mf_positions(transactions)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


def mf_rows(conn) -> list[dict]:
    positions = mf_positions(conn.execute(TX_SQL, (DEFAULT_USER_ID,)).fetchall())
    if not positions:
        return []
    codes = sorted({code for code, _ in positions})
    schemes = {s["code"]: s for s in conn.execute("SELECT * FROM mf_schemes WHERE code = ANY(%s)", (codes,))}
    recent: dict[int, list[tuple[dt.date, float]]] = {}
    for r in conn.execute(
        """
        SELECT code, date, nav::float AS nav FROM (
            SELECT code, date, nav, row_number() OVER (PARTITION BY code ORDER BY date DESC) AS rn
            FROM mf_nav WHERE code = ANY(%s)
        ) t WHERE rn <= %s ORDER BY code, date
        """,
        (codes, SPARK_POINTS),
    ):
        recent.setdefault(r["code"], []).append((r["date"], r["nav"]))

    rows = []
    for (code, broker), pos in sorted(positions.items()):
        s = schemes[code]
        navs = recent.get(code, [])
        rows.append({
            "id": f"mf:{code}:{broker}",
            "symbol": str(code),
            "name": scheme_label(s),
            "sector": MF_SECTOR,
            "kind": "mf",
            "asset_class": s["asset_class"],
            "exchange": None,
            "category": s["category"],
            "quantity": pos["units"],
            "invested": pos["invested"],
            "realized": pos["realized"],
            "broker": broker,
            "source": "manual",
            "buy_date": None,
            "note": None,
            "close": navs[-1][1] if navs else (float(s["nav"]) if s["nav"] is not None else None),
            "prev_close": navs[-2][1] if len(navs) > 1 else None,
            "price_date": navs[-1][0] if navs else s["nav_date"],
            "spark": [n for _, n in navs],
        })
    return rows


def mf_history(conn, since: dt.date) -> dict[dt.date, float]:
    positions = mf_positions(conn.execute(TX_SQL, (DEFAULT_USER_ID,)).fetchall())
    units: dict[int, float] = {}
    for (code, _), pos in positions.items():
        units[code] = units.get(code, 0.0) + pos["units"]
    if not units:
        return {}
    points = conn.execute(
        "SELECT code, date, nav::float AS nav FROM mf_nav WHERE code = ANY(%s) AND date >= %s ORDER BY date",
        (list(units), since - dt.timedelta(days=10)),
    ).fetchall()
    latest: dict[int, float] = {}
    series: dict[dt.date, float] = {}
    for p in points:
        latest[p["code"]] = p["nav"]
        if p["date"] >= since and len(latest) == len(units):
            series[p["date"]] = sum(units[c] * nav for c, nav in latest.items())
    return series


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
    return {**scheme, "label": scheme_label(scheme), "navs": navs, "transactions": transactions}


class TransactionIn(BaseModel):
    code: int
    broker: str = Field(min_length=1, max_length=40)
    kind: Literal["buy", "sell"]
    units: float = Field(gt=0)
    amount: float = Field(ge=0)
    date: dt.date | None = None
    note: str | None = Field(None, max_length=500)


def _check_and_backfill(conn, code: int) -> None:
    _positions_or_400(conn.execute(TX_SQL, (DEFAULT_USER_ID,)).fetchall())
    if conn.execute("SELECT count(*) AS n FROM mf_nav WHERE code = %s", (code,)).fetchone()["n"] < MIN_HISTORY_ROWS:
        spawn_job("refresh_mf", ["--codes", str(code)], trigger="auto")


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
        _positions_or_400(conn.execute(TX_SQL, (DEFAULT_USER_ID,)).fetchall())
