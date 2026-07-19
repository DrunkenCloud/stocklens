# Pipeline

Standalone ingestion jobs. Not imported by the API — a slow/broken fetch here
must never block FastAPI. Run from the repo root (`python -m pipeline.jobs.<job>`)
so the `pipeline` package resolves; not containerized yet (that's M7, alongside
the cron scheduler).

## Setup

```
pip install -r pipeline/requirements.txt
```

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
3. `export $(cat .env | xargs)` (or your usual env-loading method) before running jobs.

## fetch_prices

```
python -m pipeline.jobs.fetch_prices              # incremental: only new days per symbol
python -m pipeline.jobs.fetch_prices --backfill    # full history from 2015-01-01
```

Self-check (pure logic, no live Breeze/DB needed):
```
python -m pipeline.jobs.test_fetch_prices
```

## Known unverified assumptions (flag before trusting real data)

- **`breeze_code` mapping** — defaults to the plain NSE ticker per `03_PIPELINE.md`'s
  own example. Breeze's real security-master codes may differ for some symbols;
  verify once you have portal access and set `companies.breeze_code` for any that
  do (`UPDATE companies SET breeze_code = '...' WHERE symbol = '...'`).
- **Response field names** (`datetime`, `open`, `high`, `low`, `close`, `volume`)
  in `normalize_row()` — copied from documented examples, not yet checked against
  a live API response. If a real fetch throws a `KeyError`, this is the one
  function to fix.
- **Login URL pattern** in `breeze_client.login_url()` — standard Breeze pattern,
  double-check against the current portal docs.

Run `--backfill` for one symbol first and eyeball `daily_prices` before trusting
a full-universe backfill.
