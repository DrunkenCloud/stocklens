-- Every pipeline job run (cron, admin button, or automatic after login), written by
-- pipeline/run.py. The admin panel and "last synced" read from here.
CREATE TABLE job_runs (
    id          BIGSERIAL PRIMARY KEY,
    job         TEXT NOT NULL,
    args        TEXT NOT NULL DEFAULT '',
    trigger     TEXT NOT NULL DEFAULT 'cron' CHECK (trigger IN ('cron', 'admin', 'auto')),
    status      TEXT NOT NULL DEFAULT 'running' CHECK (status IN ('running', 'done', 'failed', 'skipped')),
    started_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    finished_at TIMESTAMPTZ,
    log_path    TEXT,
    summary     TEXT
);
CREATE INDEX idx_job_runs_started ON job_runs (started_at DESC);
