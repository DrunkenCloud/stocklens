#!/usr/bin/env bash
# Entry point for every job run (cron and the backend): cd to repo root (cron has
# no notion of a working dir), then run the job via pipeline/run.py, which records
# it in job_runs and writes pipeline/logs/<run id>.log.
# Usage: /path/to/pipeline/run_job.sh jobs.fetch_prices [--backfill] [--trigger admin] [--run-id N]
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

VENV_PYTHON="$REPO_ROOT/pipeline/.venv/bin/python"
if [ -x "$VENV_PYTHON" ]; then
    PYTHON="$VENV_PYTHON"
else
    PYTHON="python3"
fi

JOB="$1"
shift

echo "[$(date -Iseconds)] starting pipeline.$JOB $*"
"$PYTHON" -m pipeline.run "$JOB" "$@" && STATUS=0 || STATUS=$?
echo "[$(date -Iseconds)] pipeline.$JOB exited $STATUS"
exit $STATUS
