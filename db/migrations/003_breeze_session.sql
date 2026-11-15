CREATE TABLE breeze_session (
    id          INT PRIMARY KEY DEFAULT 1 CHECK (id = 1),
    token       TEXT NOT NULL,
    captured_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    invalid_at  TIMESTAMPTZ
);
