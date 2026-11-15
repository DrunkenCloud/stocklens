"""Load data for newly tracked stocks (spawned by the backend when a stock is
added from search or via a manual holding): fundamentals always, price history
if the Breeze session is valid (otherwise the next sync picks it up).

Usage: python -m pipeline.jobs.onboard --symbols ITC[,TCS]
"""
import argparse
import sys

from pipeline.breeze_client import SessionExpired
from pipeline.jobs import fetch_fundamentals, fetch_prices


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--symbols", required=True)
    symbols = parser.parse_args().symbols.split(",")

    failures = fetch_fundamentals.run(symbols)
    try:
        failures += fetch_prices.run(symbols)
        prices = "prices loaded"
    except SessionExpired:
        prices = "prices pending until the next ICICI login"
    except Exception as e:  # Breeze login/API trouble shouldn't hide the fundamentals result
        prices = f"prices failed ({e})"
        failures.append("prices")
    print(f"onboarded {', '.join(symbols)}: {prices}" + (f"; failed: {failures}" if failures else ""))
    if failures:
        sys.exit(1)


if __name__ == "__main__":
    main()
