# StockLens (working name)

Personal NSE stock-evaluation tool: screener + fundamentals, historical returns,
manual portfolio. FastAPI + PostgreSQL + Next.js, prices from ICICI Breeze API,
fundamentals from a free scraper/API. No AI feature (cut — no Anthropic API
budget, see `06_DECISIONS.md` D5).

**Build order is `07_ROADMAP.md`** (M0 skeleton → M1 prices → M2 returns → …
→ M6 ship). Progress: M0–M5 are built - skeleton/DB, a Breeze pipeline
verified live (all 30 seeded companies, real price history back to 2015),
return math + `/prices` endpoints, fundamentals via yfinance (also verified
live) + `/stocks` endpoints, a filterable/sortable screener, and manual
portfolio CRUD (`/portfolio`, single fixed user - D9, no auth in v1). M6 is
mostly done (cron wiring, staleness UI, error states); only the actual VM
deploy is outstanding, pending the user's infra access.

## Read before building

The spec files (`00`–`07`, skipping the deleted `04`) are the source of truth.
Don't re-derive or re-litigate what's already decided there:

- `00_OVERVIEW.md` — scope, stack, the three views, settled scope decisions
- `01_ARCHITECTURE.md` — system shape + target repo layout (`pipeline/`, `backend/`, `frontend/`, `db/`)
- `02_DATA_SOURCES.md` — Breeze (prices only) + fundamentals source constraints
- `03_PIPELINE.md` — the 3 ingestion jobs, Breeze auth flow, resilience rules
- `05_SCHEMA_AND_API.md` — Postgres schema, endpoint list, return formulas
- `06_DECISIONS.md` — rationale log (e.g. why no ClickHouse/Airflow, why AI was cut)
- `07_ROADMAP.md` — milestone order + v2 deferrals

## Hard rules

1. **Describe, don't advise.** The tool explains numbers (ratios, returns); it
   never recommends buy/sell or predicts returns. Enforced in UI copy.
   Non-negotiable.
2. **Postgres only.** No ClickHouse, no Redis, no Airflow/Kafka in v1 — see
   `06_DECISIONS.md` before proposing infra.
3. **Pipeline stays out of the API request path.** Standalone scheduled jobs,
   idempotent upserts, per-symbol failure isolation.
4. **Secrets (Breeze `api_key`/`api_secret`/session) live in env, never in code
   or git.**
5. **No AI feature.** Don't add an Anthropic (or any LLM) call anywhere in this
   project unless the user explicitly asks — there's no API budget for it.
