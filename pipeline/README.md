# Pipeline

Standalone ingestion jobs. Not imported by the API — a slow/broken fetch here
must never block FastAPI. Run from the repo root (`python -m pipeline.jobs.<job>`)
so the `pipeline` package resolves; not containerized (cron calling the job
scripts directly is the whole scheduler - `06_DECISIONS.md` D7, no
Airflow/APScheduler needed at this scale).

## Setup

```
python3 -m venv pipeline/.venv        # run_job.sh (cron wrapper) looks for this path
pipeline/.venv/bin/pip install -r pipeline/requirements.txt
cp .env.example .env   # if you haven't already, at the repo root
```

Jobs auto-load `.env` from the repo root (`pipeline/__init__.py`) — no manual
`export` needed, just fill in `.env` and run.

`DATABASE_URL` needs to reach the Postgres container from the host — with the
default `docker-compose.yml` port mapping that's
`postgresql://stocklens:stocklens@localhost:5433/stocklens`.

## Breeze auth (one-time app registration, then per-session)

1. Register an app in the ICICI Breeze developer portal → get `BREEZE_API_KEY` /
   `BREEZE_API_SECRET`. Put them in `.env`.
2. Get a session token (this expires periodically — repeat when it does):
   ```
   python -c "from pipeline.breeze_client import login_url; print(login_url())"
   ```
   Open that URL, log in, and copy the session token from the redirect URL into
   `BREEZE_API_SESSION` in `.env`.

## map_breeze_codes

Run once (and again any time you add a company): Breeze's internal `stock_code`
often differs from the plain NSE ticker (confirmed live - e.g. `M&M` -> `MAHMAH`,
`BAJAJFINSV` -> `BAFINS`, `RELIANCE` -> `RELIND`). This resolves and stores it on
`companies.breeze_code` via Breeze's `get_names()`. `fetch_prices` skips any
company with no `breeze_code` set rather than guessing.

```
python -m pipeline.jobs.map_breeze_codes
```

Known gap: `get_names()` can return a messy/ambiguous match for some symbols
(company name and token fields show multiple concatenated instruments, e.g. a
warrant alongside the equity) even though `isec_stock_code` itself came out
clean in testing. Spot-check `companies.breeze_code` after running, especially
for symbols with recent corporate actions (demergers, warrants, etc).

## fetch_prices

```
python -m pipeline.jobs.fetch_prices              # incremental: only new days per symbol
python -m pipeline.jobs.fetch_prices --backfill    # full history from 2015-01-01
```

Self-check (pure logic, no live Breeze/DB needed):
```
python -m pipeline.jobs.test_fetch_prices
```

Verified against a live account: auth, `get_names` resolution, and a full
`--backfill` for the 30 seeded companies (29 succeeded, 2015-01-01 through
today, ~2,850 rows each). One known failure: `TATAMOTORS` - Breeze's
`get_names()` returns "Result Not Found" for it, most likely because of a
corporate action (demerger) changing what the ticker maps to. Not yet
resolved; needs a manual look rather than a guessed fix.

## fetch_fundamentals

Pulls fundamentals via Yahoo Finance (`yfinance`) - see `06_DECISIONS.md` D8
for why this source and the field-scaling gotchas found while verifying it.
No separate code-mapping step needed (unlike Breeze); Yahoo's NSE convention
is just `{ticker}.NS`.

```
python -m pipeline.jobs.fetch_fundamentals
```

Snapshot-append into `fundamentals` (one row per symbol per day run), per
`03_PIPELINE.md`. Self-check for the pure conversion/CAGR math:
```
python -m pipeline.test_fundamentals_source
```

Verified live: 29/30 seeded companies fetched successfully (real P/E, P/B,
ROE, margins, debt-to-equity, dividend yield, market cap). `TATAMOTORS` fails
here too - independent confirmation (different data source, same symbol)
that it's a real stale-ticker issue, not a Breeze-specific quirk.

## Scheduling (cron)

`run_job.sh` wraps a job for cron: resolves the repo root regardless of
cron's working directory, uses `pipeline/.venv` if present (falls back to
`python3`), logs start/exit with timestamps, and - importantly - actually
propagates a failing job's exit code instead of `set -e` swallowing it
(caught by testing the wrapper directly, not assumed).

```
./pipeline/run_job.sh jobs.fetch_prices
./pipeline/run_job.sh jobs.fetch_prices --backfill
./pipeline/run_job.sh jobs.fetch_fundamentals
```

Install the cadence from `03_PIPELINE.md` (edit the path first):
```
crontab pipeline/crontab.example
```

`refresh_universe` (the third job `03_PIPELINE.md` describes) isn't built -
v1 uses the hand-seeded companies in `db/seed.sql` (`07_ROADMAP.md` M0), so
only `fetch_prices` and `fetch_fundamentals` are wired. Build it if/when you
want the tracked universe to grow past the seed set.
