CREATE TABLE IF NOT EXISTS companies (
    symbol        TEXT PRIMARY KEY,
    name          TEXT NOT NULL,
    sector        TEXT,
    breeze_code   TEXT,
    is_active     BOOLEAN NOT NULL DEFAULT TRUE,
    listed_on     DATE,
    updated_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS daily_prices (
    symbol   TEXT NOT NULL REFERENCES companies(symbol),
    date     DATE NOT NULL,
    open     NUMERIC(14,4),
    high     NUMERIC(14,4),
    low      NUMERIC(14,4),
    close    NUMERIC(14,4) NOT NULL,
    volume   BIGINT,
    PRIMARY KEY (symbol, date)
);
CREATE INDEX IF NOT EXISTS idx_prices_symbol_date ON daily_prices (symbol, date DESC);

CREATE TABLE IF NOT EXISTS fundamentals (
    symbol         TEXT NOT NULL REFERENCES companies(symbol),
    snapshot_date  DATE NOT NULL,
    pe             NUMERIC(12,4),
    pb             NUMERIC(12,4),
    roe            NUMERIC(8,4),
    op_margin      NUMERIC(8,4),
    rev_ttm        NUMERIC(18,2),
    rev_growth_1y  NUMERIC(8,4),
    rev_cagr_3y    NUMERIC(8,4),
    debt_to_equity NUMERIC(10,4),
    dividend_yield NUMERIC(8,4),
    market_cap     NUMERIC(18,2),
    raw            JSONB,
    PRIMARY KEY (symbol, snapshot_date)
);

CREATE TABLE IF NOT EXISTS users (
    id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email      TEXT UNIQUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS holdings (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     UUID NOT NULL REFERENCES users(id),
    symbol      TEXT NOT NULL REFERENCES companies(symbol),
    quantity    NUMERIC(18,4) NOT NULL,
    avg_cost    NUMERIC(14,4) NOT NULL,
    buy_date    DATE,
    account     TEXT,
    note        TEXT,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_holdings_user ON holdings (user_id);

INSERT INTO users (id) VALUES ('00000000-0000-0000-0000-000000000001')
ON CONFLICT (id) DO NOTHING;
