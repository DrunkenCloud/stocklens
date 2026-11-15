"""Download ICICI's SecurityMaster.zip and upsert every listed equity into
`securities` (powers stock search), then copy Breeze codes / ISINs onto tracked
companies. Public file, no Breeze session needed. Weekly cron + run by sync_icici
when stale.

Usage: python -m pipeline.jobs.refresh_securities
"""
import io
import urllib.request
import zipfile

from pipeline.db import connect
from pipeline.securities import parse_security_master

URL = "https://directlink.icicidirect.com/NewSecurityMaster/SecurityMaster.zip"
COLUMNS = ["isin", "name", "nse_symbol", "breeze_code", "nse_series", "bse_code", "bse_symbol"]


def download() -> tuple[str, str]:
    with urllib.request.urlopen(URL, timeout=60) as resp:
        archive = zipfile.ZipFile(io.BytesIO(resp.read()))
    read = lambda name: archive.read(name).decode("latin-1")  # noqa: E731
    return read("NSEScripMaster.txt"), read("BSEScripMaster.txt")


def main() -> None:
    rows = parse_security_master(*download())
    with connect() as conn, conn.cursor() as cur:
        cur.executemany(
            f"""
            INSERT INTO securities ({", ".join(COLUMNS)}, updated_at)
            VALUES ({", ".join(["%s"] * len(COLUMNS))}, now())
            ON CONFLICT (isin) DO UPDATE SET
                {", ".join(f"{c} = EXCLUDED.{c}" for c in COLUMNS[1:])}, updated_at = now()
            """,
            [[r[c] for c in COLUMNS] for r in rows],
        )
        cur.execute(
            """
            UPDATE companies c SET breeze_code = s.breeze_code, isin = s.isin
            FROM securities s
            WHERE s.nse_symbol = c.symbol
              AND (c.breeze_code IS DISTINCT FROM s.breeze_code OR c.isin IS DISTINCT FROM s.isin)
            """
        )
        updated = cur.rowcount
        cur.execute("SELECT count(*) FILTER (WHERE nse_symbol IS NOT NULL), count(*) FROM securities")
        nse, total = cur.fetchone()
    print(f"securities: {total} equities ({nse} on NSE); {updated} tracked companies updated")


if __name__ == "__main__":
    main()
