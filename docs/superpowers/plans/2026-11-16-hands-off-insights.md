# Hands-off insights Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Prices without ICICI login, index comparison, tax calendar, month movers/drop from peak, daily email.

**Architecture:** Pipeline jobs fall back to Yahoo when `get_client()` raises `SessionExpired`; indexes live in a
new `index_prices` table. Pure logic in `backend/services/{benchmark,tax,insights}.py`, exposed by routes in
`backend/routers/portfolio.py` and a new `backend/routers/tax.py`. The email job reads the backend's HTTP API.

**Tech Stack:** Python 3.10 (VM), FastAPI, psycopg3, yfinance, Next.js 16 static export, TanStack Query.

**Spec:** `docs/superpowers/specs/2026-11-16-hands-off-insights-design.md`

## Global Constraints

- No code comments or docstrings. Python 3.10 syntax only (no `except*`, no 3.11 typing).
- Describe, don't advise: no copy that says buy, sell, hold or wait.
- No new dependencies: yfinance and pandas are already in `pipeline/requirements.txt`; email uses stdlib `smtplib`, HTTP uses stdlib `urllib`.
- Tests are plain-assert modules run with `python -m` (backend from `backend/`, pipeline from repo root).
- Exemption ₹1,25,000 per FY; equity ST 20%, LT 12.5%; LT after 12 months (24 for unlisted non-equity funds); debt funds bought on/after 2023-04-01 always ST.
- Indexes: `^NSEI` Nifty 50, `^BSESN` Sensex, `^NSMIDCP` Nifty Next 50, `NIFTYMIDCAP150.NS` Nifty Midcap 150, `NIFTYSMLCAP250.NS` Nifty Smallcap 250, `^CRSLDX` Nifty 500. Backfill from 2015-01-01.
- Email: from and to `GMAIL`, password `GMAIL_PASSWORD` with spaces removed, `smtp.gmail.com:465` SSL. Timer Mon–Fri 19:45 Asia/Kolkata.

## Review Focus

- Yahoo returns an empty frame or raises for one symbol: that symbol is a failure, the rest still load (Task 1 test `test_empty_history_gives_no_bars`).
- A sell larger than the oldest lot spans several lots, and a sell dated before any buy is impossible (ledger already rejects): FIFO must split lots (Task 3 `test_sell_spans_lots_fifo`).
- Transactions with no date: kept out of XIRR/benchmark/tax-period maths but listed as "date unknown" (Task 2 `test_undated_flows_are_skipped`, Task 3 `test_undated_lot_has_no_long_term_date`).
- Buy on a date with no index close (weekend/holiday or before history): uses the last close on or before; before history starts, the next close (Task 2 `test_flow_on_holiday_uses_previous_close`).
- Report runs on a holiday or twice in a day: skips, sends nothing (Task 5 `test_should_send`).

---

### Task 1: Yahoo fallback for daily and live prices

**Files:**
- Create: `pipeline/yahoo_prices.py`, `pipeline/test_yahoo_prices.py`
- Modify: `pipeline/jobs/fetch_prices.py` (`run`, `main`), `pipeline/jobs/fetch_live.py` (`run`, `main`)

**Interfaces:**
- Produces: `history_bars(df) -> list[dict]` (rows shaped like Breeze: `datetime` "YYYY-MM-DD HH:MM:SS", `open/high/low/close/volume`, NaN rows dropped); `daily_bars(symbol, exchange, bse_code, start: date) -> list[dict]`; `minute_bars(tickers: dict[str, str], day: date) -> dict[str, list[dict]]` (symbol → bars, one `yf.download` call, `interval="1m"`, `group_by="ticker"`).
- `fetch_prices.run(symbols=None, backfill=False) -> list[str]` keeps its signature; returns failures; prints `source: yahoo (no ICICI session)` when falling back.

- [ ] Step 1: tests in `pipeline/test_yahoo_prices.py`: `test_history_bars_shape` (DataFrame with tz-aware index 2026-11-13 → `[{"datetime": "2026-11-13 00:00:00", "open": 1.0, ..., "volume": 5}]`), `test_empty_history_gives_no_bars`, `test_nan_rows_dropped`.
- [ ] Step 2: run `pipeline/.venv/bin/python -m pipeline.test_yahoo_prices`; expect ImportError.
- [ ] Step 3: implement `pipeline/yahoo_prices.py`; tickers via `fundamentals_source.yahoo_tickers`; `history(start=..., auto_adjust=False, interval="1d")`.
- [ ] Step 4: `fetch_prices.run`: catch `SessionExpired` from `get_client()` → fetch source = Yahoo for all companies (select also `s.bse_code` via `LEFT JOIN securities s ON s.isin = c.isin`); per-symbol isolation unchanged; `adjust_splits` after. `main` no longer exits 75 for a missing session. `onboard` gets this for free; its `except SessionExpired` branch stays harmless.
- [ ] Step 5: `fetch_live.run`: without a session, `minute_bars` for all held, `day_bar` each, upsert. Market-closed skip unchanged.
- [ ] Step 6: run tests (`test_yahoo_prices`, `jobs.test_fetch_prices`, `jobs.test_fetch_live`) → all `ok`. Live check locally: `pipeline/.venv/bin/python -c "from pipeline.yahoo_prices import daily_bars; import datetime as d; print(daily_bars('BEL','NSE',None,d.date(2026,11,10))[-1])"`.

