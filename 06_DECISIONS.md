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
