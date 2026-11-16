import datetime as dt

import yfinance as yf

from pipeline.bars import day_bar
from pipeline.yahoo_prices import history_bars, minute_bars

BACKFILL_START = dt.date(2015, 1, 1)


def _upsert(conn, symbol: str, bars: list[dict]) -> None:
    with conn.cursor() as cur:
        cur.executemany(
            """
            INSERT INTO index_prices (symbol, date, close) VALUES (%s, %s, %s)
            ON CONFLICT (symbol, date) DO UPDATE SET close = EXCLUDED.close
            """,
            [(symbol, b["datetime"][:10], b["close"]) for b in bars],
        )
    conn.commit()


def refresh_indices(conn) -> list[str]:
    failures = []
    rows = conn.execute(
        """
        SELECT m.symbol, max(p.date) FROM market_indices m LEFT JOIN index_prices p ON p.symbol = m.symbol
        GROUP BY m.symbol, m.position ORDER BY m.position
        """
    ).fetchall()
    for symbol, last in rows:
        start = last or BACKFILL_START
        try:
            bars = history_bars(yf.Ticker(symbol).history(start=start.isoformat(), interval="1d", auto_adjust=False))
            _upsert(conn, symbol, bars)
            print(f"index {symbol}: {len(bars)} rows from {start}")
        except Exception as e:
            conn.rollback()
            failures.append(symbol)
            print(f"index {symbol}: FAILED - {e}")
    return failures


def live_indices(conn, day: dt.date) -> int:
    symbols = [r[0] for r in conn.execute("SELECT symbol FROM market_indices ORDER BY position")]
    updated = 0
    for symbol, bars in minute_bars({s: s for s in symbols}, day).items():
        bar = day_bar(bars, day)
        if bar:
            _upsert(conn, symbol, [bar])
            updated += 1
    return updated
