# StockLens

Personal portfolio + stock research tool for one user. Holdings across ICICI
(synced automatically after the daily ICICI login), Zerodha and Groww (entered
by hand as shares + total invested), plus search over every NSE/BSE equity,
stock pages, a screener and a Data page for pipeline ops.

FastAPI (`/api`) + PostgreSQL + Next.js static export. Prices from ICICI
Breeze, fundamentals from Yahoo Finance, stock universe from ICICI's
SecurityMaster file. Runs locally on the user's machine at https://investlens.duckdns.org
(an `/etc/hosts` entry points the domain at 127.0.0.1; the old Azure VM deploy is retired).

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

- Daily: user clicks "Log in to ICICI" → ICICI redirects to `/api/cb/<BREEZE_CALLBACK_TOKEN>` →
  token saved to `breeze_session` → `sync_icici` job: refresh securities if stale, pull ICICI
  holdings, auto-track new stocks, replace `source='icici_sync'` holdings, prices, missing fundamentals.
- Tracking a stock (search → Track, or a manual holding for an untracked stock) inserts into
  `companies` and spawns `onboard` (fundamentals now, prices if the session is valid).
- Timers (local time, IST): prices Mon–Fri 19:00, securities Sun 02:00, fundamentals Sun 03:00;
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

## Running it (this machine)

One-time: `bash deploy/setup.sh` (asks for sudo: installs Caddy, lets it bind 80/443, adds the
`/etc/hosts` entry, enables Docker + user lingering, trusts Caddy's local CA).

- Postgres: docker compose `db` (`restart: unless-stopped`), port 5433.
- `systemctl --user` units, symlinked from `deploy/systemd/` into `~/.config/systemd/user/`:
  `stocklens-backend` (uvicorn 127.0.0.1:8000), `stocklens-caddy` (`deploy/Caddyfile`, `tls internal`,
  serves `frontend/out` and proxies `/api/*`), `stocklens-job@<job>` + `stocklens-{prices,fundamentals,securities}.timer`.
- After changes: backend → `systemctl --user restart stocklens-backend`; frontend →
  `npm --prefix frontend run build` (Caddy serves the new `out/` immediately); migrations →
  `pipeline/.venv/bin/python db/migrate.py`. Logs: `journalctl --user -u stocklens-backend`.
- ICICI's registered redirect is `https://investlens.duckdns.org/api/cb/<BREEZE_CALLBACK_TOKEN>`;
  the hosts entry makes the browser deliver it to this machine.

## Live-verified gotchas

- Breeze `stock_code` ≠ NSE ticker (M&M → MAHMAH, BAJAJFINSV → BAFINS). SecurityMaster `ShortName`
  is the Breeze code; `ExchangeCode` is the NSE ticker; BSE file has `ScripCode`/`ScripID`.
- Indian equity ISIN: `INE` + 4 chars + `01` at index 7–8; anything else is a bond/NCD/govt security.
- Breeze sessions die at midnight IST. Expired token text: "Session key is expired."; wrong token:
  "Could not authenticate credentials. Please check session key."; "Unable to retrieve customer
  details" is a catch-all and is not treated as a session verdict.
- ICICI's developer portal truncates the redirect URL at ~60 chars; the callback arrives as a POST
  with `apisession` in the query string.
- Breeze historical prices are not adjusted for splits/bonuses (HDFCBANK's 1:1 bonus halves the price).
- `get_portfolio_holdings` field names come from docs and were not yet confirmed live; parsing is
  strict and a bad shape fails the sync without touching stored holdings.
- Yahoo (`{SYMBOL}.NS`): roe/op_margin/revenueGrowth are fractions (×100), debtToEquity is ×100
  pre-scaled (÷100), dividendYield is already a percent.
