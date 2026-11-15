import datetime as dt
import sys
import time

from pipeline.breeze_client import SessionExpired, check_response, get_client, is_session_error
from pipeline.db import connect
from pipeline.jobs.fetch_prices import upsert_rows
from pipeline.run import SKIPPED_EXIT

PACE_SECONDS = 0.85


def day_bar(bars: list[dict], day: dt.date) -> dict | None:
    prefix = day.isoformat()
    today = sorted((b for b in bars if b["datetime"].startswith(prefix)), key=lambda b: b["datetime"])
    if not today:
        return None
    return {
        "datetime": today[0]["datetime"],
        "open": float(today[0]["open"]),
        "high": max(float(b["high"]) for b in today),
        "low": min(float(b["low"]) for b in today),
        "close": float(today[-1]["close"]),
        "volume": sum(int(float(b.get("volume") or 0)) for b in today),
    }


def _minute_bars(client, breeze_code: str, exchange: str, day: dt.date) -> list[dict]:
    kwargs = dict(
        interval="1minute",
        from_date=f"{day.isoformat()}T00:00:00.000Z",
        to_date=f"{day.isoformat()}T23:59:59.000Z",
        stock_code=breeze_code,
        exchange_code=exchange,
        product_type="cash",
    )
    if exchange == "BSE":
        return check_response(client.get_historical_data_v2(**kwargs))
    return check_response(client.get_historical_data(**kwargs))


def run(day: dt.date) -> tuple[list[str], int]:
    client = get_client()
    failures = []
    with connect() as conn:
        held = conn.execute(
            """
            SELECT c.symbol, c.breeze_code, c.exchange FROM companies c
            JOIN stock_transactions t ON t.symbol = c.symbol
            WHERE c.is_active AND c.breeze_code IS NOT NULL
            GROUP BY c.symbol, c.breeze_code, c.exchange
            HAVING sum(CASE t.kind WHEN 'buy' THEN t.quantity ELSE -t.quantity END) > 0
            ORDER BY c.symbol
            """
        ).fetchall()
        updated = 0
        for symbol, breeze_code, exchange in held:
            try:
                bar = day_bar(_minute_bars(client, breeze_code, exchange, day), day)
                if bar:
                    upsert_rows(conn, symbol, [bar])
                    updated += 1
            except SessionExpired:
                raise
            except Exception as e:
                conn.rollback()
                if is_session_error(e):
                    raise SessionExpired(str(e)) from e
                failures.append(symbol)
                print(f"{symbol}: FAILED - {e}")
            time.sleep(PACE_SECONDS)
    print(f"live prices: {updated} of {len(held)} held stocks updated for {day}")
    return failures, updated


def main() -> None:
    day = dt.date.fromisoformat(sys.argv[1]) if len(sys.argv) > 1 else dt.date.today()
    try:
        failures, updated = run(day)
    except SessionExpired as e:
        print(f"skipped: Breeze session not valid ({e}) - log in to ICICI from the app")
        sys.exit(SKIPPED_EXIT)
    if updated == 0 and not failures:
        print(f"skipped: no trades on {day} (market closed)")
        sys.exit(SKIPPED_EXIT)
    if failures:
        sys.exit(1)


if __name__ == "__main__":
    main()
