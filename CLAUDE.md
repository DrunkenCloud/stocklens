# StockLens (working name)

Personal NSE stock-evaluation tool: screener + fundamentals, AI narrative,
historical returns, manual portfolio. FastAPI + PostgreSQL + Next.js, prices
from ICICI Breeze API, fundamentals from a free scraper/API, AI via Anthropic.

**No code yet — this repo is currently the v1 spec.** Build order is in
`07_ROADMAP.md` (M0 skeleton → M1 prices → M2 returns → … → M7 ship).

## Read before building

The spec files (`00`–`07`) are the source of truth. Don't re-derive or
re-litigate what's already decided there:

- `00_OVERVIEW.md` — scope, stack, the three views, settled scope decisions
- `01_ARCHITECTURE.md` — system shape + target repo layout (`pipeline/`, `backend/`, `frontend/`, `db/`)
- `02_DATA_SOURCES.md` — Breeze (prices only) + fundamentals source constraints
- `03_PIPELINE.md` — the 3 ingestion jobs, Breeze auth flow, resilience rules
- `04_AI_FEATURE.md` — the exact AI prompt design (use it verbatim)
- `05_SCHEMA_AND_API.md` — Postgres schema, endpoint list, return formulas
- `06_DECISIONS.md` — rationale log (e.g. why no ClickHouse/Airflow)
- `07_ROADMAP.md` — milestone order + v2 deferrals

## Hard rules

1. **Describe, don't advise.** The tool (and its AI narrative) explains numbers;
   it never recommends buy/sell or predicts returns. Enforced in the AI system
   prompt (`04_AI_FEATURE.md`) and UI copy. Non-negotiable.
2. **Postgres only.** No ClickHouse, no Redis, no Airflow/Kafka in v1 — see
   `06_DECISIONS.md` before proposing infra.
3. **Pipeline stays out of the API request path.** Standalone scheduled jobs,
   idempotent upserts, per-symbol failure isolation.
4. **AI grounded in stored numbers only** — structured prompt with real data,
   never "analyze RELIANCE" freeform. Cache narratives keyed on
   `(symbol, fundamentals_snapshot_date)`.
5. **Secrets (Breeze `api_key`/`api_secret`/session, Anthropic key) live in env,
   never in code or git.**
