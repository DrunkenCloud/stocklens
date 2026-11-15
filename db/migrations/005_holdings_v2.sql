ALTER TABLE holdings
    ADD COLUMN broker   TEXT,
    ADD COLUMN source   TEXT NOT NULL DEFAULT 'manual' CHECK (source IN ('manual', 'icici_sync')),
    ADD COLUMN invested NUMERIC(18,2);

UPDATE holdings SET invested = quantity * avg_cost, broker = coalesce(nullif(trim(account), ''), 'Other');

ALTER TABLE holdings
    ALTER COLUMN broker SET NOT NULL,
    ALTER COLUMN invested SET NOT NULL,
    DROP COLUMN avg_cost,
    DROP COLUMN account;
