# Data Pipeline

Standalone ingestion. Not part of the FastAPI request path — a slow or broken fetch
must never block the API. Jobs run on a schedule, fetch from the two sources,
normalize, and upsert into Postgres.

---

## Jobs

### Job 1 — `refresh_universe` (weekly)
Refresh the list of NSE-listed stocks we track → `companies` table.
- Source: NSE listed-equities list (or the fundamentals source's symbol list).
- Upsert by `symbol`. Mark delisted symbols inactive rather than deleting (keeps
  historical prices meaningful).
- Low frequency — listings don't change often.

### Job 2 — `fetch_prices` (daily, after market close)
Pull daily OHLCV per active symbol from Breeze → `daily_prices`.
- **Incremental:** only fetch from `last_stored_date + 1` to today per symbol
  (don't re-pull 10 years every night).
- **Backfill mode:** a one-time flag to pull full history when a symbol is first
  added.
- Upsert on `(symbol, date)` so re-runs are idempotent.
- Respect Breeze rate limits: throttle, small concurrency (e.g. 3 workers), retry
  with backoff on transient errors.

### Job 3 — `fetch_fundamentals` (weekly, or after earnings season)
Pull core ratios + key financials per symbol from the free source → `fundamentals`.
- Fundamentals change slowly (quarterly), so weekly is plenty.
- **This is the fragile job** (scraper). Expect breakage; see resilience below.
- Store as a dated snapshot row per symbol so history is preserved and you can show
  trends (`fundamentals` is append-by-snapshot, not overwrite).

---

## Scheduling

v1 keep it dead simple:
- **cron** on the Azure VM calling each job script, **or**
- a tiny Python scheduler (`schedule` lib / APScheduler) in `pipeline/schedule.py`.

Suggested cadence:
```
refresh_universe      Sun 02:00
fetch_prices          Mon–Fri 19:00 IST   (after 15:30 close + settle)
fetch_fundamentals    Sun 03:00
```
No Airflow/Kafka for v1 — that's over-engineering at this scale (noted in
`06_DECISIONS.md`).

---

## Breeze auth flow (wrap in `breeze_client.py`)

Session-based, not a plain API key. One-time app setup, then per-session login.

**One-time (manual, in ICICI Breeze portal):**
1. Register an app → get `api_key` and `api_secret`.
2. Note them in env/secrets (never commit).

**Per session (in code):**
```
from breeze_connect import BreezeConnect

breeze = BreezeConnect(api_key=API_KEY)

# api_session token comes from the login/session-key step:
#   - user logs in via the Breeze login URL for the app
#   - that yields a session token (api_session)
breeze.generate_session(api_secret=API_SECRET, session_token=API_SESSION)

# now calls work, e.g. daily history:
data = breeze.get_historical_data(
    interval="1day",
    from_date="2015-01-01T00:00:00.000Z",
    to_date="2026-01-01T00:00:00.000Z",
    stock_code="RELIANCE",     # Breeze uses its own stock_code scheme
    exchange_code="NSE",
    product_type="cash",
)
```

**Practical notes:**
- The `api_session`/session token typically needs periodic regeneration (it's not
  permanent). For an automated daily job, script the login/session-generation, or
  use a community autologin helper. Isolate this pain in `breeze_client.py`.
- Breeze has its **own `stock_code` mapping** that isn't always the plain NSE ticker.
  Build/maintain a symbol→breeze_code map (store `breeze_code` on `companies`).
- Wrap every call in retry+backoff; Breeze can rate-limit or return transient errors.

---

## Resilience (especially the fragile fundamentals job)

- **Idempotent upserts** everywhere → safe to re-run.
- **Per-symbol isolation:** one symbol failing must not abort the whole run
  (try/except per symbol, log failures, continue).
- **Failure log table or file:** record which symbols failed and why, so a re-run
  can target just those.
- **Staleness is acceptable:** if fundamentals scraping breaks for a week, the app
  keeps serving the last good snapshot. Surface "as of <date>" in the UI so users
  know data age.
- **Alerting (light):** a job that fails entirely should at least log loudly / send
  yourself a notification. No need for full observability tooling in v1.

---

## What the pipeline writes (recap)

| Job | Table(s) | Frequency | Fragility |
|---|---|---|---|
| refresh_universe | `companies` | weekly | low |
| fetch_prices | `daily_prices` | daily (weekdays) | low–med (rate limits) |
| fetch_fundamentals | `fundamentals` | weekly | **high (scraper)** |
