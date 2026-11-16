import datetime as dt
import sys
import time

from pipeline.bars import day_bar
from pipeline.breeze_client import SessionExpired, check_response, get_client, is_session_error
from pipeline.fundamentals_source import yahoo_tickers
from pipeline.indices import live_indices
from pipeline.db import connect
from pipeline.jobs.fetch_prices import upsert_rows
from pipeline.run import SKIPPED_EXIT
from pipeline.yahoo_prices import minute_bars

PACE_SECONDS = 0.85


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


HELD_SQL = """
SELECT c.symbol, c.breeze_code, c.exchange FROM companies c
JOIN stock_transactions t ON t.symbol = c.symbol
WHERE c.is_active
GROUP BY c.symbol, c.breeze_code, c.exchange
HAVING sum(CASE t.kind WHEN 'buy' THEN t.quantity ELSE -t.quantity END) > 0
ORDER BY c.symbol
"""


def _breeze(conn, client, held, day: dt.date) -> tuple[list[str], int, list]:
    failures, updated, missing = [], 0, []
    for row in held:
        symbol, breeze_code, exchange = row
        if not breeze_code:
            missing.append(row)
            continue
        try:
            bar = day_bar(_minute_bars(client, breeze_code, exchange, day), day)
            if bar:
                upsert_rows(conn, symbol, [bar])
                updated += 1
            else:
                missing.append(row)
        except SessionExpired:
            raise
        except Exception as e:
            conn.rollback()
            if is_session_error(e):
                raise SessionExpired(str(e)) from e
            failures.append(symbol)
            print(f"{symbol}: FAILED - {e}")
        time.sleep(PACE_SECONDS)
    return failures, updated, missing


def _yahoo(conn, held, day: dt.date) -> tuple[list[str], int]:
    tickers = {symbol: yahoo_tickers(symbol, exchange, None)[0] for symbol, _, exchange in held}
    failures, updated = [], 0
    for symbol, bars in minute_bars(tickers, day).items():
        bar = day_bar(bars, day)
        if not bar:
            continue
        try:
            upsert_rows(conn, symbol, [bar])
            updated += 1
        except Exception as e:
            conn.rollback()
            failures.append(symbol)
            print(f"{symbol}: FAILED - {e}")
    return failures, updated


def run(day: dt.date) -> tuple[list[str], int]:
    try:
        client = get_client()
    except SessionExpired:
        client = None
    with connect() as conn:
        held = conn.execute(HELD_SQL).fetchall()
        source = "breeze"
        if client:
            try:
                failures, updated, missing = _breeze(conn, client, held, day)
                if missing:
                    more_failures, more = _yahoo(conn, missing, day)
                    failures, updated = failures + more_failures, updated + more
                    source = f"breeze, yahoo for {more} of {len(missing)} Breeze had no data for"
            except SessionExpired:
                client = None
        if not client:
            source = "yahoo"
            failures, updated = _yahoo(conn, held, day)
        try:
            print(f"live indices: {live_indices(conn, day)} updated")
        except Exception as e:
            conn.rollback()
            print(f"live indices: FAILED - {e}")
    print(f"live prices ({source}): {updated} of {len(held)} held stocks updated for {day}")
    return failures, updated


def main() -> None:
    day = dt.date.fromisoformat(sys.argv[1]) if len(sys.argv) > 1 else dt.date.today()
    failures, updated = run(day)
    if updated == 0 and not failures:
        print(f"skipped: no trades on {day} (market closed)")
        sys.exit(SKIPPED_EXIT)
    if failures:
        sys.exit(1)


if __name__ == "__main__":
    main()
