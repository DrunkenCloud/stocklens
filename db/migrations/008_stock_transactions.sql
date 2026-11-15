CREATE TABLE stock_transactions (
    id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id    UUID NOT NULL REFERENCES users(id),
    symbol     TEXT NOT NULL REFERENCES companies(symbol),
    broker     TEXT NOT NULL,
    kind       TEXT NOT NULL CHECK (kind IN ('buy', 'sell')),
    quantity   NUMERIC(18,4) NOT NULL CHECK (quantity > 0),
    price      NUMERIC(14,4) NOT NULL CHECK (price >= 0),
    date       DATE,
    note       TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_stock_transactions_user ON stock_transactions (user_id, symbol);

INSERT INTO stock_transactions (user_id, symbol, broker, kind, quantity, price, date, note, created_at)
SELECT user_id, symbol, broker, 'buy', quantity, invested / quantity, buy_date, coalesce(note, 'Opening position'), created_at
FROM holdings;

DROP TABLE holdings;
