# Hands-off insights: prices without login, indexes, tax calendar, movers, daily email

## Intent

The user is a hands-off investor. They want StockLens to keep itself current without them opening it or
logging in to ICICI every day, to show a few insights that matter to someone who does not trade often,
and to email them a short daily report. Approved in conversation on 2026-11-16.

Goals:
- Stock/ETF prices update every trading day with no ICICI login.
- Compare the portfolio with major Indian indexes, including "XIRR if the same money had gone into the index".
- Tax calendar: when each lot turns long-term, and this financial year's gains against the ₹1.25L exemption.
- Month movers and drop from peak on the Portfolio page.
- A daily email after market close.

Non-goals: limit/concentration banners, filings/news, buy/sell signals (user declined all three).
Anti-goals: anything that tells the user to buy, sell or wait (root rule 1); storing ICICI credentials to
automate login; new infrastructure beyond Postgres + systemd timers; LLM calls.

## Approaches considered

- Prices without login: (a) Yahoo Finance fallback, already a dependency for fundamentals; (b) NSE/BSE
  bhavcopy files; (c) scripted ICICI login with stored password + TOTP. Picked (a): reuses the existing
  source, covers NSE, BSE-only and ETFs (verified live), handles intraday. (c) rejected for security.
- Index data: (a) Yahoo price indexes; (b) index-fund NAVs from `mf_nav` (include dividends, minus fees, but
  only exist for held funds and give no Sensex). Picked (a); UI states that price indexes leave out
  dividends (~1–1.5%/yr).
- Report data: (a) report job calls the backend's HTTP API on 127.0.0.1:8000; (b) duplicate the SQL in the
  pipeline; (c) send email from the backend. Picked (a): email and site always agree, the pipeline still
  never shares a process with the API, and the backend never imports pipeline code.

## Design

### 1. Yahoo fallback for prices
- `pipeline/yahoo_prices.py`: daily bars from `yf.Ticker(t).history(start=..., auto_adjust=False)` using
  `Close` (split-adjusted, not dividend-adjusted, matching Breeze). Ticker from
  `fundamentals_source.yahoo_tickers(symbol, exchange, bse_code)`; first ticker that returns rows wins.
- `fetch_prices`: if `get_client()` raises `SessionExpired`, fetch every active company from Yahoo with the
  same incremental/backfill dates and `upsert_rows`, run `adjust_splits`, exit 0 with a summary that says
  the source was Yahoo. With a valid session, behaviour is unchanged.
- `fetch_live`: without a session, one batched Yahoo request for all held symbols (1-minute bars, today),
  merged into today's `daily_prices` row exactly like the Breeze path. Market-closed check stays.
- `onboard` gets history the same way when there is no session.

### 2. Indexes
- Table `index_prices (symbol TEXT, date DATE, close NUMERIC(14,4), PRIMARY KEY (symbol, date))`.
- Fixed list in pipeline: Nifty 50 `^NSEI`, Sensex `^BSESN`, Nifty Next 50 `^NSMIDCP`, Nifty Midcap 150
  `NIFTYMIDCAP150.NS`, Nifty Smallcap 250 `NIFTYSMLCAP250.NS`, Nifty 500 `^CRSLDX`. Backfilled from
  2015 on first run, incremental after. Updated at the end of `fetch_prices` (always from Yahoo) and in
  `fetch_live` (today's level, same batch request).
- `GET /api/portfolio/benchmarks`: per index: name, last close and date, 1D/1M/1Y change %, and the
  public-market-equivalent: replay every dated stock/MF/ETF buy (-amount) and sell (+amount) as index units
  at that day's close (last close on or before the date), value the remaining units at the latest close,
  XIRR of those flows. Returned next to the portfolio's own XIRR and coverage. Pure logic in
  `backend/services/benchmark.py` with self-checks.
- Portfolio page panel "You vs indexes".

### 3. Tax calendar
- `backend/services/tax.py`: FIFO lots per (asset, broker) from the ledgers; sells consume oldest lots first.
- Classes (Indian rules after 23 Jul 2024):
  - equity: stocks, equity ETFs, equity-oriented funds (equity, index-equity, ELSS, aggressive/arbitrage/
    equity-savings hybrid): long-term after 12 months; ST 20%, LT 12.5% above ₹1.25L per FY.
  - listed other: gold/silver ETFs: long-term after 12 months; ST slab, LT 12.5%.
  - unlisted other: FoFs (overseas, gold, silver) and other non-debt funds: long-term after 24 months; ST
    slab, LT 12.5%.
  - debt: debt-oriented funds bought on/after 1 Apr 2023 are always short-term at slab.
- Long-term date = buy date + 12 (or 24) months + 1 day.
- `GET /api/tax`: current FY (Apr–Mar); realised ST/LT gains this FY per class (FIFO); unrealised ST/LT per
  class; equity LTCG exemption used/remaining; lots turning long-term in the next 90 days; all open lots;
  undated lots listed separately as "purchase date unknown". Facts only, no "wait to sell" wording.
- New `/tax/` page (nav item "Tax"): upcoming first, then FY summary, then all lots.

### 4. Month movers and drop from peak
- Movers: per holding, month-to-date change = value now − value at the last close before the month −
  buys + sells this month. Top gainers and losers by rupees.
- Drop from peak: time-weighted index from the dated growth series (daily return net of that day's flows);
  current drop from its peak, peak date, worst drop. Coverage note for undated holdings.
- Endpoint `GET /api/portfolio/insights`; panels on the Portfolio page.

### 5. Daily email
- `pipeline/jobs/daily_report.py`: reads `/api/status`, `/api/portfolio`, `/api/portfolio/benchmarks`,
  `/api/tax`, `/api/portfolio/insights` from `http://127.0.0.1:8000` (stdlib `urllib`), sends HTML + plain
  text via Gmail SMTP SSL from `GMAIL` to `GMAIL` with `GMAIL_PASSWORD` (spaces stripped).
- Skips (exit 75) when there are no prices for today (holiday) or a report already went out today.
- Content: value, day change, index day changes, top 3 up/down today, lots turning long-term in the next
  14 days, month movers; link to the site.
- Timer `stocklens-report.timer` Mon–Fri 19:45 Asia/Kolkata, `Persistent=true`.
- `GMAIL`, `GMAIL_PASSWORD` added to the secrets list; already copied into the VM `.env`.

## Left to the builder
Exact layouts within the existing design system, email styling, Yahoo error handling details, and how
index units handle a sell larger than the index position (allowed to go negative).
