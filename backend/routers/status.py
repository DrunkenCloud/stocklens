import datetime as dt

from fastapi import APIRouter

from db import pool
from jobs import mark_stale_runs
from services.session import session_state

router = APIRouter()

@router.get("/status")
def status():
    with pool.connection() as conn:
        mark_stale_runs(conn)
        session = conn.execute("SELECT captured_at, invalid_at FROM breeze_session WHERE id = 1").fetchone() or {}
        last_sync = conn.execute(
            """
            SELECT id, status, started_at, finished_at, summary FROM job_runs
            WHERE job = 'sync_icici' AND status <> 'running' ORDER BY started_at DESC LIMIT 1
            """
        ).fetchone()
        running = [r["job"] for r in conn.execute("SELECT DISTINCT job FROM job_runs WHERE status = 'running' AND job <> 'fetch_live'")]
        live = conn.execute(
            """
            SELECT finished_at FROM job_runs WHERE job = 'fetch_live' AND status = 'done'
            AND finished_at > now() - interval '30 minutes' ORDER BY finished_at DESC LIMIT 1
            """
        ).fetchone()
        prices_as_of = conn.execute("SELECT max(date) AS d FROM daily_prices").fetchone()["d"]

    captured_at = session.get("captured_at")
    return {
        "breeze": {
            "state": session_state(captured_at, session.get("invalid_at"), dt.datetime.now(dt.timezone.utc)),
            "captured_at": captured_at,
        },
        "last_sync": last_sync,
        "running": running,
        "prices_as_of": prices_as_of,
        "live_at": live["finished_at"] if live else None,
    }
