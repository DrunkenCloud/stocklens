import os
import pathlib
import sys
import uuid

import psycopg
from psycopg import conninfo

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from migrate import apply_migrations, load_env

USER_ID = "00000000-0000-0000-0000-000000000001"


def scratch_db():
    base = os.environ["DATABASE_URL"]
    name = f"migtest_{uuid.uuid4().hex[:8]}"
    with psycopg.connect(base, autocommit=True) as admin:
        admin.execute(f"CREATE DATABASE {name}")
    params = conninfo.conninfo_to_dict(base)
    params["dbname"] = name
    return name, conninfo.make_conninfo(**params)


def drop_db(name):
    with psycopg.connect(os.environ["DATABASE_URL"], autocommit=True) as admin:
        admin.execute(f"DROP DATABASE {name} WITH (FORCE)")


def test_fresh_apply_is_idempotent(url):
    with psycopg.connect(url) as conn:
        first = apply_migrations(conn)
        second = apply_migrations(conn)
        assert first == sorted(first) and len(first) >= 5, first
        assert second == [], second
        tables = {r[0] for r in conn.execute("SELECT tablename FROM pg_tables WHERE schemaname='public'")}
        assert {"securities", "breeze_session", "job_runs", "schema_migrations"} <= tables, tables


def test_v1_holding_survives_upgrade(url):
    with psycopg.connect(url) as conn:
        apply_migrations(conn, upto="001_baseline.sql")
        conn.execute("INSERT INTO companies (symbol, name) VALUES ('ITC', 'ITC Ltd')")
        conn.execute(
            "INSERT INTO holdings (user_id, symbol, quantity, avg_cost, account) VALUES (%s, 'ITC', 10, 100, 'Zerodha')",
            (USER_ID,),
        )
        conn.execute(
            "INSERT INTO holdings (user_id, symbol, quantity, avg_cost, account) VALUES (%s, 'ITC', 2, 50, NULL)",
            (USER_ID,),
        )
        conn.commit()
        apply_migrations(conn)
        rows = conn.execute("SELECT quantity, price, broker, kind FROM stock_transactions ORDER BY quantity DESC").fetchall()
        assert [(float(q), float(p), b, k) for q, p, b, k in rows] == [
            (10.0, 100.0, "Zerodha", "buy"),
            (2.0, 50.0, "Other", "buy"),
        ], rows
        tables = {r[0] for r in conn.execute("SELECT tablename FROM pg_tables WHERE schemaname='public'")}
        assert "holdings" not in tables, tables


if __name__ == "__main__":
    load_env()
    for test in (test_fresh_apply_is_idempotent, test_v1_holding_survives_upgrade):
        name, url = scratch_db()
        try:
            test(url)
            print(f"ok  {test.__name__}")
        finally:
            drop_db(name)
