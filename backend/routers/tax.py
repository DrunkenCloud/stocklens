import datetime as dt

from fastapi import APIRouter

from db import pool
from holdings import asset_info, holding_rows, load_ledger
from services.tax import fifo, tax_class, tax_report

router = APIRouter()


@router.get("/tax")
def get_tax():
    with pool.connection() as conn:
        txs = load_ledger(conn, "all")
        rows, _ = holding_rows(conn, "all")
        info = asset_info(conn, {t["key"] for t in txs})

    prices = {r["id"]: r["close"] for r in rows}
    meta = {
        key: {**i, "tax_class": tax_class(i["kind"], i["asset_class"], i["category"]),
              "price": prices.get(f"{key[0]}:{key[1]}:{key[2]}")}
        for key, i in info.items()
    }
    lots, realised = fifo(txs)
    return tax_report(lots, realised, meta, dt.date.today())
