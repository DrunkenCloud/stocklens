import os
import pathlib
import sys

import psycopg

DB_DIR = pathlib.Path(__file__).resolve().parent
MIGRATIONS_DIR = DB_DIR / "migrations"


def load_env() -> None:
    try:
        from dotenv import load_dotenv
    except ImportError:
        return
    load_dotenv(DB_DIR.parent / ".env")


def apply_migrations(conn: psycopg.Connection, upto: str | None = None) -> list[str]:
    conn.execute("CREATE TABLE IF NOT EXISTS schema_migrations (name TEXT PRIMARY KEY, applied_at TIMESTAMPTZ NOT NULL DEFAULT now())")
    conn.commit()
    done = {r[0] for r in conn.execute("SELECT name FROM schema_migrations")}

    applied = []
    for path in sorted(MIGRATIONS_DIR.glob("*.sql")):
        if upto is not None and path.name > upto:
            break
        if path.name in done:
            continue
        try:
            conn.execute(path.read_text())
            conn.execute("INSERT INTO schema_migrations (name) VALUES (%s)", (path.name,))
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        applied.append(path.name)
    return applied


def main() -> None:
    load_env()
    with psycopg.connect(os.environ["DATABASE_URL"]) as conn:
        applied = apply_migrations(conn)
        print("applied: " + ", ".join(applied) if applied else "nothing to apply")
        if "--seed" in sys.argv:
            conn.execute((DB_DIR / "seed.sql").read_text())
            conn.commit()
            print("seeded")


if __name__ == "__main__":
    main()
