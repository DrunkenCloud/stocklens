"""Fetch daily OHLCV from Breeze into daily_prices. Incremental by default.

Usage:
    python -m pipeline.jobs.fetch_prices              # incremental, all active companies
    python -m pipeline.jobs.fetch_prices --backfill    # force full history for all active companies

Per-symbol isolation: one symbol failing (bad breeze_code, transient API error
after retries) is logged and skipped, never aborts the run (03_PIPELINE.md).
"""
import argparse
import datetime as dt
import os
import sys
import time

import psycopg

from pipeline.breeze_client import get_client

BACKFILL_START = dt.date(2015, 1, 1)  # matches the ~10yr history Breeze documents
RETRIES = 3
RETRY_BACKOFF_SECONDS = 5


def incremental_from_date(last_date: dt.date | None, today: dt.date, backfill: bool) -> dt.date:
    """Pure: decide the from-date for one symbol given its last stored date."""
    if backfill or last_date is None:
        return BACKFILL_START
    return last_date + dt.timedelta(days=1)


def normalize_row(raw: dict) -> tuple:
    """Pure: one Breeze historical-data record -> (date, open, high, low, close, volume).

    Field names and types (strings, e.g. "1291.9") confirmed against a live
    get_historical_data response.
    """
    date_str = raw["datetime"][:10]

    def num(key):
        v = raw.get(key)
        return float(v) if v is not None else None

    volume = raw.get("volume")
    return (
        dt.date.fromisoformat(date_str),
        num("open"),
        num("high"),
        num("low"),
        float(raw["close"]),
        int(volume) if volume is not None else None,
    )


def fetch_symbol(client, breeze_code: str, from_date: dt.date, to_date: dt.date) -> list[dict]:
    last_err = None
    for attempt in range(1, RETRIES + 1):
        try:
            resp = client.get_historical_data(
                interval="1day",
                from_date=f"{from_date.isoformat()}T00:00:00.000Z",
                to_date=f"{to_date.isoformat()}T00:00:00.000Z",
                stock_code=breeze_code,
                exchange_code="NSE",
                product_type="cash",
            )
            return resp.get("Success") or []
        except Exception as e:  # noqa: BLE001 - retried then surfaced to caller for per-symbol isolation
            last_err = e
            time.sleep(RETRY_BACKOFF_SECONDS * attempt)
    raise RuntimeError(f"failed after {RETRIES} attempts: {last_err}") from last_err


def upsert_rows(conn, symbol: str, rows: list[dict]) -> None:
    parsed = [normalize_row(r) for r in rows]
    with conn.cursor() as cur:
        cur.executemany(
            """
            INSERT INTO daily_prices (symbol, date, open, high, low, close, volume)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (symbol, date) DO UPDATE SET
                open = EXCLUDED.open, high = EXCLUDED.high, low = EXCLUDED.low,
                close = EXCLUDED.close, volume = EXCLUDED.volume
            """,
            [(symbol, *p) for p in parsed],
        )
    conn.commit()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--backfill", action="store_true", help="fetch full history instead of incremental")
    args = parser.parse_args()

    client = get_client()
    conn = psycopg.connect(os.environ["DATABASE_URL"])
    today = dt.date.today()
    failures = []

    with conn.cursor() as cur:
        cur.execute("SELECT symbol, breeze_code FROM companies WHERE is_active")
        companies = cur.fetchall()

    for symbol, breeze_code in companies:
        if not breeze_code:
            # Breeze's stock_code often differs from the NSE ticker (confirmed live -
            # e.g. M&M -> MAHMAH). Run map_breeze_codes.py first to populate this.
            failures.append(symbol)
            print(f"{symbol}: SKIPPED - no breeze_code set, run: python -m pipeline.jobs.map_breeze_codes")
            continue

        with conn.cursor() as cur:
            cur.execute("SELECT max(date) FROM daily_prices WHERE symbol = %s", (symbol,))
            (last_date,) = cur.fetchone()

        from_date = incremental_from_date(last_date, today, args.backfill)
        if from_date > today:
            continue

        try:
            rows = fetch_symbol(client, breeze_code, from_date, today)
            upsert_rows(conn, symbol, rows)
            print(f"{symbol}: {len(rows)} rows ({from_date} -> {today})")
        except Exception as e:
            failures.append(symbol)
            print(f"{symbol}: FAILED - {e}")

    conn.close()

    if failures:
        print(f"\n{len(failures)} symbol(s) failed: {failures}")
        sys.exit(1)


if __name__ == "__main__":
    main()
