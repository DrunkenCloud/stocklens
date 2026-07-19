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
                          Anthropic API ◀─────│    FastAPI       │
                          (AI narrative)      │   (backend)      │
                                              │                  │
                                              │  /stocks         │
                                              │  /screen         │
                                              │  /prices         │
                                              │  /analysis (AI)  │
                                              │  /portfolio      │
                                              └─────────────────┘
                                                       ▲
                                                       │ HTTP/JSON
                                              ┌─────────────────┐
                                              │   Next.js UI     │
                                              │                  │
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
Single source of truth for the app. Five tables (`04`/`05`). The pipeline writes;
FastAPI reads (plus writes for user-entered holdings). No second database — see
`06_DECISIONS.md` on why ClickHouse is out.

**FastAPI backend.**
Read API over the stored data + the AI-analysis endpoint (which calls Anthropic on
demand and can cache the result). Also handles manual holdings CRUD. Return
calculations (CAGR, drawdown, etc.) live here as pure functions over `daily_prices`.

**Anthropic API.**
Called by the `/analysis` endpoint to turn a stock's structured fundamentals into a
plain-English narrative. Not in the pipeline for v1 (though it *could* help clean
messy fundamentals later — Option D in `04_AI_FEATURE.md`).

**Next.js frontend.**
Three surfaces: screener (filter/rank table), stock detail (fundamentals + AI
narrative + price chart), portfolio (manual entry + returns). Talks only to FastAPI.

## Data flow, end to end

1. **Ingest (offline, scheduled):** pipeline pulls daily prices (Breeze) and
   fundamentals (free source) → normalizes → upserts into Postgres.
2. **Browse/screen (request):** UI → `GET /screen?filters` → FastAPI queries
   `fundamentals` + latest `daily_prices` → ranked list back.
3. **Stock detail (request):** UI → `GET /stocks/{symbol}` (fundamentals + price
   series) and `GET /analysis/{symbol}` (AI narrative, cached).
4. **Returns (request):** UI → `GET /prices/{symbol}/returns?from=...&amount=...`
   → FastAPI computes CAGR / total return / drawdown from `daily_prices`.
5. **Portfolio (request):** UI → `POST/GET /portfolio` → holdings stored in
   Postgres; returns computed against latest price per symbol.

## Suggested repo layout

```
stocklens/
├── pipeline/                  # standalone ingestion (not imported by API)
│   ├── breeze_client.py       # auth flow + price fetch wrapper
│   ├── fundamentals_source.py # scraper/API wrapper + normalization
│   ├── jobs/
│   │   ├── refresh_universe.py
│   │   ├── fetch_prices.py
│   │   └── fetch_fundamentals.py
│   ├── schedule.py            # cron-like runner
│   └── README.md
│
├── backend/                   # FastAPI app
│   ├── main.py
│   ├── db.py                  # connection / session
│   ├── models.py              # ORM models (or SQL + pydantic)
│   ├── routers/
│   │   ├── stocks.py
│   │   ├── screen.py
│   │   ├── prices.py
│   │   ├── analysis.py        # Anthropic call lives here
│   │   └── portfolio.py
│   ├── services/
│   │   ├── returns.py         # CAGR, drawdown, etc. (pure functions)
│   │   └── ai_analysis.py     # prompt build + Anthropic call + cache
│   └── requirements.txt
│
├── frontend/                  # Next.js
│   ├── app/ (or pages/)
│   │   ├── screener/
│   │   ├── stock/[symbol]/
│   │   └── portfolio/
│   └── components/
│
├── db/
│   ├── schema.sql             # from 05_SCHEMA_AND_API.md
│   └── migrations/
│
├── docker-compose.yml         # postgres + backend (+ frontend)
└── README.md                  # incl. the guardrail statement
```

## Deployment (v1)

`docker-compose` with Postgres + FastAPI (and optionally the Next.js build) on the
user's existing Azure VM. The pipeline can run as a cron job on the same box calling
the job scripts. Nothing here needs managed cloud services for v1.
