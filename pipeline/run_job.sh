#!/usr/bin/env bash
# Cron wrapper: cd to repo root (cron has no notion of a working dir), then
# run a job module through the venv's python, logging with timestamps.
# Usage in crontab: /path/to/pipeline/run_job.sh jobs.fetch_prices [--backfill]
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
"$PYTHON" -m "pipeline.$JOB" "$@" && STATUS=0 || STATUS=$?
echo "[$(date -Iseconds)] pipeline.$JOB exited $STATUS"
exit $STATUS
