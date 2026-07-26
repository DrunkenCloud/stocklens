# pipeline/

Standalone ingestion jobs — **not imported by the backend** (`01_ARCHITECTURE.md`).
Full setup, job-by-job docs, and what's been verified live are in
`pipeline/README.md` — read that first. This file is conventions only.

## Conventions

- **Run from the repo root**, not from inside `pipeline/`:
  `python -m pipeline.jobs.<job>`. The package resolves relative to repo root;
  running from elsewhere breaks the `pipeline/__init__.py` auto-`.env`-loading.
- **`.env` loads automatically** (`pipeline/__init__.py`) — never add manual
  `export`/dotenv-loading to a job script, it's already handled once, centrally.
- **Per-symbol isolation, always.** Every job loops over companies in a
  try/except per symbol, logs failures, and keeps going — never let one bad
  symbol (delisted ticker, corporate action, rate limit) abort the whole run.
  `fetch_prices.py` / `fetch_fundamentals.py` are the reference pattern.
- **Idempotent upserts, always.** `ON CONFLICT ... DO UPDATE` — every job must
  be safe to re-run (cron re-runs it on schedule; the admin panel lets a human
  re-run it on demand too now, see `ADMIN_OPS.md`).
- **New job scripts need `run_job.sh` compatibility** — callable as
  `pipeline/run_job.sh jobs.<new_job> [args]`. No changes needed to
  `run_job.sh` itself for a new job; it's generic.
- **Verify against live data before trusting a source, don't assume from
  docs.** Both real bugs found this project (Breeze's `stock_code` not
  matching the NSE ticker; Yahoo's `debtToEquity` being pre-scaled by 100)
  were caught by testing against real API responses, not by reading
  documentation. See `06_DECISIONS.md` D3/D8 for what that looked like.

## Self-checks

Pure logic (date math, response parsing, unit conversions) gets an
assert-based self-check, not a test framework — `test_fetch_prices.py`,
`test_fundamentals_source.py`. Run via
`pipeline/.venv/bin/python -m pipeline.jobs.test_fetch_prices` (or the
equivalent module path). No network/DB access in these — that's what makes
them fast enough to actually run before trusting a change.
