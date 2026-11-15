import argparse
import json
import sys
import urllib.request

from pipeline.db import connect
from pipeline.fund_portfolios import CATALOG_URL, portfolio_rows, portfolio_url

INDUSTRY_SOURCE_CODES = [152092]


def fetch_json(url: str):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=120) as resp:
        return json.loads(resp.read())


def held_codes(conn) -> list[int]:
    rows = conn.execute(
        """
        SELECT DISTINCT code FROM mf_transactions
        UNION
        SELECT s.code FROM companies c JOIN mf_schemes s ON s.isin = c.isin
        WHERE c.kind = 'etf' AND c.symbol IN (SELECT DISTINCT symbol FROM stock_transactions)
        """
    ).fetchall()
    return sorted({r[0] for r in rows} | set(INDUSTRY_SOURCE_CODES))


def run(codes: list[int] | None = None) -> list[int]:
    catalog = fetch_json(CATALOG_URL)
    missing = []
    with connect() as conn:
        for code in codes or held_codes(conn):
            entry = catalog.get(str(code))
            if not entry or not entry.get("has_holdings") or not entry.get("latest_as_of"):
                missing.append(code)
                print(f"{code}: no published portfolio")
                continue
            pid, as_of = entry["portfolio_id"], entry["latest_as_of"]
            current = conn.execute(
                "SELECT max(as_of) FROM fund_portfolio_holdings WHERE portfolio_id = %s", (pid,)
            ).fetchone()[0]
            if current is None or current.isoformat() != as_of:
                rows = portfolio_rows(fetch_json(portfolio_url(as_of, pid)))
                conn.execute("DELETE FROM fund_portfolio_holdings WHERE portfolio_id = %s", (pid,))
                with conn.cursor() as cur:
                    cur.executemany(
                        """
                        INSERT INTO fund_portfolio_holdings (portfolio_id, position, as_of, isin, name, holding_type, industry, pct_nav)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        """,
                        [(pid, r["position"], as_of, r["isin"], r["name"], r["holding_type"], r["industry"], r["pct_nav"]) for r in rows],
                    )
                print(f"{code}: {len(rows)} holdings as of {as_of}")
            conn.execute("UPDATE mf_schemes SET portfolio_id = %s, portfolio_as_of = %s WHERE code = %s", (pid, as_of, code))
            conn.commit()
    return missing


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--codes", help="comma-separated AMFI scheme codes; default every held fund and ETF")
    args = parser.parse_args()
    missing = run([int(c) for c in args.codes.split(",")] if args.codes else None)
    print("fund portfolios up to date" + (f"; {len(missing)} without published portfolio" if missing else ""))


if __name__ == "__main__":
    main()
