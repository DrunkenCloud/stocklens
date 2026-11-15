ALTER TABLE securities
    ADD COLUMN kind TEXT NOT NULL DEFAULT 'stock',
    ADD COLUMN asset_class TEXT NOT NULL DEFAULT 'equity',
    ADD COLUMN bse_breeze_code TEXT;

ALTER TABLE companies
    ADD COLUMN exchange TEXT NOT NULL DEFAULT 'NSE' CHECK (exchange IN ('NSE', 'BSE')),
    ADD COLUMN kind TEXT NOT NULL DEFAULT 'stock' CHECK (kind IN ('stock', 'etf')),
    ADD COLUMN asset_class TEXT NOT NULL DEFAULT 'equity';
