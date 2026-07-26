# Decisions Log

Why the project is shaped the way it is. Recorded so choices aren't re-argued
mid-build, and so the reasoning is defensible if someone (an interviewer, a future
you) asks.

---

## D1 — PostgreSQL only; ClickHouse deliberately excluded (for now)

**Decision:** store everything in Postgres. Do not add ClickHouse in v1.

**Why:** at daily granularity, the whole NSE (~2,000 stocks × ~250 trading days ×
~20 years) is roughly **10 million rows** in `daily_prices`. Postgres handles that
comfortably with a `(symbol, date)` index. ClickHouse's advantage shows up in the
hundreds-of-millions-to-billions range (i.e. *intraday* data), which v1 doesn't use.

**Why not "ClickHouse as a cache":** caching = fast key lookups of hot data, which is
**Redis's** job. ClickHouse is a columnar OLAP scan/aggregate engine, not a lookup
cache. Using it as a cache is the wrong tool and doesn't survive the interview
question "why not Redis?". Also, the daily data is already fast from Postgres —
nothing to cache.

**Where ClickHouse *would* honestly fit** (if ever added): as the **OLAP engine for
cross-universe historical analytics** — e.g. a market-wide screener/backtester:
"across all stocks, every day for 20 years, find every instance below the 200-day MA
with rising volume." That scans tens of millions of rows with windowed aggregates —
genuinely ClickHouse-shaped. It becomes clearly justified if the project goes
**intraday** (row counts explode). Until then, adding it is résumé-driven design,
which is worse than not having it.

**If ClickHouse is wanted for résumé reasons:** do it as a *separate* small project
where it's obviously right — e.g. API telemetry/log analytics (also closer to how
production shops actually use it) — rather than bending this tool to fit it.

---

## D2 — Manual holdings, not broker-pulled

**Decision:** users type in their own holdings (stocks) with an optional account
label.

**Why:** the user has 3 demat accounts; Breeze sees only the ICICI one, so an
auto-pull would be incomplete anyway. Manual entry works across all accounts, works
for *any* user (not just ICICI customers), sidesteps the fiddly Breeze
session-auth for the portfolio path, and makes the tool multi-user by default.

**Cost:** users do data entry. Acceptable for a personal/portfolio tool; can add
optional Breeze holdings-import later as a convenience, not a dependency.

---

## D3 — Breeze kept, but for prices only

**Decision:** Breeze feeds `daily_prices` and latest price. Not holdings (D2), not
fundamentals (it has none).

**Why:** it's free with the user's account, strong at market data, and the user
explicitly wants to use it. Repositioning it to prices puts it where it's actually
good and where it's a hard dependency worth the auth hassle.

---

## D4 — Fundamentals scope limited to "what free data reliably gives"

**Decision:** v1 View 1 = core ratios + a few years of key financials + price
history + AI narrative. No promise of deep cash-flow-statement detail or peer comps.

**Why:** no clean free official fundamentals API for India exists; scraper/free-tier
sources give core ratios reliably-ish but deep detail is flaky
(`02_DATA_SOURCES.md`). Better to ship a solid "comprehensive-enough" tool than to
promise depth the data can't back.

---

## D5 — AI feature cut from v1 (superseded — was: narrative summary, Option A)

**Original decision:** the AI would write a plain-English interpretation of a
stock's fundamentals (Option A). Chat (B), scoring (C), and pipeline-normalization
(D) were deferred.

**Superseded:** no Anthropic API key/budget available, so the whole AI feature —
not just A — is cut from v1. Ratios, trends, and return stats are shown as plain
data; the "describe, don't advise" guardrail (D6) still applies to how they're
presented (no computed "score", no buy/sell language), it's just enforced in UI
copy instead of an AI system prompt now.

**Why this is fine:** the AI narrative was additive polish on top of already-solid
data (D4), not load-bearing for the tool's usefulness — View 2 (returns) and the
screener stand on their own. Revisit if API budget becomes available; the shelved
design (prompt, caching strategy, endpoint) lived in `04_AI_FEATURE.md` before it
was removed — recoverable from git history if picked back up.

---

## D6 — "Describe, don't advise" guardrail

**Decision:** the tool presents and explains data; it never recommends
buying/selling and never predicts returns. Enforced in UI copy, stated in the
README. (Originally also enforced in an AI system prompt — moot now that the AI
feature is cut, D5 — but the guardrail applies to the whole tool regardless.)