### Task 2: Indexes and "same money in the index" XIRR

**Files:**
- Create: `db/migrations/010_index_prices.sql`, `pipeline/indices.py`, `backend/services/benchmark.py`, `backend/services/test_benchmark.py`
- Modify: `pipeline/jobs/fetch_prices.py` (`main` calls `refresh_indices` after prices, any source), `pipeline/jobs/fetch_live.py` (adds index tickers to the same batch), `backend/routers/portfolio.py` (route)

**Interfaces:**
- `index_prices (symbol TEXT, date DATE, close NUMERIC(14,4) NOT NULL, PRIMARY KEY (symbol, date))`.
- `pipeline/indices.py`: `INDICES: list[tuple[str, str]]` (ticker, name) in the Global Constraints order; `refresh_indices(conn) -> None`.
- `services/benchmark.py`: `close_on(series: list[tuple[date, float]], day: date) -> float | None`; `period_changes(series, today) -> dict` keys `day_pct`, `month_pct`, `year_pct` (last close vs last close on/before today−1 trading row, −1 month, −1 year); `index_equivalent(flows: list[tuple[date|None, float]], series, today) -> dict` keys `value`, `xirr`.
- `GET /api/portfolio/benchmarks` → `{"portfolio": {"xirr", "value", "coverage_pct"}, "indices": [{"symbol","name","close","date","day_pct","month_pct","year_pct","xirr","value"}]}`; flows from `load_ledger(conn, "all")` (buy negative, sell positive amount), skipping undated.

- [ ] Step 1: tests: `test_flow_on_holiday_uses_previous_close`, `test_index_equivalent_matches_simple_growth` (one buy of 100 at close 10, today close 12 → value 120, xirr ≈ 20% over exactly one year), `test_sell_removes_units`, `test_undated_flows_are_skipped`, `test_period_changes`.
- [ ] Step 2: run `cd backend && .venv/bin/python -m services.test_benchmark` → fails.
- [ ] Step 3: implement benchmark service, migration, `pipeline/indices.py` (incremental from max(date), else 2015-01-01; `yf.Ticker(t).history(auto_adjust=False)`), route.
- [ ] Step 4: tests pass; locally `db/migrate.py`, run `pipeline/.venv/bin/python -c "from pipeline.db import connect; from pipeline.indices import refresh_indices; c=connect(); refresh_indices(c)"`, curl `/api/portfolio/benchmarks`.

### Task 3: Tax calendar

**Files:**
- Create: `backend/services/tax.py`, `backend/services/test_tax.py`, `backend/routers/tax.py`
- Modify: `backend/main.py` (include router)

**Interfaces:**
- `tax_class(kind: str, asset_class: str | None, category: str | None) -> str` → one of `equity`, `listed_other`, `unlisted_other`, `debt`. Stocks → equity; ETF equity → equity, gold/silver → listed_other, debt → debt; MF: category contains "FoF"/"Fund of Funds" → unlisted_other; asset_class equity → equity; debt → debt; gold/silver → unlisted_other; hybrid with arbitrage/equity savings/aggressive/balanced advantage/dynamic asset → equity, conservative → debt, else unlisted_other; anything else unlisted_other.
- `long_term_on(buy: date, tax_cls: str) -> date | None` (None for debt bought ≥ 2023-04-01; months 12 or 24, then +1 day; clamp Feb 29).
- `fifo(txs: list[dict]) -> tuple[list[dict], list[dict]]`: input rows as `load_ledger` yields (`key`, `kind`, `units`, `amount`, `date`, `created_at`); output open lots `{key, date, units, cost}` and realised matches `{key, buy_date, sell_date, units, cost, proceeds}`.
- `fy_bounds(today) -> tuple[date, date]` (1 Apr–31 Mar).
- `tax_report(lots, realised, meta: dict[key, {"name","tax_class","price"}], today) -> dict` with `fy`, `exemption` {limit 125000, used, remaining}, `realised` and `unrealised` each `{class: {"short": x, "long": y}}`, `upcoming` (lots turning LT within 90 days, sorted by date, with `days_left`), `lots` (all open: name, broker, date, units, cost, value, gain, term `short|long|always_short|unknown`, `long_term_on`).
- `GET /api/tax` builds meta from the same queries `holding_rows` uses (latest price per asset, kind/asset_class/category).

