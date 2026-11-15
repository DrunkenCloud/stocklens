# StockLens

Personal portfolio + stock research tool for one user. Holdings across ICICI
(synced automatically after the daily ICICI login), Zerodha and Groww (entered
by hand as shares + total invested), plus search over every NSE/BSE equity,
stock pages, a screener and a Data page for pipeline ops.

FastAPI (`/api`) + PostgreSQL + Next.js static export. Prices from ICICI
Breeze, fundamentals from Yahoo Finance, stock universe from ICICI's
SecurityMaster file. Hosted on an Azure VM at https://investlens.duckdns.org behind a
site-wide Caddy password. It has to run there: ICICI's API only accepts calls from the VM's IP.

Area conventions: `backend/CLAUDE.md`, `pipeline/CLAUDE.md`, `frontend/CLAUDE.md`.

## Hard rules

1. **Describe, don't advise.** Explain numbers; never recommend buy/sell or predict returns.
2. **Postgres only.** No Redis, queues, Airflow, ClickHouse. Job history lives in `job_runs`.
3. **Pipeline stays out of the API process.** The backend spawns `pipeline/run_job.sh` as a
   detached subprocess (`backend/jobs.py`); it never imports pipeline code.
4. **Secrets in env, never in git:** `BREEZE_API_KEY`, `BREEZE_API_SECRET`, `BREEZE_CALLBACK_TOKEN`,
   `DATABASE_URL`. The daily Breeze session token lives in the `breeze_session` table.
5. **No LLM calls** anywhere unless the user asks.
6. **No auth per feature.** The app is unauthenticated by design; auth would be a site-wide decision.
7. **No code comments or docstrings.** Knowledge worth keeping goes in these CLAUDE.md files.

## Data flow

- Holdings are ledgers, entered by hand for every broker (ICICI included; nothing syncs holdings):
  `stock_transactions` and `mf_transactions` hold dated buys/sells. `backend/services/ledger.py` derives
  positions (average cost, realised gains), XIRR and the invested-vs-value growth series; entries without a
  date stay in holdings but are left out of XIRR and growth (the UI says how much).
- Daily: user clicks "Log in to ICICI" → ICICI redirects to `/api/cb/<BREEZE_CALLBACK_TOKEN>` →
  token saved to `breeze_session` → `sync_icici` job: refresh securities if stale, prices, missing fundamentals.
- Tracking a stock (search → Track, or a manual holding for an untracked stock) inserts into
  `companies` and spawns `onboard` (fundamentals now, prices if the session is valid).
- Mutual funds: buy/sell entries in `mf_transactions` (per fund per broker, average cost); positions,
  realised gains and value come from those + `mf_nav`. `refresh_mf` loads every scheme's NAV from AMFI and
  backfills history (MFapi) for held funds. `/portfolio?scope=all|stocks|mf` merges stocks, ETFs and funds.
- Timers (pinned to Asia/Kolkata; the VM clock is UTC): prices Mon–Fri 19:00, MF NAVs daily 23:30, securities Sun 02:00,
  fundamentals Sun 03:00;
  `Persistent=true` catches up after the machine was off. Jobs skip cleanly (exit 75, status
  `skipped`) without a valid session.

## Local dev

```
docker compose up -d db
pipeline/.venv/bin/python db/migrate.py --seed
cd backend && set -a && . ../.env && set +a && .venv/bin/uvicorn main:app --port 8000
cd frontend && npm run dev
```
venvs: `uv venv --python 3.12 pipeline/.venv && uv pip install --python pipeline/.venv/bin/python -r pipeline/requirements.txt`
(same for backend).

## Deployment

VM `ssh 135.235.195.168` (user `drunkencloud`, no passwordless sudo, repo at `~/trading`, Python 3.10:
no 3.11+ syntax). Root-level changes live in `deploy/vm_root.sh`, which the user runs themselves:
updates, fail2ban, sshd drop-in, ufw (22/80/443), Caddyfile with `basic_auth` on everything except
`/api/cb/*`.

- `bash deploy/deploy.sh` (no sudo): builds the frontend, rsyncs the repo (keeps the VM's `.env`,
  venvs, logs) and `frontend/out/` → `~/trading/frontend/dist/`, runs migrations, links
  `deploy/systemd/*` into `~/.config/systemd/user/`, enables the timers, restarts the backend.
- Units: `stocklens-backend` (uvicorn 127.0.0.1:8000, `KillMode=process` so spawned jobs survive
  restarts), `stocklens-job@<job>` + `stocklens-{prices,fundamentals,securities}.timer`.
  Logs: `journalctl --user -u stocklens-backend`, run logs in `pipeline/logs/`.
- Caddy is the system service with `/etc/caddy/Caddyfile`; edit the file, never only the admin API.

## Live-verified gotchas

- Breeze `stock_code` ≠ NSE ticker (M&M → MAHMAH, BAJAJFINSV → BAFINS). SecurityMaster `ShortName`
  is the Breeze code; `ExchangeCode` is the NSE ticker; BSE file has `ScripCode`/`ScripID`.
- Indian equity ISIN: `INE` + 4 chars + `01` at index 7–8; anything else is a bond/NCD/govt security.
- Breeze sessions die at midnight IST. Expired token text: "Session key is expired."; wrong token:
  "Could not authenticate credentials. Please check session key."; "Unable to retrieve customer
  details" is a catch-all and is not treated as a session verdict.
- ICICI's developer portal truncates the redirect URL at ~60 chars; the callback arrives as a POST
  with `apisession` in the query string.
- Breeze adjusts history for splits/bonuses only at download time; rows fetched before a corporate action stay
  unadjusted. `fetch_prices` runs `pipeline/splits.py` after each fetch: overnight drops of 2/3/4/5/10/20x
  (±6%) scale earlier prices. Trades from before a split must be entered split-adjusted (qty×, price÷).
- ETFs are `INF…` ISINs in NSE series `EQ` (kept, `kind='etf'`, asset class from the name). ICICI's app shows
  its own names for them (ICICIGOLD = GOLDIETF, ICICISILVE = SILVERIETF); Breeze codes map them.
- BSE-only stocks (e.g. NSE Ltd, BSE 544937): Breeze `get_historical_data` rejects BSE; use
  `get_historical_data_v2` (fetched in 900-day windows) with the BSE `ShortName` as stock code.
- Breeze answers an empty date range with Error "No Data Found": that is zero rows, not a failure.
- AMFI NAV file moved to `https://portal.amfiindia.com/spages/NAVAll.txt` (8 columns incl. Plan/Option).
  Some schemes (Motilal Oswal Multi Cap) have blank Plan/Option; refresh keeps a previously set value.
- Opening MF positions were entered from app screenshots: units = current value ÷ NAV on 13 Nov 2026,
  purchase dates unknown (so no XIRR until dated entries exist).
- Yahoo (`{SYMBOL}.NS`, BSE-only `{SYMBOL}.BO`): roe/op_margin/revenueGrowth are fractions (×100), debtToEquity is ×100
  pre-scaled (÷100), dividendYield is already a percent.
