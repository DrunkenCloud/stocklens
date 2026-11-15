import argparse
import datetime as dt
import json
import urllib.request

from pipeline.db import connect
from pipeline.mf import parse_navall

NAVALL_URL = "https://portal.amfiindia.com/spages/NAVAll.txt"
HISTORY_URL = "https://api.mfapi.in/mf/{code}"
COLUMNS = ["code", "name", "amc", "category", "plan", "option", "isin", "isin_reinvest", "asset_class", "nav", "nav_date"]
MIN_HISTORY_ROWS = 30


def fetch(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=90) as resp:
        return resp.read()


def update_schemes(conn) -> int:
    rows = parse_navall(fetch(NAVALL_URL).decode("utf-8", errors="replace"))
    with conn.cursor() as cur:
        cur.executemany(
            f"""
            INSERT INTO mf_schemes ({", ".join(COLUMNS)}, updated_at) VALUES ({", ".join(["%s"] * len(COLUMNS))}, now())
            ON CONFLICT (code) DO UPDATE SET {", ".join(
                f"{c} = COALESCE(EXCLUDED.{c}, mf_schemes.{c})" if c in ("plan", "option") else f"{c} = EXCLUDED.{c}"
                for c in COLUMNS[1:]
            )}, updated_at = now()
            """,
            [[r[c] for c in COLUMNS] for r in rows],
        )
    conn.commit()
    return len(rows)


def backfill_history(conn, code: int) -> int:
    data = json.loads(fetch(HISTORY_URL.format(code=code)))
    points = [(code, dt.datetime.strptime(p["date"], "%d-%m-%Y").date(), float(p["nav"])) for p in data.get("data", [])]
    with conn.cursor() as cur:
        cur.executemany("INSERT INTO mf_nav (code, date, nav) VALUES (%s, %s, %s) ON CONFLICT DO NOTHING", points)
    conn.commit()
    return len(points)


def run(codes: list[int] | None = None) -> list[int]:
    failures = []
    with connect() as conn:
        print(f"schemes: {update_schemes(conn)} with today's NAV")
        held = [r[0] for r in conn.execute("SELECT DISTINCT code FROM mf_transactions ORDER BY 1")]
        targets = codes or held
        conn.execute(
            "INSERT INTO mf_nav (code, date, nav) SELECT code, nav_date, nav FROM mf_schemes "
            "WHERE code = ANY(%s) AND nav IS NOT NULL ON CONFLICT DO NOTHING",
            (targets,),
        )
        conn.commit()
        for code in targets:
            (count,) = conn.execute("SELECT count(*) FROM mf_nav WHERE code = %s", (code,)).fetchone()
            if count >= MIN_HISTORY_ROWS and not codes:
                continue
            try:
                print(f"{code}: {backfill_history(conn, code)} NAV points")
            except Exception as e:
                conn.rollback()
                failures.append(code)
                print(f"{code}: FAILED - {e}")
    return failures


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--codes", help="comma-separated scheme codes to backfill; default every held fund missing history")
    args = parser.parse_args()
    failures = run([int(c) for c in args.codes.split(",")] if args.codes else None)
    if failures:
        raise SystemExit(1)
    print("mutual fund NAVs up to date")


if __name__ == "__main__":
    main()
