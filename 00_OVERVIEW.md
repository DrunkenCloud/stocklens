# StockLens — Project Overview (v1 Spec)

> A personal stock-evaluation tool: research Indian (NSE) stocks through their
> fundamentals and price history, and track your own holdings by hand. Built on
> FastAPI + PostgreSQL + a Vite/React frontend, with a small data pipeline
> pulling prices from the ICICI Direct **Breeze API** and fundamentals from a
> free source.

*(StockLens is a working name — rename freely.)*

---

## What this is

One app, three surfaces that link together:

1. **Screener + per-stock detail (View 1 — the heart of it).**
   Evaluate and pick stocks. Look at fundamentals (P/E, P/B, revenue & earnings
   growth, debt-to-equity, ROE, margins, dividend history), filter/rank across
   the universe to surface candidates.

2. **Historical returns (View 2).**
   For any stock, chart daily price history and compute the numbers an investor
   cares about: total return over N years, CAGR, max drawdown, best/worst years,
   "if I'd invested ₹X on date D, what's it worth now."

3. **Portfolio (manual).**
   Users enter their own holdings by hand (stocks; MFs deferred to a later
   version). Cost basis, quantity, buy date. Returns computed against latest
   price. Manual entry (not broker-pulled) so it works across multiple demat
   accounts and for any user, not just one ICICI account.

The three link naturally: screen in View 1 → open a stock → see its return
profile (View 2) → optionally add it to your portfolio.

---

## Scope decisions already made (and why)

These were settled during planning. Recorded here so they don't get re-litigated
mid-build.

| Decision | Choice | Why |
|---|---|---|
| Market | **NSE (India) only** | Focus; matches user's interest. |
| Price granularity | **Daily OHLCV** (intraday deferred) | Simpler; enough for investing-horizon analysis. |
| Database | **PostgreSQL only** | At daily granularity the whole NSE ≈ ~10M rows over 20yr — comfortably Postgres-sized. ClickHouse would be forced/résumé-driven here; deliberately excluded. See `06_DECISIONS.md`. |
| Holdings | **Manual entry** | User has 3 demat accounts; Breeze sees only one. Manual works for everyone and all accounts. |
| Mutual funds | **Deferred to v2** | Stocks first; MF data is a separate sourcing problem. |
| Price/portfolio data | **Breeze API** (prices only, not holdings) | Free with user's ICICI account; strong at market data. Repositioned to its actual strength. |
| Fundamentals data | **Separate free source** | Breeze does NOT provide fundamentals. Realistic free options are constrained — see `02_DATA_SOURCES.md`. |
| AI narrative feature | **Cut from v1** | No Anthropic API budget/key. Ratios + returns speak for themselves; revisit if that changes — see `06_DECISIONS.md` D5. |

---

## The guardrail (non-negotiable)

The tool **describes and explains** data. It does **not** tell people what to buy.

- Ratios and historical returns are descriptive facts.
- Past growth does **not** predict future returns.
- No feature emits a buy/sell signal or a "score" dressed up as advice.
- State this plainly in the app UI and the README.

This is not just ethics theatre: it keeps the scope honest, avoids implying the
tool is a financial advisor (it isn't), and reads as mature to anyone reviewing
the project.

---

## Tech stack

- **Backend:** Python, FastAPI (routes under `/api`)
- **DB:** PostgreSQL
- **Frontend:** Vite + React + react-router (TypeScript), static SPA — switched
  from an original Next.js choice once every page went client-side; see
  `06_DECISIONS.md` D10
- **Data pipeline:** Python scripts / scheduled jobs (see `03_PIPELINE.md`)
- **Prices:** `breeze-connect` (ICICI Direct Breeze API)
- **Fundamentals:** free scraper/API (see `02_DATA_SOURCES.md`)
- **Deploy:** user's existing Azure VM — native processes (Postgres, backend,
  Caddy), not Docker; the VM's real memory budget (848MB) ruled that out —
  see `06_DECISIONS.md` D10

All within the user's existing skill set (FastAPI, Postgres, React, Docker for local dev).

---

## File map for this spec

| File | Contents |
|---|---|
| `00_OVERVIEW.md` | This file. The what and why. |
| `01_ARCHITECTURE.md` | System diagram, components, data flow, repo layout. |
| `02_DATA_SOURCES.md` | Breeze + fundamentals: what's realistic with free data, honestly. |
| `03_PIPELINE.md` | Ingestion jobs, scheduling, the Breeze auth flow. |
| `05_SCHEMA_AND_API.md` | Postgres schema + FastAPI endpoint list + return formulas. |
| `06_DECISIONS.md` | Rationale log, incl. why ClickHouse was excluded and where it *would* fit. |
| `07_ROADMAP.md` | v1 build order (milestones) + what's deferred to v2+. |

---

## v1 done-definition (one line)

A user can browse NSE stocks, open one to see its fundamentals + a price/return
chart, screen the universe on basic criteria, and manually track a portfolio
with live-ish returns — all on free data.
