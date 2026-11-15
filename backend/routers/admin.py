import pathlib

from fastapi import APIRouter, HTTPException, Query

from db import pool
from jobs import JOBS, JobAlreadyRunning, mark_stale_runs, spawn_job

router = APIRouter()

TRIGGERABLE = [name for name in JOBS if name != "onboard"]
LOG_TAIL_CHARS = 8000


@router.post("/admin/jobs/{name}", status_code=202)
def trigger_job(name: str):
    if name not in TRIGGERABLE:
        raise HTTPException(status_code=404, detail=f"unknown job {name}")
    try:
        return {"run_id": spawn_job(name, trigger="admin")}
    except JobAlreadyRunning:
        raise HTTPException(status_code=409, detail=f"{name} is already running")


@router.get("/admin/jobs")
def list_runs(limit: int = Query(30, le=200)):
    with pool.connection() as conn:
        mark_stale_runs(conn)
        runs = conn.execute(
            """
            SELECT id, job, args, trigger, status, started_at, finished_at, summary
            FROM job_runs
            WHERE job <> 'fetch_live' OR id = (SELECT max(id) FROM job_runs WHERE job = 'fetch_live')
            ORDER BY started_at DESC LIMIT %s
            """,
            (limit,),
        ).fetchall()
    return {"jobs": TRIGGERABLE, "runs": runs}


@router.get("/admin/jobs/{run_id}")
def get_run(run_id: int):
    with pool.connection() as conn:
        run = conn.execute(
            "SELECT id, job, args, trigger, status, started_at, finished_at, summary, log_path FROM job_runs WHERE id = %s",
            (run_id,),
        ).fetchone()
    if run is None:
        raise HTTPException(status_code=404, detail="unknown run")
    log_path = run.pop("log_path")
    log = pathlib.Path(log_path) if log_path else None
    run["log_tail"] = log.read_text(errors="replace")[-LOG_TAIL_CHARS:] if log and log.exists() else ""
    return run
