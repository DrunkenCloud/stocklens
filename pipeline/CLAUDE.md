# pipeline/

Standalone jobs, run from the repo root via `pipeline/run_job.sh jobs.<name> [args]`, which calls
`pipeline/run.py` to record the run in `job_runs` and write `pipeline/logs/<id>.log`.
`pipeline/__init__.py` loads the repo-root `.env`.

Jobs: `sync_icici`, `fetch_prices [--backfill] [--symbols A,B]`, `fetch_fundamentals
[--symbols A,B | --missing]`, `refresh_securities`, `onboard --symbols A`.

- Exit 75 (`run.SKIPPED_EXIT`) = skipped (no valid Breeze session); recorded as `skipped`.
- `breeze_client.get_client()` reads the token from `breeze_session`, raises `SessionExpired` and
  marks the row invalid on session errors. Breeze reports API errors in the payload: use
  `check_response()`.
- Per-symbol isolation: one bad symbol is logged and skipped, with `conn.rollback()` so the
  connection stays usable. An expired session aborts the whole run instead.
- Idempotent upserts everywhere; every job is safe to re-run.
- Verify sources against live responses before trusting docs (see root CLAUDE.md gotchas).
- Pure logic gets plain-assert self-checks: `pipeline/.venv/bin/python -m pipeline.test_holdings`.
