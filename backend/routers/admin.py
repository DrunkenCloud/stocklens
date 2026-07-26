"""Admin operations: trigger pipeline jobs and add companies from the UI
instead of SSH. See ADMIN_OPS.md for the design and why it's shaped this way
(subprocess, not in-process; no queue; no new auth).
"""
import os
import pathlib
import subprocess
import tempfile
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from db import pool

router = APIRouter()

REPO_ROOT = pathlib.Path(os.environ.get("REPO_ROOT", "..")).resolve()
RUN_JOB_SH = REPO_ROOT / "pipeline" / "run_job.sh"

JOBS: dict[str, list[str]] = {
    "fetch_prices": ["jobs.fetch_prices"],
    "fetch_prices_backfill": ["jobs.fetch_prices", "--backfill"],
    "fetch_fundamentals": ["jobs.fetch_fundamentals"],
    "map_breeze_codes": ["jobs.map_breeze_codes"],
}


class _JobRecord:
    def __init__(self, name: str, process: subprocess.Popen, log_path: pathlib.Path):
        self.name = name
        self.process = process
        self.log_path = log_path
        self.started_at = datetime.now(timezone.utc)

    def status(self) -> str:
        code = self.process.poll()
        return "running" if code is None else ("done" if code == 0 else "failed")


_jobs: dict[str, _JobRecord] = {}


@router.post("/admin/jobs/{job_name}", status_code=202)
def trigger_job(job_name: str):
    if job_name not in JOBS:
        raise HTTPException(status_code=404, detail=f"unknown job {job_name}")
    if any(j.name == job_name and j.status() == "running" for j in _jobs.values()):
        raise HTTPException(status_code=409, detail=f"{job_name} is already running")

    log_fh = tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".log", prefix=f"{job_name}-")
    process = subprocess.Popen(
        [str(RUN_JOB_SH), *JOBS[job_name]],
        stdout=log_fh,
        stderr=subprocess.STDOUT,
        cwd=REPO_ROOT,
    )
    job_id = str(uuid.uuid4())
    _jobs[job_id] = _JobRecord(job_name, process, pathlib.Path(log_fh.name))
    return {"job_id": job_id}


@router.get("/admin/jobs/{job_id}")
def job_status(job_id: str):
    job = _jobs.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="unknown job_id")

    log_tail = job.log_path.read_text()[-4000:] if job.log_path.exists() else ""
    return {"name": job.name, "status": job.status(), "started_at": job.started_at.isoformat(), "log_tail": log_tail}


@router.get("/admin/jobs")
def list_jobs():
    return [
        {"job_id": jid, "name": j.name, "status": j.status(), "started_at": j.started_at.isoformat()}
        for jid, j in sorted(_jobs.items(), key=lambda kv: kv[1].started_at, reverse=True)
    ]


class CompanyIn(BaseModel):
    symbol: str
    name: str
    sector: str | None = None


@router.post("/companies", status_code=201)
def add_company(company: CompanyIn):
    symbol = company.symbol.strip().upper()
    if not symbol:
        raise HTTPException(status_code=400, detail="symbol required")

    with pool.connection() as conn:
        if conn.execute("SELECT 1 FROM companies WHERE symbol = %s", (symbol,)).fetchone():
            raise HTTPException(status_code=409, detail=f"{symbol} already tracked")
        conn.execute(
            "INSERT INTO companies (symbol, name, sector) VALUES (%s, %s, %s)",
            (symbol, company.name, company.sector),
        )
        conn.commit()
    return {"symbol": symbol}
