# backend/

FastAPI, plain SQL via psycopg3 with a dict-row pool (`db.py`); routes return rows directly and
FastAPI encodes Decimal/date. No ORM.

- Every route under `/api` (`main.py` includes each router with `prefix="/api"`).
- One router per resource in `routers/`; pure logic in `services/` with plain-assert self-checks
  run as `.venv/bin/python -m services.test_portfolio` (from `backend/`). No pytest.
- Background work goes through `jobs.spawn_job(name, extra_args, trigger)`: creates the `job_runs`
  row, then detaches `pipeline/run_job.sh ... --run-id N`. Never import pipeline code.
- Single user: `DEFAULT_USER_ID = 00000000-0000-0000-0000-000000000001` (seeded by migration 001).
- ICICI-synced holdings (`source='icici_sync'`) are read-only via the API (409).
- `db.py` needs `DATABASE_URL` in the environment (no dotenv here).