- [ ] Step 1: tests: `test_sell_spans_lots_fifo`, `test_long_term_after_12_months_plus_a_day` (buy 2025-11-20 → 2026-11-21), `test_fof_needs_24_months`, `test_debt_after_april_2023_never_long_term`, `test_undated_lot_has_no_long_term_date`, `test_fy_bounds` (2026-11-16 → 2026-04-01..2027-03-31; 2027-02-01 same FY), `test_exemption_counts_only_equity_long_term_realised`, `test_tax_class_rules` (table of inputs).
- [ ] Step 2: run → fails. Step 3: implement. Step 4: tests pass; curl `/api/tax` locally.

### Task 4: Month movers and drop from peak

**Files:**
- Create: `backend/services/insights.py`, `backend/services/test_insights.py`
- Modify: `backend/routers/portfolio.py` (route), `backend/holdings.py` (expose a `price_history(conn, keys, since)` helper reused by growth if it shrinks code)

**Interfaces:**
- `month_movers(txs, prices: dict[key, list[(date, price)]], today) -> list[dict]` → per key `{key, change}` where change = value now − value at last close before the 1st of this month − buys + sells this month; positions opened this month start at 0.
- `drawdown(series: list[{"date","invested","value"}]) -> dict | None` → `{current_pct, peak_date, max_pct}` from a time-weighted index: day return = (value − (invested − prev_invested)) / prev_value.
- `GET /api/portfolio/insights` → `{"movers": {"up": [...5], "down": [...5]}, "drawdown": {...}, "month_start": date}`; each mover row adds `name`, `broker`, `symbol`, `kind`.

- [ ] Step 1: tests: `test_mover_excludes_new_money`, `test_new_position_this_month`, `test_drawdown_ignores_contributions` (value jumps because of a buy → no gain; then −10% → current −10%).
- [ ] Step 2–4: fail, implement, pass; curl locally.

### Task 5: Daily email

**Files:**
- Create: `pipeline/jobs/daily_report.py`, `pipeline/jobs/test_daily_report.py`, `deploy/systemd/stocklens-report.timer`

**Interfaces:**
- `should_send(status: dict, today: date, sent_today: bool) -> bool` (True only if `status["prices_as_of"] == today` and not already sent; sent = a `job_runs` row for `daily_report` with status `done` started today).
- `render(data: dict, today: date) -> tuple[str, str, str]` (subject, text, html). Subject: `StockLens · Mon 16 Nov · ₹2,63,179 (−0.6%)`. Sections: today (value, change, Nifty/Sensex day change), top 3 up / down today by rupees, turning long-term in the next 14 days, this month's top movers, link `https://investlens.duckdns.org`.
- `main()`: fetch the five endpoints from `http://127.0.0.1:8000/api`, skip with exit 75 when `should_send` is false, else send.

- [ ] Step 1: tests: `test_should_send` (holiday → False, already sent → False, normal → True), `test_render_contains_value_and_sign` (Indian formatting, `−` for losses, empty upcoming section omitted).
- [ ] Step 2–4: fail, implement, pass. Run `main` locally against the local backend with a forced send once.
- [ ] Step 5: timer `OnCalendar=Mon..Fri 19:45 Asia/Kolkata`, `Persistent=true`, `Unit=stocklens-job@daily_report.service`; deploy script picks it up from `deploy/systemd/*` (verify `deploy.sh` enables every `*.timer`).

### Task 6: Frontend

**Files:**
- Create: `frontend/src/components/portfolio/benchmarks.tsx`, `frontend/src/components/portfolio/movers.tsx`, `frontend/src/app/tax/page.tsx`
- Modify: `frontend/src/lib/types.ts`, `frontend/src/lib/queries.ts` (`useBenchmarks`, `useInsights`, `useTax`, added to the live-refresh invalidation list), `frontend/src/app/page.tsx` (panels after the growth chart), `frontend/src/components/app-shell.tsx` (nav "Tax", `ReceiptIndianRupeeIcon`)

- [ ] Benchmarks panel: rows per index: name, level, 1D/1M/1Y %, "Same money in index" value and XIRR; "Your portfolio" row first; footnote: "Price indexes, dividends not included; flows without a date left out."
- [ ] Movers panel: this month's top up/down by ₹ with links via `holdingHref`; drop from peak figure with peak date.
- [ ] Tax page: "Turning long-term soon" list, FY summary (realised/unrealised short/long per class, exemption bar), all lots table (lists under `lg`), "Purchase date unknown" group, footnote with the rules used and "slab rate" for non-equity short-term.
- [ ] Verify: `cd frontend && npx tsc --noEmit && npx eslint src && npm run build`; check in the browser against the local backend.

### Task 7: Docs, deploy, verify on the VM

- [ ] Root `CLAUDE.md`: secrets list adds `GMAIL`, `GMAIL_PASSWORD`; data flow lines for Yahoo fallback, `index_prices`, tax, insights, daily report timer; gotcha: Yahoo `auto_adjust=False` keeps prices dividend-unadjusted like Breeze. `pipeline/CLAUDE.md` job list.
- [ ] `bash deploy/deploy.sh`; on the VM run `fetch_prices` (expect Yahoo source when no session), `daily_report` once; confirm the email arrives and `/api/portfolio/benchmarks`, `/api/tax`, `/api/portfolio/insights` respond.
