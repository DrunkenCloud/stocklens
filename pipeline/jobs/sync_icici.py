import datetime as dt
import sys

from pipeline.breeze_client import SessionExpired, get_client
from pipeline.db import connect
from pipeline.jobs import fetch_fundamentals, fetch_prices, refresh_securities
from pipeline.run import SKIPPED_EXIT

SECURITIES_MAX_AGE = dt.timedelta(days=7)


def refresh_securities_if_stale() -> None:
    with connect() as conn:
        count, newest = conn.execute("SELECT count(*), max(updated_at) FROM securities").fetchone()
    if count == 0 or newest < dt.datetime.now(dt.timezone.utc) - SECURITIES_MAX_AGE:
        refresh_securities.main()


def main() -> None:
    refresh_securities_if_stale()
    try:
        get_client()
        price_failures = fetch_prices.run()
    except SessionExpired as e:
        print(f"skipped: Breeze session not valid ({e}) - log in to ICICI from the app")
        sys.exit(SKIPPED_EXIT)
    fund_failures = fetch_fundamentals.run(missing_only=True)

    problems = []
    if price_failures:
        problems.append(f"{len(price_failures)} price failures")
    if fund_failures:
        problems.append(f"{len(fund_failures)} fundamentals failures")
    print("updated after login; " + (", ".join(problems) if problems else "prices up to date"))
    if problems:
        sys.exit(1)


if __name__ == "__main__":
    main()
