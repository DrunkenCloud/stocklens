# Admin operations: getting pipeline ops out of SSH

Not part of the original numbered spec (`00`–`07`) — that's the settled v1
plan, don't re-litigate it there. This is a post-deploy operability decision:
right now, adding a company to track or re-running a pipeline job means SSH
into the VM and running a command by hand. Fine for the deploy-time
bootstrap, tedious for ongoing personal use. This doc is the design for
fixing that with a small in-app Admin panel.

## What it does

- **Add a company** — a form (symbol, name, sector) that inserts into
  `companies`. Today the only way in is `db/seed.sql`.
- **Trigger a pipeline job on demand** — buttons for `fetch_prices`,
  `fetch_prices --backfill`, `fetch_fundamentals`, `map_breeze_codes`, with
  live status/log output, instead of `ssh` + `run_job.sh`.

## Design

**Backend** (`backend/routers/admin.py`):
- `POST /api/admin/jobs/{job_name}` — spawns `pipeline/run_job.sh` as a
  **detached subprocess** (not imported/run in-process). Returns a `job_id`
  immediately (202).
- `GET /api/admin/jobs/{job_id}` — polls the subprocess (`Popen.poll()`) and
  tails its log file. `GET /api/admin/jobs` lists recent runs.
- `POST /api/companies` — insert a row into `companies`.

**Frontend**: a new `/admin` page — the add-company form, four job buttons,
and a polling status view (2s interval) showing the live log tail.

**Job registry**: an in-memory dict in the API process (`job_id -> Popen +
log path + start time`). Lost on server restart — acceptable for a personal
admin tool; jobs are cheap and idempotent to re-run, and losing status on a
restart you triggered yourself is a non-event.

## Why subprocess, not in-process (FastAPI `BackgroundTasks`)

`BackgroundTasks` would run job code inside the API's own process (via a
thread pool) — simpler to wire, but it means importing `pipeline` code
directly into `backend`, which breaks the boundary `01_ARCHITECTURE.md`
already established ("pipeline: standalone ingestion, **not imported by
API**") and couples a job crash to the API process. Spawning
`pipeline/run_job.sh` as a subprocess keeps that boundary intact — the API
*triggers* runs now, but still doesn't *execute* them in its own process.
Also gets the wrapper's existing logging/exit-code handling for free
(already built, already tested this session).

## Why not more — things deliberately not built

- **No job queue (Celery/Redis/etc).** One admin (you), occasional clicks,
  four jobs. An in-memory dict and a subprocess is the whole "queue" this
  needs. Same reasoning as `06_DECISIONS.md` D1 (no Redis) and D7 (no
  Airflow/Kafka) — a task-queue system here would be résumé-driven, not
  needed-driven.
- **No per-symbol job scoping.** Re-running a full job after adding one
  company costs a few extra seconds (30 companies took 5–20s in testing) —
  not worth adding `--symbol` filters to three job scripts for. Worth
  revisiting only if the tracked universe grows enough that "just re-run the
  whole thing" stops being cheap. Also, `fetch_prices`' existing incremental
  logic already backfills a genuinely-new company correctly on its own
  (`incremental_from_date` returns the full backfill start when there's no
  existing price row) — so this isn't even required for correctness, just a
  speed optimization for later.
- **No new auth on these endpoints.** The whole app is already
  unauthenticated by design (`06_DECISIONS.md` D9 — single fixed user, v1 is
  single-user). Portfolio CRUD is already wide open to anyone with the URL;
  gating just the admin endpoints while leaving that open wouldn't actually
  improve the security posture, just be inconsistent. If real auth is ever
  wanted, that's a site-wide v2 decision (already logged as deferred in
  `07_ROADMAP.md`), not something to bolt onto one feature.
- **No persisted job history.** In-memory is enough for "did the thing I
  just clicked work" — a job-runs table is worth adding if this ever needs
  to answer "did last Tuesday's cron run succeed," which cron's own log file
  (`pipeline/cron.log`) already answers today.

## Status

Building the whole thing described above now — it's small enough not to
phase. Future ideas if this ever needs more: per-symbol job scoping (once
the universe grows), a persisted job-history table, WebSocket log streaming
instead of polling.
