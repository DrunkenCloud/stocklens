"""Fetch fundamentals (Yahoo Finance) per active company, snapshot-append into
`fundamentals` (one row per symbol per day, so history accumulates). Yahoo is
the fragile source - per-symbol isolation so one bad/delisted symbol doesn't
abort the run. No Breeze session needed.

Usage: python -m pipeline.jobs.fetch_fundamentals [--symbols ITC,TCS | --missing]
  --missing: only companies with no fundamentals snapshot yet
"""
import argparse
import datetime as dt
import sys

from psycopg.types.json import Json

from pipeline.db import connect
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
        # Stocks tracked via search/ICICI sync arrive without a sector; Yahoo's fills the gap
        # (hand-seeded sectors are kept).
        cur.execute(
            "UPDATE companies SET sector = %s WHERE symbol = %s AND sector IS NULL",
            (data["raw"].get("sector"), symbol),
        )
    conn.commit()


def run(symbols: list[str] | None = None, missing_only: bool = False) -> list[str]:
    """Snapshot fundamentals for active companies (or just `symbols`). Returns failed symbols."""
    today = dt.date.today()
    failures = []

    with connect() as conn:
        rows = conn.execute(
            """
            SELECT c.symbol FROM companies c
            WHERE c.is_active
              AND (%(symbols)s::text[] IS NULL OR c.symbol = ANY(%(symbols)s::text[]))
              AND (NOT %(missing)s OR NOT EXISTS (SELECT 1 FROM fundamentals f WHERE f.symbol = c.symbol))
            ORDER BY c.symbol
            """,
            {"symbols": symbols, "missing": missing_only},
        ).fetchall()

        for (symbol,) in rows:
            try:
                data = fetch_fundamentals(symbol)
                upsert_snapshot(conn, symbol, today, data)
                print(f"{symbol}: pe={data['pe']} pb={data['pb']} roe={data['roe']}")
            except Exception as e:
                conn.rollback()
                failures.append(symbol)
                print(f"{symbol}: FAILED - {e}")

    if failures:
        print(f"{len(failures)} symbol(s) failed: {failures}")
    return failures


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--symbols", help="comma-separated; default all active companies")
    parser.add_argument("--missing", action="store_true", help="only companies with no snapshot yet")
    args = parser.parse_args()

    failures = run(args.symbols.split(",") if args.symbols else None, missing_only=args.missing)
    if failures:
        sys.exit(1)
    print("fundamentals up to date")


if __name__ == "__main__":
    main()
