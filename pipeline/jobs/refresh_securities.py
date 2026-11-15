import io
import urllib.request
import zipfile

from pipeline.db import connect
from pipeline.securities import parse_security_master

URL = "https://directlink.icicidirect.com/NewSecurityMaster/SecurityMaster.zip"
COLUMNS = ["isin", "name", "nse_symbol", "breeze_code", "nse_series", "bse_code", "bse_symbol", "bse_breeze_code", "kind", "asset_class"]


def download() -> tuple[str, str]:
    with urllib.request.urlopen(URL, timeout=60) as resp:
        archive = zipfile.ZipFile(io.BytesIO(resp.read()))
    read = lambda name: archive.read(name).decode("latin-1")
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
            UPDATE companies c SET
                breeze_code = CASE WHEN c.exchange = 'BSE' THEN s.bse_breeze_code ELSE s.breeze_code END,
                isin = s.isin, kind = s.kind, asset_class = s.asset_class
            FROM securities s
            WHERE ((c.exchange = 'NSE' AND s.nse_symbol = c.symbol) OR (c.exchange = 'BSE' AND s.isin = c.isin))
              AND (c.breeze_code IS DISTINCT FROM CASE WHEN c.exchange = 'BSE' THEN s.bse_breeze_code ELSE s.breeze_code END
                   OR c.isin IS DISTINCT FROM s.isin OR c.kind <> s.kind OR c.asset_class <> s.asset_class)
            """
        )
        updated = cur.rowcount
        cur.execute("SELECT count(*) FILTER (WHERE nse_symbol IS NOT NULL), count(*) FROM securities")
        nse, total = cur.fetchone()
    print(f"securities: {total} equities ({nse} on NSE); {updated} tracked companies updated")


if __name__ == "__main__":
    main()
