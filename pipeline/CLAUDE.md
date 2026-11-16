# pipeline/

Standalone jobs, run from the repo root via `pipeline/run_job.sh jobs.<name> [args]`, which calls
`pipeline/run.py` to record the run in `job_runs` and write `pipeline/logs/<id>.log`.
`pipeline/__init__.py` loads the repo-root `.env`.

Jobs: `sync_icici`, `fetch_prices [--backfill] [--symbols A,B]`, `fetch_live [YYYY-MM-DD]`, `fetch_fundamentals
[--symbols A,B | --missing]`, `refresh_securities`, `refresh_mf`, `refresh_fund_portfolios`, `onboard --symbols A`,
`daily_report [--force]`.

- Exit 75 (`run.SKIPPED_EXIT`) = skipped (no valid Breeze session for `sync_icici`, market closed for `fetch_live`,
  holiday or already sent for `daily_report`); recorded as `skipped`. Price jobs never skip for a missing session.
- `breeze_client.get_client()` reads the token from `breeze_session`, raises `SessionExpired` and
  marks the row invalid on session errors. Breeze reports API errors in the payload: use
  `check_response()`.
- `daily_report` talks to the backend over HTTP (`STOCKLENS_API`, default `http://127.0.0.1:8000/api`); it never imports
  backend code, and the backend never imports pipeline code. `pipeline/bars.py` holds `day_bar` (shared by live
  prices and indexes).
- Per-symbol isolation: one bad symbol is logged and skipped, with `conn.rollback()` so the
  connection stays usable. A session that dies mid-run switches the rest of the run to Yahoo.
- Idempotent upserts everywhere; every job is safe to re-run.
- Verify sources against live responses before trusting docs (see root CLAUDE.md gotchas).
- Pure logic gets plain-assert self-checks: `pipeline/.venv/bin/python -m pipeline.test_holdings`.
