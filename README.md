# StockLens

A personal stock-evaluation tool for Indian (NSE) equities: screen stocks on
their fundamentals, chart historical price returns (CAGR, drawdown, "what if
I'd invested ₹X"), and manually track holdings across demat accounts.

> **Not investment advice.** This tool describes and explains data — it never
> recommends buying or selling, and it never predicts returns. Past growth does
> not predict future performance. Data is for research/educational use.

## Status

M0–M5 are built and verified against live data (real Breeze price history,
real Yahoo Finance fundamentals) — see [`07_ROADMAP.md`](07_ROADMAP.md) for
what each milestone covers. Only M6 (cron wiring done; actual VM deploy still
pending) is left. Numbered docs (`00`–`07`, `04` removed when the AI feature
was cut) are the full v1 spec — start with [`00_OVERVIEW.md`](00_OVERVIEW.md).

## Stack

- **Backend:** Python / FastAPI (routes under `/api`)
- **Database:** PostgreSQL
- **Frontend:** Vite + React + react-router (static SPA, no Node.js server needed in prod — see `06_DECISIONS.md` D10)
- **Prices:** ICICI Direct Breeze API (`breeze-connect`) — see [`pipeline/README.md`](pipeline/README.md)
- **Fundamentals:** Yahoo Finance (`yfinance`) — see [`06_DECISIONS.md`](06_DECISIONS.md) D8
- **Deploy:** native processes on a small Azure VPS (not Docker — see D10), pipeline jobs via cron

## Running locally

```
docker compose up --build
curl localhost:8000/api/health   # {"status":"ok","companies":30}
```

Postgres schema (`db/schema.sql`) and seed companies (`db/seed.sql`) load
automatically on first boot via Postgres's `docker-entrypoint-initdb.d`.

Frontend:
```
cd frontend
npm install
cp .env.local.example .env.local
npm run dev   # localhost:3000
```

Pipeline (prices + fundamentals jobs) needs its own setup — Breeze
credentials, a venv, and cron wiring — see
[`pipeline/README.md`](pipeline/README.md).
