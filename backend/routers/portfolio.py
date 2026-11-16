import datetime as dt
import uuid
from typing import Literal

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field, model_validator

from db import pool
from holdings import DEFAULT_USER_ID, asset_info, exposure_breakdown, exposure_from_rows, growth, holding_rows, load_ledger, price_history
from jobs import spawn_job
from routers.securities import ensure_tracked
from services.benchmark import index_equivalent, period_changes
from services.insights import drawdown, month_movers
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


@router.get("/portfolio/exposure/breakdown")
def get_exposure_breakdown(key: str = Query(..., pattern="^(asset|sector|kind):.{1,80}$"), scope: str = Scope):
    with pool.connection() as conn:
        rows, _ = holding_rows(conn, scope)
        return exposure_breakdown(conn, rows, key)


@router.get("/portfolio/growth")
def get_growth(days: int = Query(365, ge=7, le=365 * 30), scope: str = Scope):
    with pool.connection() as conn:
        return growth(conn, scope, dt.date.today() - dt.timedelta(days=days))


@router.get("/portfolio/benchmarks")
def get_benchmarks():
    today = dt.date.today()
    with pool.connection() as conn:
        rows, overall = holding_rows(conn, "all")
        txs = load_ledger(conn, "all")
        indices = conn.execute("SELECT symbol, name FROM market_indices ORDER BY position").fetchall()
        series: dict[str, list] = {}
        for r in conn.execute("SELECT symbol, date, close::float AS close FROM index_prices ORDER BY symbol, date"):
            series.setdefault(r["symbol"], []).append((r["date"], r["close"]))

    undated = {t["key"] for t in txs if t["date"] is None}
    flows = [(t["date"], -float(t["amount"]) if t["kind"] == "buy" else float(t["amount"])) for t in txs if t["key"] not in undated]
    out = []
    for idx in indices:
        s = series.get(idx["symbol"], [])
        out.append({
            "symbol": idx["symbol"], "name": idx["name"],
            "close": s[-1][1] if s else None, "date": s[-1][0] if s else None,
            **period_changes(s), **index_equivalent(flows, s, today),
        })
    return {
        "portfolio": {
            "xirr": overall["xirr"],
            "coverage_pct": overall["xirr_coverage_pct"],
            "invested": -sum(a for _, a in flows),
            "value": sum(r["quantity"] * r["close"] for r in rows if r["dated"] and r["close"] is not None),
            "first_date": min((d for d, _ in flows), default=None),
        },
        "indices": out,
    }


MOVERS = 5


@router.get("/portfolio/insights")
def get_insights():
    today = dt.date.today()
    month_start = today.replace(day=1)
    with pool.connection() as conn:
        txs = load_ledger(conn, "all")
        keys = {t["key"] for t in txs}
        movers = month_movers(txs, price_history(conn, keys, month_start - dt.timedelta(days=15)), today)
        info = asset_info(conn, {m["key"] for m in movers})
        series = growth(conn, "all", dt.date.min)["series"]

    undated = {t["key"] for t in txs if t["date"] is None}
    flows = [(t["date"], float(t["amount"]) * (1 if t["kind"] == "buy" else -1)) for t in txs if t["key"] not in undated]
    rows = [{**info[m["key"]], "change": m["change"]} for m in movers]
    return {
        "month_start": month_start,
        "movers": {
            "up": sorted((r for r in rows if r["change"] > 0), key=lambda r: -r["change"])[:MOVERS],
            "down": sorted((r for r in rows if r["change"] < 0), key=lambda r: r["change"])[:MOVERS],
        },
        "drawdown": drawdown(series, flows),
        "excluded_count": len(undated),
    }


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
