# Roadmap

## v1 build order (milestones)

Build in this order so each step produces something testable and nothing blocks on
the fragile bits.

**M0 — Skeleton & DB.**
- Repo layout (`01_ARCHITECTURE.md`), `docker-compose` with Postgres + FastAPI.
- Apply `schema.sql` (`05_SCHEMA_AND_API.md`). Seed a few dozen companies by hand.
- FastAPI health check + DB connection.
*Done when:* API runs, DB has schema + a handful of `companies`.

**M1 — Prices pipeline (Breeze).**
- `breeze_client.py`: get auth working end-to-end (the session flow is the risk —
  do this first, isolated).
- `fetch_prices` job with incremental + backfill modes. Build the symbol→breeze_code
  map.
- Backfill history for the seeded companies.
*Done when:* `daily_prices` has real multi-year history for the seed set.

**M2 — Returns + price API + chart.**
- `services/returns.py` (CAGR, total return, drawdown, best/worst year) + unit tests.
- `GET /prices/{symbol}` and `/prices/{symbol}/returns`.
- Minimal Next.js stock page with a price chart + return stats.
*Done when:* you can open a stock and see its price history and returns. **This is
already a useful tool.**

**M3 — Fundamentals pipeline (the fragile one).**
- `fundamentals_source.py` wrapper + normalization into `fundamentals`.
- `fetch_fundamentals` job with per-symbol isolation + failure logging.
- `GET /stocks/{symbol}` and `/stocks/{symbol}/fundamentals`.
- Show ratios on the stock page.
*Done when:* stock page shows core ratios "as of" a date.

**M4 — Screener (View 1).**
- `GET /screen` with the filter/sort params.
- Next.js screener table: filter, sort, click through to stock page.
*Done when:* you can filter the universe on ratios and pick candidates.

**M5 — AI narrative (Option A).**
- `services/ai_analysis.py`: prompt build (`04_AI_FEATURE.md`) + Anthropic call +
  `analysis_cache`.
- `GET /analysis/{symbol}`.
- "AI analysis" card on the stock page with as-of date + disclaimer.
*Done when:* each stock shows a grounded plain-English narrative.

**M6 — Portfolio (manual).**
- `holdings` CRUD endpoints + Next.js portfolio page (add/edit/delete).
- Per-holding + total returns vs. latest close; `account` tag for multiple demats.
*Done when:* you can hand-enter holdings and see live-ish returns.

**M7 — Polish & ship.**
- README with the guardrail statement + "not investment advice."
- Scheduler wired (cron) for the three jobs.
- Staleness/"as of" surfaced in UI; basic error states.
- Deploy on the Azure VM.
*Done when:* it runs unattended and you actually use it.

**Suggested critical path:** M0 → M1 → M2 gets you a genuinely useful thing fast.
M3/M4 add the picking side. M5 adds the AI. M6 adds portfolio. Ship after M7.

---

## Deferred (v2+)

Parked deliberately. Each has a trigger for when it's worth doing.

| Item | Trigger to revisit |
|---|---|
| **Mutual funds** (tracking, then analysis) | After stocks solid; need an MF/NAV data source. |
| **Intraday prices** | If you want intraday analysis — *this* is when ClickHouse earns its place. |
| **ClickHouse OLAP layer** | Intraday, or a market-wide backtester over the full universe. |
| **AI chat about a stock** (Option B) | After narrative (A) proves useful. |
| **AI scoring/comparison** (Option C) | Only if kept transparent/descriptive (guardrail). |
| **AI pipeline normalization** (Option D) | If scraped fundamentals are too messy to use raw. |
| **Dividend-adjusted returns** | If price source provides adjusted closes. |
| **Peer / sector comparison** | Needs reliable fundamentals coverage across peers. |
| **Breeze holdings auto-import** | As optional convenience atop manual entry (not a dependency). |
| **Real auth / multi-user** | If sharing beyond yourself. |
| **Observability (Prometheus/Grafana)** | If it becomes a real service you operate. |

---

## What "v1 success" looks like

You open the app, filter NSE stocks on a couple of ratios, click one, read its
fundamentals + an AI-written explanation + its 5-year return profile, and separately
track your own holdings across your demat accounts with current returns — all on free
data, running unattended on your VM. Useful to you first; a clean portfolio piece
second.
