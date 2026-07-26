# Architecture

## System shape

```
                    ┌────────────────────────┐
                    │      DATA PIPELINE       │
                    │  (scheduled Python jobs) │
                    │                          │
   Breeze API ─────▶│  • prices job (daily)    │
   (ICICI Direct)   │  • fundamentals job      │──────┐
                    │  • universe/refresh job  │      │
   Fundamentals ───▶│                          │      │
   source (free)    └────────────────────────┘      │ writes
                                                       ▼
                                              ┌─────────────────┐
                                              │   PostgreSQL     │
                                              │                  │
                                              │  companies       │
                                              │  daily_prices    │
                                              │  fundamentals    │
                                              │  holdings        │
                                              │  users           │
                                              └─────────────────┘
                                                       ▲
                                                       │ reads
                                              ┌─────────────────┐
                                              │    FastAPI       │
                                              │   (backend)      │
                                              │                  │
                                              │  /api/stocks     │
                                              │  /api/screen     │
                                              │  /api/prices     │
                                              │  /api/portfolio  │
                                              └─────────────────┘
                                                       ▲
                                                       │ HTTP/JSON
                                              ┌─────────────────┐
                                              │  Vite/React SPA  │
                                              │  (static files)  │
                                              │  Screener        │
                                              │  Stock detail    │
                                              │  Portfolio       │
                                              └─────────────────┘
```

## Components

**Data pipeline (Python, scheduled).**
Standalone jobs, not part of the request path. They fetch from Breeze and the
fundamentals source and write into Postgres. Runs on a schedule (cron / a simple
scheduler). Kept separate from FastAPI so a slow/broken fetch never blocks the API.
Details in `03_PIPELINE.md`.

**PostgreSQL.**
Single source of truth for the app. Five tables (`05_SCHEMA_AND_API.md`). The pipeline writes;
FastAPI reads (plus writes for user-entered holdings). No second database — see
`06_DECISIONS.md` on why ClickHouse is out.

**FastAPI backend.**
Read API over the stored data, routes under `/api`. Also handles manual holdings
CRUD. Return calculations (CAGR, drawdown, etc.) live here as pure functions over
`daily_prices`.

**Vite/React frontend.**
A static SPA (no Node.js server needed in prod — `06_DECISIONS.md` D10). Three
surfaces: screener (filter/rank table), stock detail (fundamentals + price
chart), portfolio (manual entry + returns). Talks only to FastAPI, client-side.

## Data flow, end to end

1. **Ingest (offline, scheduled):** pipeline pulls daily prices (Breeze) and
   fundamentals (free source) → normalizes → upserts into Postgres.
2. **Browse/screen (request):** UI → `GET /api/screen?filters` → FastAPI queries
   `fundamentals` + latest `daily_prices` → ranked list back.
3. **Stock detail (request):** UI → `GET /api/stocks/{symbol}` (fundamentals + price
   series).
4. **Returns (request):** UI → `GET /api/prices/{symbol}/returns?from=...&amount=...`
   → FastAPI computes CAGR / total return / drawdown from `daily_prices`.
5. **Portfolio (request):** UI → `POST/GET /api/portfolio` → holdings stored in
   Postgres; returns computed against latest price per symbol.

## Repo layout (as built)

```
stocklens/
├── pipeline/                  # standalone ingestion (not imported by API)
│   ├── breeze_client.py       # auth flow + price fetch wrapper
│   ├── fundamentals_source.py # yfinance wrapper + normalization
│   ├── run_job.sh             # cron wrapper (repo-root-relative, venv-aware)
│   ├── crontab.example
│   ├── jobs/
│   │   ├── map_breeze_codes.py  # symbol -> Breeze stock_code (D3)
│   │   ├── fetch_prices.py
│   │   └── fetch_fundamentals.py
│   └── README.md
│   # refresh_universe.py not built - v1 uses hand-seeded companies (db/seed.sql)
│
├── backend/                   # FastAPI app, routes under /api
│   ├── main.py
│   ├── db.py                  # connection pool
│   ├── routers/
│   │   ├── stocks.py
│   │   ├── screen.py
│   │   ├── prices.py
│   │   ├── portfolio.py
│   │   └── breeze_auth.py     # session-capture callback (deploy-time addition)
│   ├── services/
│   │   └── returns.py         # CAGR, drawdown, etc. (pure functions)
│   └── requirements.txt
│
├── frontend/                  # Vite + React + react-router (static SPA - D10)
│   ├── src/
│   │   ├── main.tsx / App.tsx
│   │   ├── api.ts
│   │   └── pages/
│   │       ├── Screener.tsx
│   │       ├── Portfolio.tsx
│   │       └── StockDetail.tsx
│   └── vite.config.ts
│
├── db/
│   ├── schema.sql             # from 05_SCHEMA_AND_API.md
│   └── seed.sql                # companies + default user (D9)
│
├── docker-compose.yml         # local dev only (postgres + backend)
└── README.md                  # incl. the guardrail statement
```

## Deployment (v1)

Native processes on the user's existing Azure VM, not Docker — the VM's real
memory budget (848MB total) ruled that out; see `06_DECISIONS.md` D10 for the
full reasoning. Postgres via apt, the backend as a `systemctl --user` service,
the frontend as a static build served by the VM's existing Caddy reverse
proxy (which also fronts another app on the same box). The pipeline runs via
cron calling the job scripts (`pipeline/run_job.sh`, `pipeline/crontab.example`).
Docker Compose (`docker-compose.yml`) remains the local dev setup.
