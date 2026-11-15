CREATE TABLE mf_schemes (
    code          INT PRIMARY KEY,
    name          TEXT NOT NULL,
    amc           TEXT,
    category      TEXT,
    plan          TEXT,
    option        TEXT,
    isin          TEXT,
    isin_reinvest TEXT,
    asset_class   TEXT NOT NULL DEFAULT 'other',
    nav           NUMERIC(16,4),
    nav_date      DATE,
    updated_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_mf_schemes_isin ON mf_schemes (isin);

CREATE TABLE mf_nav (
    code INT NOT NULL REFERENCES mf_schemes(code),
    date DATE NOT NULL,
    nav  NUMERIC(16,4) NOT NULL,
    PRIMARY KEY (code, date)
);

CREATE TABLE mf_transactions (
    id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id    UUID NOT NULL REFERENCES users(id),
    code       INT NOT NULL REFERENCES mf_schemes(code),
    broker     TEXT NOT NULL,
    kind       TEXT NOT NULL CHECK (kind IN ('buy', 'sell')),
    units      NUMERIC(18,4) NOT NULL CHECK (units > 0),
    amount     NUMERIC(18,2) NOT NULL CHECK (amount >= 0),
    date       DATE,
    note       TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_mf_transactions_user ON mf_transactions (user_id, code);
