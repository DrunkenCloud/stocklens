"""Spawn pipeline jobs as detached subprocesses (never imported: the pipeline
stays out of the API process). The job_runs row is created here so callers get
an id back immediately; pipeline/run.py fills in log, status and summary.
"""
import os
import pathlib
import subprocess

from db import pool

REPO_ROOT = pathlib.Path(os.environ.get("REPO_ROOT", "..")).resolve()
RUN_JOB_SH = REPO_ROOT / "pipeline" / "run_job.sh"

# name -> [module, *fixed args]. "onboard" takes --symbols from the caller.
JOBS: dict[str, list[str]] = {
    "sync_icici": ["jobs.sync_icici"],
    "fetch_prices": ["jobs.fetch_prices"],
    "fetch_prices_backfill": ["jobs.fetch_prices", "--backfill"],
    "fetch_fundamentals": ["jobs.fetch_fundamentals"],
    "refresh_securities": ["jobs.refresh_securities"],
    "onboard": ["jobs.onboard"],
}
STALE_AFTER = "6 hours"  # a 'running' row older than this lost its process (VM reboot, kill)

_children: list[subprocess.Popen] = []


class JobAlreadyRunning(Exception):
    pass


def mark_stale_runs(conn) -> None:
    conn.execute(
        f"""
        UPDATE job_runs SET status = 'failed', finished_at = now(), summary = 'no exit recorded (process died?)'
        WHERE status = 'running' AND started_at < now() - interval '{STALE_AFTER}'
        """
    )


def spawn_job(name: str, extra_args: list[str] | None = None, trigger: str = "admin") -> int:
    module, *args = JOBS[name]
    args = [*args, *(extra_args or [])]
    job = module.removeprefix("jobs.")

    with pool.connection() as conn:
        mark_stale_runs(conn)
        if name != "onboard" and conn.execute(
            "SELECT 1 FROM job_runs WHERE job = %s AND args = %s AND status = 'running'", (job, " ".join(args))
        ).fetchone():
            raise JobAlreadyRunning(name)
        run_id = conn.execute(
            "INSERT INTO job_runs (job, args, trigger) VALUES (%s, %s, %s) RETURNING id", (job, " ".join(args), trigger)
        ).fetchone()["id"]

    _children[:] = [p for p in _children if p.poll() is None]  # reap finished children (no zombies)
    _children.append(subprocess.Popen(
        [str(RUN_JOB_SH), module, *args, "--trigger", trigger, "--run-id", str(run_id)],
        cwd=REPO_ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True,
    ))
    return run_id
