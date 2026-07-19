# Schema & API

## PostgreSQL schema

Five tables. SQL is illustrative — adjust types/constraints to taste.

```sql
-- Tracked NSE universe. Written by refresh_universe job.
CREATE TABLE companies (
    symbol        TEXT PRIMARY KEY,          -- NSE ticker, e.g. 'RELIANCE'
    name          TEXT NOT NULL,
    sector        TEXT,
    breeze_code   TEXT,                      -- Breeze's own stock_code mapping
    is_active     BOOLEAN NOT NULL DEFAULT TRUE,
    listed_on     DATE,
    updated_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Daily OHLCV. Written by fetch_prices job. The big table (~10M rows @ 20yr univ).
CREATE TABLE daily_prices (
    symbol   TEXT NOT NULL REFERENCES companies(symbol),
    date     DATE NOT NULL,
    open     NUMERIC(14,4),
    high     NUMERIC(14,4),
    low      NUMERIC(14,4),
    close    NUMERIC(14,4) NOT NULL,
    volume   BIGINT,
    PRIMARY KEY (symbol, date)
);
CREATE INDEX idx_prices_symbol_date ON daily_prices (symbol, date DESC);

-- Fundamentals as dated snapshots (append, don't overwrite -> keeps trend history).
-- Written by fetch_fundamentals job. Nullable everywhere: free data is patchy.
CREATE TABLE fundamentals (
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
CREATE TABLE users (
    id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email      TEXT UNIQUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Manually-entered holdings. Stocks only in v1 (MFs deferred).
CREATE TABLE holdings (
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
CREATE INDEX idx_holdings_user ON holdings (user_id);

-- Optional: cache AI narratives so we don't re-call per page view.
CREATE TABLE analysis_cache (
    symbol         TEXT NOT NULL REFERENCES companies(symbol),
    snapshot_date  DATE NOT NULL,     -- ties narrative to the fundamentals it used
    narrative      TEXT NOT NULL,
    generated_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (symbol, snapshot_date)
);
```

Notes:
- `fundamentals` is snapshot-append so View 1 can show trends and the AI can cite
  "3yr ago" figures.
- Everything in `fundamentals` is nullable on purpose — free data is patchy; the
  app and AI both handle N/A gracefully.
- `holdings.account` lets a user tag which demat an entry belongs to (their 3
  accounts) without integrating any broker.

---

## FastAPI endpoints

### Stocks / detail
```
GET /stocks/{symbol}
    → company info + latest fundamentals snapshot + recent price summary
GET /stocks/{symbol}/fundamentals?history=true
    → all fundamentals snapshots (for trend charts)
```

### Screener (View 1)
```
GET /screen
    query params (all optional): pe_max, pe_min, pb_max, roe_min,
        de_max, div_yield_min, rev_cagr_3y_min, sector, sort_by, order, limit
    → ranked list of {symbol, name, sector, key ratios, latest close}
    Backed by latest fundamentals snapshot per symbol JOIN latest price.
```

### Prices / returns (View 2)
```
GET /prices/{symbol}?from=YYYY-MM-DD&to=YYYY-MM-DD
    → daily OHLCV series for charting
GET /prices/{symbol}/returns?from=YYYY-MM-DD&amount=100000
    → computed: total_return, cagr, max_drawdown, best_year, worst_year,
      value_now (of `amount` invested at `from`)
    Formulas below.
```

### AI analysis (View 1)
```
GET /analysis/{symbol}
    → { narrative, as_of_date, disclaimer }
    Serves from analysis_cache if current; else calls Anthropic, caches, returns.
    See 04_AI_FEATURE.md.
```

### Portfolio
```
GET    /portfolio                 → holdings + per-holding & total returns
POST   /portfolio                 → add a holding (symbol, qty, avg_cost, buy_date, account, note)
PUT    /portfolio/{id}            → edit
DELETE /portfolio/{id}            → remove
```
Per-holding return = `(latest_close - avg_cost) * quantity`; also % and total.

---

## Return formulas (implement in `services/returns.py`)

Pure functions over a `daily_prices` series. Keep them unit-tested — they're the
quantitative core of View 2.

**Total return** (price only, over period start→end):
```
total_return_pct = (close_end - close_start) / close_start * 100
```

**CAGR** (compound annual growth rate):
```
years = (date_end - date_start).days / 365.25
cagr_pct = ((close_end / close_start) ** (1 / years) - 1) * 100     # years > 0
```

**Value of a lump sum** invested at start:
```
units    = amount / close_start
value_now = units * close_end
```

**Max drawdown** (worst peak-to-trough over the period):
```
running_peak = close[0]
max_dd = 0
for c in close_series:
    running_peak = max(running_peak, c)
    dd = (c - running_peak) / running_peak     # <= 0
    max_dd = min(max_dd, dd)
max_drawdown_pct = max_dd * 100                # negative number
```

**Best / worst calendar year** (group by year, per-year total return):
```
for each year Y:
    year_return = (last_close_in_Y - first_close_in_Y) / first_close_in_Y * 100
best_year  = year with max year_return
worst_year = year with min year_return
```

**Honesty notes to bake into the code/UI:**
- These are **price returns**. If you don't have dividend-adjusted closes, say so —
  total shareholder return would be higher for dividend payers. (Dividend-adjusted
  series is a v2 upgrade if the price source supports it.)
- CAGR over a cherry-picked start date flatters or punishes; consider showing CAGR
  over several fixed windows (1y/3y/5y/max) rather than one, so it's not misleading.
- Never annualize a sub-1-year period into a CAGR (mathematically valid, practically
  deceptive) — guard `years >= 1` or label clearly.
