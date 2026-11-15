-- The daily ICICI Breeze session token, captured by the login callback. Lives here
-- (not .env) so the app can tell whether it's still valid and when it was captured.
-- api_key/api_secret stay in env. Single row.
CREATE TABLE breeze_session (
    id          INT PRIMARY KEY DEFAULT 1 CHECK (id = 1),
    token       TEXT NOT NULL,
    captured_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    invalid_at  TIMESTAMPTZ             -- set when Breeze rejects the token as expired
);
