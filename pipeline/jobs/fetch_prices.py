import argparse
import datetime as dt
import sys
import time

from pipeline.breeze_client import SessionExpired, check_response, get_client, is_session_error
from pipeline.db import connect
from pipeline.run import SKIPPED_EXIT
from pipeline.splits import detect_splits

BACKFILL_START = dt.date(2015, 1, 1)
RETRIES = 3
RETRY_BACKOFF_SECONDS = 5


def incremental_from_date(last_date: dt.date | None, today: dt.date, backfill: bool) -> dt.date:
    if backfill or last_date is None:
        return BACKFILL_START
    return last_date


def normalize_row(raw: dict) -> tuple:
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


BSE_WINDOW_DAYS = 900


def date_windows(start: dt.date, end: dt.date, days: int) -> list[tuple[dt.date, dt.date]]:
    windows = []
    while start <= end:
        stop = min(end, start + dt.timedelta(days=days - 1))
        windows.append((start, stop))
        start = stop + dt.timedelta(days=1)
    return windows


def _call(client, breeze_code: str, from_date: dt.date, to_date: dt.date, exchange: str) -> list[dict]:
    kwargs = dict(
        interval="1day",
        from_date=f"{from_date.isoformat()}T00:00:00.000Z",
        to_date=f"{to_date.isoformat()}T00:00:00.000Z",
        stock_code=breeze_code,
        exchange_code=exchange,
        product_type="cash",
    )
    if exchange == "BSE":
        return check_response(client.get_historical_data_v2(**kwargs))
    return check_response(client.get_historical_data(**kwargs))


def fetch_symbol(client, breeze_code: str, from_date: dt.date, to_date: dt.date, exchange: str = "NSE") -> list[dict]:
    windows = date_windows(from_date, to_date, BSE_WINDOW_DAYS) if exchange == "BSE" else [(from_date, to_date)]
    rows = []
    for start, stop in windows:
        last_err = None
        for attempt in range(1, RETRIES + 1):
            try:
                rows += _call(client, breeze_code, start, stop, exchange)
                break
            except SessionExpired:
                raise
            except Exception as e:
                last_err = e
                time.sleep(RETRY_BACKOFF_SECONDS * attempt)
        else:
            raise RuntimeError(f"failed after {RETRIES} attempts: {last_err}") from last_err
    return rows


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


def adjust_splits(conn, symbols: list[str]) -> None:
    for symbol in symbols:
        closes = [(d, float(c)) for d, c in conn.execute(
            "SELECT date, close FROM daily_prices WHERE symbol = %s ORDER BY date", (symbol,)
        )]
        for day, factor in detect_splits(closes):
            conn.execute(
                """
                UPDATE daily_prices SET open = open / %(f)s, high = high / %(f)s, low = low / %(f)s,
                    close = close / %(f)s, volume = volume * %(f)s
                WHERE symbol = %(s)s AND date < %(d)s
                """,
                {"f": factor, "s": symbol, "d": day},
            )
            print(f"{symbol}: adjusted prices before {day} for a 1:{factor} split/bonus")
        conn.commit()


def run(symbols: list[str] | None = None, backfill: bool = False) -> list[str]:
    client = get_client()
    today = dt.date.today()
    failures = []

    with connect() as conn:
        companies = conn.execute(
            """
            SELECT c.symbol, c.breeze_code, c.exchange, max(p.date)
            FROM companies c LEFT JOIN daily_prices p ON p.symbol = c.symbol
            WHERE c.is_active AND (%(symbols)s::text[] IS NULL OR c.symbol = ANY(%(symbols)s::text[]))
            GROUP BY c.symbol, c.breeze_code, c.exchange ORDER BY c.symbol
            """,
            {"symbols": symbols},
        ).fetchall()

        for symbol, breeze_code, exchange, last_date in companies:
            if not breeze_code:
                failures.append(symbol)
                print(f"{symbol}: SKIPPED - no breeze_code (not in ICICI's security master?)")
                continue
            from_date = incremental_from_date(last_date, today, backfill)
            if from_date > today:
                continue
            try:
                rows = fetch_symbol(client, breeze_code, from_date, today, exchange)
                upsert_rows(conn, symbol, rows)
                print(f"{symbol}: {len(rows)} rows ({from_date} -> {today})")
            except SessionExpired:
                raise
            except Exception as e:
                conn.rollback()
                if is_session_error(e):
                    raise SessionExpired(str(e)) from e
                failures.append(symbol)
                print(f"{symbol}: FAILED - {e}")

        adjust_splits(conn, [c[0] for c in companies])

    if failures:
        print(f"{len(failures)} symbol(s) failed: {failures}")
    return failures


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--backfill", action="store_true", help="fetch full history instead of incremental")
    parser.add_argument("--symbols", help="comma-separated; default all active companies")
    args = parser.parse_args()

    try:
        failures = run(args.symbols.split(",") if args.symbols else None, backfill=args.backfill)
    except SessionExpired as e:
        print(f"skipped: Breeze session not valid ({e}) - log in to ICICI from the app")
        sys.exit(SKIPPED_EXIT)
    if failures:
        sys.exit(1)
    print("prices up to date")


if __name__ == "__main__":
    main()
