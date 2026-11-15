CREATE TABLE securities (
    isin        TEXT PRIMARY KEY,
    name        TEXT NOT NULL,
    nse_symbol  TEXT,
    breeze_code TEXT,
    nse_series  TEXT,
    bse_code    TEXT,
    bse_symbol  TEXT,
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_securities_nse_symbol ON securities (nse_symbol);
CREATE INDEX idx_securities_bse_symbol ON securities (bse_symbol);

ALTER TABLE companies ADD COLUMN IF NOT EXISTS isin TEXT;
