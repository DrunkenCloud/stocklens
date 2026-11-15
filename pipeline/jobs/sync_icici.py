import datetime as dt
import sys

from pipeline.breeze_client import SessionExpired, get_client, is_session_error, mark_session_invalid
from pipeline.db import connect
from pipeline.holdings import parse_portfolio_holdings
from pipeline.jobs import fetch_fundamentals, fetch_prices, refresh_securities
from pipeline.run import SKIPPED_EXIT

USER_ID = "00000000-0000-0000-0000-000000000001"
SECURITIES_MAX_AGE = dt.timedelta(days=7)


def refresh_securities_if_stale() -> None:
    with connect() as conn:
        count, newest = conn.execute("SELECT count(*), max(updated_at) FROM securities").fetchone()
    if count == 0 or newest < dt.datetime.now(dt.timezone.utc) - SECURITIES_MAX_AGE:
        refresh_securities.main()


def fetch_icici_holdings() -> list[tuple[str, float, float]]:
    client = get_client()
    resp = client.get_portfolio_holdings(exchange_code="NSE")
    if isinstance(resp, dict) and resp.get("Error") and is_session_error(Exception(str(resp["Error"]))):
        mark_session_invalid()
        raise SessionExpired(str(resp["Error"]))
    return parse_portfolio_holdings(resp)


def store_holdings(holdings: list[tuple[str, float, float]]) -> tuple[int, list[str]]:
    with connect() as conn:
        mapped = {
            code: (symbol, name, isin)
            for code, symbol, name, isin in conn.execute(
                "SELECT breeze_code, nse_symbol, name, isin FROM securities WHERE nse_symbol IS NOT NULL AND breeze_code = ANY(%s)",
                ([h[0] for h in holdings],),
            )
        }
        unmapped = [code for code, _, _ in holdings if code not in mapped]
        rows = [(code, *mapped[code], qty, avg) for code, qty, avg in holdings if code in mapped]

        for code, symbol, name, isin, _, _ in rows:
            conn.execute(
                """
                INSERT INTO companies (symbol, name, isin, breeze_code) VALUES (%s, %s, %s, %s)
                ON CONFLICT (symbol) DO UPDATE SET is_active = TRUE, isin = EXCLUDED.isin, breeze_code = EXCLUDED.breeze_code
                """,
                (symbol, name, isin, code),
            )
        conn.execute("DELETE FROM holdings WHERE user_id = %s AND source = 'icici_sync'", (USER_ID,))
        for _, symbol, _, _, qty, avg in rows:
            conn.execute(
                """
                INSERT INTO holdings (user_id, symbol, quantity, invested, broker, source)
                VALUES (%s, %s, %s, %s, 'ICICI', 'icici_sync')
                """,
                (USER_ID, symbol, qty, round(qty * avg, 2)),
            )
    return len(rows), unmapped


def main() -> None:
    refresh_securities_if_stale()
    try:
        holdings = fetch_icici_holdings()
    except SessionExpired as e:
        print(f"skipped: Breeze session not valid ({e}) - log in to ICICI from the app")
        sys.exit(SKIPPED_EXIT)
    except Exception as e:
        print(f"FAILED reading ICICI holdings - stored holdings left unchanged: {e}")
        sys.exit(1)

    stored, unmapped = store_holdings(holdings)
    print(f"ICICI: {stored} holdings synced")
    if unmapped:
        print(f"ICICI: {len(unmapped)} holding(s) not on NSE / not in securities list, skipped: {unmapped}")

    try:
        price_failures = fetch_prices.run()
    except SessionExpired as e:
        price_failures = None
        print(f"prices skipped: session expired mid-sync ({e})")
    fund_failures = fetch_fundamentals.run(missing_only=True)

    problems = []
    if price_failures is None:
        problems.append("prices skipped")
    elif price_failures:
        problems.append(f"{len(price_failures)} price failures")
    if fund_failures:
        problems.append(f"{len(fund_failures)} fundamentals failures")
    print(f"synced {stored} ICICI holdings; " + (", ".join(problems) if problems else "prices up to date"))
    if problems:
        sys.exit(1)


if __name__ == "__main__":
    main()