**Why:** keeps scope honest, avoids posing as a financial advisor (it isn't one),
and reads as mature. Past growth doesn't predict future returns and the tool
should say so.

---

## D7 — No Airflow / Kafka / heavy orchestration in v1

**Decision:** cron or a tiny Python scheduler for the pipeline.

**Why:** three low-frequency jobs at this data scale don't need a distributed
scheduler or a message bus. Adding them would be over-engineering — same principle as
D1. Revisit only if the pipeline grows many interdependent jobs or moves intraday.

---

## D8 — Fundamentals source: `yfinance` (Yahoo Finance)

**Decision:** M3's `fetch_fundamentals` job pulls fundamentals via the
`yfinance` Python library (`Ticker(f"{symbol}.NS").info` + `.financials` for
multi-year revenue), not a hand-rolled Screener.in/NSE HTML scraper.

**Why:** `02_DATA_SOURCES.md` deliberately left the exact source open ("pick
one primary, keep a fallback"). A hand-written scraper breaks on every markup
change to the source site; `yfinance` is an actively-maintained community
library that already absorbs that churn, and it covers NSE directly via the
`.NS` ticker suffix - no separate per-symbol code mapping needed (unlike
Breeze, D3). Still free-tier-fragile in the sense `02_DATA_SOURCES.md` warns
about (an unofficial API wrapper, not a stable contract), just fragile in a
place a library maintainer absorbs instead of us.

**Field-scaling gotcha found by testing live, not assumed:** `yfinance`'s
`debtToEquity` comes back pre-multiplied by 100 (Yahoo convention) while
`returnOnEquity`/`operatingMargins`/`revenueGrowth` come back as plain
fractions, and `dividendYield` is already a plain percent - four different
scalings across five fields. Confirmed against real tickers (TCS/ITC's
near-zero real-world debt only matches the schema's plain-ratio convention
once `debtToEquity` is divided by 100) before trusting it - same lesson as
the Breeze `stock_code` surprise in M1 (D3). See
`pipeline/fundamentals_source.py`'s docstring for the verified mapping.

---

## D9 — Single fixed default user, no auth in v1

**Decision:** `holdings.user_id` points at one seeded row
(`00000000-0000-0000-0000-000000000001`, `db/seed.sql`). The `/portfolio`
endpoints operate against that fixed id directly - no login, no signup, no
session/token.

**Why:** v1 is explicitly single-user (`07_ROADMAP.md` defers "real auth /
multi-user" to v2, triggered only "if sharing beyond yourself"). The `users`
table and `holdings.user_id` foreign key already exist to keep that seam open
(`05_SCHEMA_AND_API.md`'s own comment: "even single-user, keep the seam for
multi-user") - a fixed id is the minimum that honors the seam without
building auth nobody needs yet.

---

## D10 — Frontend: Vite + React (not Next.js); deploy: native processes (not Docker)

**Decision:** switched the frontend from Next.js (`00_OVERVIEW.md`'s original
choice) to a Vite + React + react-router SPA. Deployment runs native
processes on the VPS (Postgres via apt, backend via a `systemctl --user`
service) instead of Docker Compose in production; Docker stays for local dev
only. Backend routes moved under an `/api` prefix in both dev and prod.

**Why:** by M6, every frontend page had already become client-side-fetching
(screener/portfolio always were; the stock detail page was converted for
this deploy). Next.js's App Router (SSR, static-export dynamic-route
constraints, Suspense-for-`useSearchParams`) stopped buying anything once
nothing server-renders - it was just acting as an elaborate static site
generator for what is actually a plain SPA. Vite removes that friction and
ships a smaller bundle (77KB gzipped vs. Next's ~100KB+ shared JS). Neither
choice changes server RAM usage (both end as static files served by Caddy,
zero persistent Node.js process) - the win is code simplicity, not the
memory budget below.

The deploy target (an existing Azure VPS, already running Caddy + a "memos"
app) has **848MB RAM, 394MB available** - confirmed by SSH before deciding
anything. Docker was installed but unused; running Postgres + backend +
frontend each in a container adds real per-container overhead on a box this
tight, for no benefit once the frontend needs no runtime at all. Native
Postgres + a lightweight Python venv backend fits comfortably; the `/api`
prefix lets Caddy split static files from the backend cleanly via a single
reverse-proxy rule.

Also: no passwordless sudo on the VPS, so the one-time root setup (installing
`postgresql`, creating the DB role, `loginctl enable-linger`) is a short
script the user runs themselves - not something automatable over a
non-interactive SSH session, and not something to ask for a sudo password to
work around.

---

## Summary table

| # | Decision | One-line reason |
|---|---|---|
| D1 | Postgres only, no ClickHouse | 10M daily rows fit Postgres; CH would be forced |
| D2 | Manual holdings | 3 demat accounts; works for any user |
| D3 | Breeze = prices only | Free, strong at market data, its real strength |
| D4 | Fundamentals scoped to free-reliable | No clean free deep-fundamentals source |
| D5 | AI feature cut from v1 | No Anthropic API key/budget available |
| D6 | Describe-don't-advise guardrail | Honest scope, not a financial advisor |
| D7 | cron, no Airflow/Kafka | Right-sized for 3 low-freq jobs |
| D8 | Fundamentals via yfinance | Community-maintained, covers NSE, no code mapping needed |
| D9 | Single fixed default user, no auth | v1 is single-user; schema seam kept for v2 |
| D10 | Vite/React (not Next.js); native deploy (not Docker) | Every page went client-side; VPS has 848MB RAM |
