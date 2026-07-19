# StockLens

A personal stock-evaluation tool for Indian (NSE) equities: browse and screen
stocks on their fundamentals, chart historical price returns (CAGR, drawdown,
"what if I'd invested ₹X"), and manually track holdings across demat accounts.

> **Not investment advice.** This tool describes and explains data — it never
> recommends buying or selling, and it never predicts returns. Past growth does
> not predict future performance. Data is for research/educational use.

## Status

Building per [`07_ROADMAP.md`](07_ROADMAP.md). M0 (skeleton + DB) and M1
(Breeze auth + prices job, not yet tested against a live account) are done.
Numbered docs (`00`–`07`, `04` removed) are the full v1 spec — start with
[`00_OVERVIEW.md`](00_OVERVIEW.md).

## Stack

- **Backend:** Python / FastAPI
- **Database:** PostgreSQL
- **Frontend:** Next.js (TypeScript)
- **Prices:** ICICI Direct Breeze API (`breeze-connect`)
- **Fundamentals:** free scraper/API (see [`02_DATA_SOURCES.md`](02_DATA_SOURCES.md))
- **Deploy:** Docker Compose on an Azure VM

## Running locally

```
docker compose up --build
curl localhost:8000/health   # {"status":"ok","companies":30}
```

Postgres schema (`db/schema.sql`) and seed companies (`db/seed.sql`) load
automatically on first boot via Postgres's `docker-entrypoint-initdb.d`.
