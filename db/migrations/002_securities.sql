-- Every listed equity from ICICI's SecurityMaster file, one row per company (ISIN
-- links its NSE and BSE listings). Written by pipeline/jobs/refresh_securities.py;
-- powers stock search. breeze_code is ICICI's own stock code (often != the ticker,
-- e.g. M&M -> MAHMAH).
CREATE TABLE securities (
    isin        TEXT PRIMARY KEY,
    name        TEXT NOT NULL,
    nse_symbol  TEXT,
    breeze_code TEXT,
    nse_series  TEXT,
    bse_code    TEXT,               -- BSE scrip code, e.g. '500325'
    bse_symbol  TEXT,
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_securities_nse_symbol ON securities (nse_symbol);
CREATE INDEX idx_securities_bse_symbol ON securities (bse_symbol);

ALTER TABLE companies ADD COLUMN IF NOT EXISTS isin TEXT;
