CREATE TABLE market_indices (
    symbol   TEXT PRIMARY KEY,
    name     TEXT NOT NULL,
    position INT NOT NULL
);

INSERT INTO market_indices (symbol, name, position) VALUES
    ('^NSEI', 'Nifty 50', 1),
    ('^BSESN', 'Sensex', 2),
    ('^NSMIDCP', 'Nifty Next 50', 3),
    ('NIFTYMIDCAP150.NS', 'Nifty Midcap 150', 4),
    ('NIFTYSMLCAP250.NS', 'Nifty Smallcap 250', 5),
    ('^CRSLDX', 'Nifty 500', 6);

CREATE TABLE index_prices (
    symbol TEXT NOT NULL REFERENCES market_indices(symbol),
    date   DATE NOT NULL,
    close  NUMERIC(14,4) NOT NULL,
    PRIMARY KEY (symbol, date)
);
