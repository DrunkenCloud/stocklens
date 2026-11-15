-- v1 schema as deployed (Jul 2026). IF NOT EXISTS everywhere so this is a no-op on the
-- existing prod database, which predates migrations.


-- Tracked NSE universe.
CREATE TABLE IF NOT EXISTS companies (
    symbol        TEXT PRIMARY KEY,          -- NSE ticker, e.g. 'RELIANCE'
    name          TEXT NOT NULL,
    sector        TEXT,
    breeze_code   TEXT,                      -- Breeze's own stock_code mapping
    is_active     BOOLEAN NOT NULL DEFAULT TRUE,
    listed_on     DATE,
    updated_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Daily OHLCV. Written by fetch_prices job.
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

-- Fundamentals as dated snapshots (append, don't overwrite -> keeps trend history).
-- Written by fetch_fundamentals job. Nullable everywhere: free data is patchy.
CREATE TABLE IF NOT EXISTS fundamentals (
    symbol         TEXT NOT NULL REFERENCES companies(symbol),
    snapshot_date  DATE NOT NULL,
    pe             NUMERIC(12,4),
    pb             NUMERIC(12,4),
    roe            NUMERIC(8,4),         -- percent
    op_margin      NUMERIC(8,4),         -- percent
    rev_ttm        NUMERIC(18,2),
    rev_growth_1y  NUMERIC(8,4),         -- percent
    rev_cagr_3y    NUMERIC(8,4),         -- percent
    debt_to_equity NUMERIC(10,4),
    dividend_yield NUMERIC(8,4),         -- percent
    market_cap     NUMERIC(18,2),
    raw            JSONB,                -- whatever else the source gave, unnormalized
    PRIMARY KEY (symbol, snapshot_date)
);

-- Users (minimal for v1; even single-user, keep the seam for multi-user).
CREATE TABLE IF NOT EXISTS users (
    id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email      TEXT UNIQUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Manually-entered holdings. Stocks only in v1 (MFs deferred).
CREATE TABLE IF NOT EXISTS holdings (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     UUID NOT NULL REFERENCES users(id),
    symbol      TEXT NOT NULL REFERENCES companies(symbol),
    quantity    NUMERIC(18,4) NOT NULL,
    avg_cost    NUMERIC(14,4) NOT NULL,   -- per share, user-entered
    buy_date    DATE,
    account     TEXT,                     -- free-text label, e.g. which demat
    note        TEXT,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_holdings_user ON holdings (user_id);

-- Single default user (the app is single-user, no auth). Fixed id so the backend
-- can reference it without a lookup.
INSERT INTO users (id) VALUES ('00000000-0000-0000-0000-000000000001')
ON CONFLICT (id) DO NOTHING;
