# Data Sources

Two sources feed one database. They cover different things and have very different
reliability. Be honest about the second one — it bounds what View 1 can promise.

---

## 1. Prices + market data → Breeze API (ICICI Direct)

**What it is:** the official ICICI Direct market/trading API. Free to any ICICI
Direct account holder — ICICI charges nothing to connect, create apps, or access
historical data; they monetize only executed trades. For a read-only analytics
tool, cost is ₹0.

**Python client:** `breeze-connect` (official). `pip install breeze-connect`.

**What we use it for:**
- **Daily historical OHLCV per stock** → feeds `daily_prices` (View 2 returns/charts).
  The SDK exposes long history (documented up to ~10 years of OHLCV, down to
  1-second/1-minute intervals — we only need `1day` for v1, but the headroom means
  going intraday later needs no source change).
- **Latest/last price** for portfolio return calc and screener "current price".

**What we deliberately do NOT use it for:**
- **Holdings** — even though Breeze exposes `get_demat_holdings`, the user has 3
  demat accounts and Breeze sees only the ICICI one. Holdings are manual instead
  (works for all accounts + any user). See `00_OVERVIEW.md`.
- **Fundamentals** — Breeze is market-data only. It has no P/E, revenue, margins,
  cash flow, etc. That's a different source (below).

**Auth caveat (budget an hour):** Breeze uses a session-based flow, not a simple
static key. You register an app (get `api_key` + `api_secret`), then per session
generate an `api_session` token via login, then instantiate the client. It's mildly
fiddly; there are community autologin helpers if the manual flow annoys you. Wrap
all of this in `pipeline/breeze_client.py` so the rest of the code never sees it.
See `03_PIPELINE.md` for the flow.

**Regulatory note to verify, don't assume:** under SEBI's newer framework, a static
IP is being made mandatory for API-based *trading* (order execution) from
1 Apr 2026. This tool is read-only (no order placement), so it most likely isn't
affected — but the boundary isn't crystal-clear from ICICI's marketing pages.
**Verify against current Breeze docs/FAQ before relying on it**, and definitely
before ever adding any order features.

---

## 2. Fundamentals → a separate free source (the constrained part)

**The honest situation:** there is no clean, official, free API for Indian equity
fundamentals. This is the single biggest data risk in the project, so scope View 1
to what's reliably gettable rather than promising terminal-grade depth.

**Realistic free routes (pick one primary, keep a fallback):**

- **Scraper-based libraries around Screener.in / NSE.** Community Python projects
  scrape fundamentals. They *work* but are **fragile** — they break when the source
  site changes markup. Good coverage when working; needs occasional maintenance.
- **Free-tier fundamentals APIs.** Some providers offer limited free calls/coverage.
  More stable than scraping but rate/coverage limited.
- **NSE filings / bhavcopy.** Official, free, stable for *some* data (corporate
  filings, EOD dumps) but not a tidy ratio feed — more parsing work.

**v1 picked `yfinance`** (a "free-tier API"-shaped middle ground: an unofficial
wrapper, not hand-rolled HTML scraping, and a community absorbs the breakage
instead of us). Verified live against all 30 seeded companies. See
`06_DECISIONS.md` D8 for why and the field-scaling gotchas found while
verifying it.

**What's realistically available for free (tier honestly):**

| Data | Free availability | Notes |
|---|---|---|
| Daily OHLCV / price history | ✅ Solid (Breeze) | Not a fundamentals problem. |
| Core ratios (P/E, P/B, ROE, D/E, div yield) | 🟡 Gettable | Via scraper/free API; the backbone of View 1. |
| Revenue / earnings, few-year trend | 🟡 Gettable | Enough for growth calcs. |
| Full multi-year cash-flow-statement detail | 🔴 Flaky | Inconsistent free coverage. Don't promise it in v1. |
| Peer / sector comparison sets | 🔴 Flaky | Nice-to-have; defer. |

**Consequence for scope:** v1 View 1 = **core ratios + a few years of key financials
+ price history**. That is already a genuinely useful, "comprehensive *enough*"
stock-evaluation tool. Deep statement-level analysis and peer comps are v2, gated
on finding a reliable source.

---

## Source responsibilities summary

| Concern | Source | Reliability | Table |
|---|---|---|---|
| Daily prices / history | Breeze | High | `daily_prices` |
| Latest price | Breeze | High | (read from `daily_prices`) |
| Core fundamentals | Free scraper/API | Medium (fragile) | `fundamentals` |
| Holdings | **Manual user entry** | N/A | `holdings` |

## Licensing / ToS reminder

- Breeze: fine for personal use under your account; don't redistribute raw data.
- Scraped fundamentals: respect the source site's ToS and rate limits; cache
  locally, don't hammer. Add a "data for research/educational use, not advice"
  line in the UI (also serves the guardrail).
