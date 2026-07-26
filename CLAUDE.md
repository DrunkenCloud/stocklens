# StockLens (working name)

Personal NSE stock-evaluation tool: screener + fundamentals, historical returns,
manual portfolio, an admin panel for pipeline ops. FastAPI (routes under `/api`)
+ PostgreSQL + a Vite/React static SPA, prices from ICICI Breeze API,
fundamentals from Yahoo Finance. No AI feature (cut — no Anthropic API budget,
see `06_DECISIONS.md` D5).

**Live at https://investlens.duckdns.org** — deployed on the user's Azure VPS
(135.235.195.168), native processes (not Docker), Caddy reverse-proxying
`/api/*` to the backend and serving the frontend as static files. See
"Deployment" below for how to change what's running there.

**Build order is `07_ROADMAP.md`** (M0 skeleton → M1 prices → M2 returns → …
→ M6 ship). All of M0–M6 are done and verified against live data — real Breeze
price history (2015–2026, all 30 tracked companies), real Yahoo Finance
fundamentals, cron-scheduled ongoing updates, and now an Admin panel
(`ADMIN_OPS.md`) so routine ops don't need SSH.

## Read before building

The spec files (`00`–`07`, skipping the deleted `04`) are the *original* v1
spec — source of truth for what v1 is, don't re-derive or re-litigate what's
already decided there. Two more docs cover what came after v1 was written:

- `00_OVERVIEW.md` — scope, stack, the three views, settled scope decisions
- `01_ARCHITECTURE.md` — system shape + repo layout (as built, not just "suggested")
- `02_DATA_SOURCES.md` — Breeze (prices only) + fundamentals source constraints
- `03_PIPELINE.md` — the 3 ingestion jobs, Breeze auth flow, resilience rules
- `05_SCHEMA_AND_API.md` — Postgres schema, endpoint list, return formulas
- `06_DECISIONS.md` — rationale log (why no ClickHouse/Airflow, why AI was cut,
  why Vite not Next.js, why native deploy not Docker, why no auth)
- `07_ROADMAP.md` — milestone order + v2 deferrals
- `ADMIN_OPS.md` — the admin panel: what it does, what it deliberately doesn't

Directory-scoped `CLAUDE.md` files exist in `backend/`, `frontend/`, and
`pipeline/` with area-specific conventions — read the one for whichever part
you're touching in addition to this file.

## Hard rules

1. **Describe, don't advise.** The tool explains numbers (ratios, returns); it
   never recommends buy/sell or predicts returns. Enforced in UI copy.
   Non-negotiable.
2. **Postgres only.** No ClickHouse, no Redis, no Airflow/Kafka/job-queue — see
   `06_DECISIONS.md` (D1, D7) and `ADMIN_OPS.md` before proposing infra. This
   isn't just a v1-launch constraint - it held through the admin panel too.
3. **Pipeline stays out of the API request path.** Standalone scheduled jobs,
   idempotent upserts, per-symbol failure isolation. The admin panel *triggers*
   pipeline jobs as detached subprocesses (`pipeline/run_job.sh`) — it does not
   import pipeline code into the backend process. Keep that boundary if you
   add more admin-triggered operations.
4. **Secrets (Breeze `api_key`/`api_secret`/session, `BREEZE_CALLBACK_TOKEN`)
   live in env, never in code or git.**
5. **No AI feature.** Don't add an Anthropic (or any LLM) call anywhere in this
   project unless the user explicitly asks — there's no API budget for it.
6. **No new auth for one feature at a time.** The whole app is intentionally
   unauthenticated (single fixed user, D9) — don't gate just the admin panel
   or just one endpoint. If auth is wanted, it's a site-wide decision (deferred
   to v2 in `07_ROADMAP.md`).

## Deployment

VM: `ssh 135.235.195.168` (user `drunkencloud`, key-based auth, **no
passwordless sudo** — privileged changes need a short script run by the user
themselves, see `deploy/setup_root.sh`). Repo lives at `~/trading` on the VM,
synced via `git ls-files | rsync --files-from=-` (no git remote configured -
this is a direct dev-machine-to-VM push, not a pull-based deploy).

To ship a change:
- **Backend:** rsync the changed files, then
  `systemctl --user restart stocklens-backend.service` on the VM.
- **Frontend:** build locally with the prod API URL
  (`VITE_API_URL=https://investlens.duckdns.org/api npm run build`), rsync
  `frontend/dist/` to `~/trading/frontend/dist/` on the VM (Caddy serves it
  directly - no Node.js runtime on the VM at all).
- **Pipeline:** rsync `pipeline/`, no restart needed (jobs are triggered fresh
  each cron tick / admin-panel click, not a long-running process).

Caddy config lives in its live-reloaded JSON state (admin API on
`127.0.0.1:2019`), not hand-edited in `/etc/caddy/Caddyfile` — see
`06_DECISIONS.md` D10 for how the `investlens.duckdns.org` route was added
additively alongside the VM's pre-existing `memos-diary.duckdns.org` site.
