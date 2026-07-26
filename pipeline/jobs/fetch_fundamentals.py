"""Fetch fundamentals (Yahoo Finance) per active company, snapshot-append into
`fundamentals`. This is the fragile job (02_DATA_SOURCES.md /
03_PIPELINE.md) - per-symbol isolation so one bad/delisted symbol doesn't
abort the run.

Usage: python -m pipeline.jobs.fetch_fundamentals
"""
import datetime as dt
import os
import sys

import psycopg
from psycopg.types.json import Json

from pipeline.fundamentals_source import fetch_fundamentals

COLUMNS = [
    "pe", "pb", "roe", "op_margin", "rev_ttm", "rev_growth_1y",
    "rev_cagr_3y", "debt_to_equity", "dividend_yield", "market_cap",
]


def upsert_snapshot(conn, symbol: str, snapshot_date: dt.date, data: dict) -> None:
    with conn.cursor() as cur:
        cur.execute(
            f"""
            INSERT INTO fundamentals (symbol, snapshot_date, {", ".join(COLUMNS)}, raw)
            VALUES (%s, %s, {", ".join(["%s"] * len(COLUMNS))}, %s)
            ON CONFLICT (symbol, snapshot_date) DO UPDATE SET
                {", ".join(f"{c} = EXCLUDED.{c}" for c in COLUMNS)}, raw = EXCLUDED.raw
            """,
            [symbol, snapshot_date, *(data[c] for c in COLUMNS), Json(data["raw"])],
        )
    conn.commit()


def main() -> None:
    conn = psycopg.connect(os.environ["DATABASE_URL"])
    today = dt.date.today()
    failures = []

    with conn.cursor() as cur:
        cur.execute("SELECT symbol FROM companies WHERE is_active ORDER BY symbol")
        symbols = [r[0] for r in cur.fetchall()]

    for symbol in symbols:
        try:
            data = fetch_fundamentals(symbol)
            upsert_snapshot(conn, symbol, today, data)
            print(f"{symbol}: pe={data['pe']} pb={data['pb']} roe={data['roe']}")
        except Exception as e:
            failures.append(symbol)
            print(f"{symbol}: FAILED - {e}")

    conn.close()
    if failures:
        print(f"\n{len(failures)} symbol(s) failed: {failures}")
        sys.exit(1)


if __name__ == "__main__":
    main()
