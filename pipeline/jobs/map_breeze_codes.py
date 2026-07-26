"""One-off/rerunnable: resolve each company's Breeze stock_code via get_names()
and store it on companies.breeze_code. Breeze's internal code (isec_stock_code)
often differs from the plain NSE ticker (e.g. M&M -> MAHMAH, BAJAJFINSV -> BAFINS)
- confirmed against a live account, not guessed.

Usage: python -m pipeline.jobs.map_breeze_codes
"""
import os

import psycopg

from pipeline.breeze_client import get_client


def resolve_code(client, symbol: str) -> str | None:
    result = client.get_names(exchange_code="NSE", stock_code=symbol)
    code = result.get("isec_stock_code")
    return code or None


def main() -> None:
    client = get_client()
    conn = psycopg.connect(os.environ["DATABASE_URL"])
    failures = []

    with conn.cursor() as cur:
        cur.execute("SELECT symbol FROM companies WHERE is_active ORDER BY symbol")
        symbols = [r[0] for r in cur.fetchall()]

    for symbol in symbols:
        try:
            code = resolve_code(client, symbol)
            if code is None:
                failures.append(symbol)
                print(f"{symbol}: no isec_stock_code returned")
                continue
            with conn.cursor() as cur:
                cur.execute("UPDATE companies SET breeze_code = %s WHERE symbol = %s", (code, symbol))
            conn.commit()
            print(f"{symbol} -> {code}")
        except Exception as e:
            failures.append(symbol)
            print(f"{symbol}: FAILED - {e}")

    conn.close()
    if failures:
        print(f"\n{len(failures)} symbol(s) need manual mapping: {failures}")


if __name__ == "__main__":
    main()
