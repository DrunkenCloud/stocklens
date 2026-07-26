# backend/

FastAPI app. Plain SQL via `psycopg` + a connection pool (`db.py`) — no ORM
(`05_SCHEMA_AND_API.md` explicitly allows "SQL + pydantic"; keep it that way
unless the schema genuinely outgrows hand-written queries).

## Conventions

- **Every route lives under `/api`** — `app.include_router(x, prefix="/api")`
  in `main.py` for each router. Keep this consistent in dev and prod (don't
  special-case one or the other); Caddy's routing on the deployed VM depends
  on it to split static files from the backend with one rule.
- **One router file per resource** (`routers/stocks.py`, `screen.py`,
  `prices.py`, `portfolio.py`, `breeze_auth.py`, `admin.py`) — add new
  endpoints to the matching file, new files for new resources.
- **Pure functions get a self-check**, not a test framework. See
  `services/test_returns.py` / `routers/test_breeze_auth.py` — plain asserts,
  runnable via `python -m services.test_returns` (needs `backend/.venv`, see
  Setup below). No pytest, no fixtures, per the project's general "ponytail"
  bias toward the smallest thing that actually verifies the logic.
- **Admin-triggered pipeline jobs run as subprocesses, never imports.**
  `routers/admin.py` spawns `pipeline/run_job.sh` — it does not
  `import pipeline`. This is deliberate (`01_ARCHITECTURE.md`: pipeline is
  "not imported by API"; `ADMIN_OPS.md` explains why subprocess over
  `BackgroundTasks`). Keep it that way for any new admin-triggered operation.
- **No new auth per-endpoint.** The whole app is unauthenticated by design
  (D9) — see the root `CLAUDE.md` hard rules before adding a guard to just
  one route.

## Setup (for running/testing outside Docker)

```
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

`db.py` reads `DATABASE_URL` from the environment (no dotenv loading here,
unlike `pipeline/` — set it explicitly, e.g.
`DATABASE_URL=postgresql://stocklens:stocklens@localhost:5433/stocklens .venv/bin/uvicorn main:app`
against the docker-compose Postgres for local testing without the API
container).
