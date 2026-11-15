ALTER TABLE mf_schemes
    ADD COLUMN portfolio_id TEXT,
    ADD COLUMN portfolio_as_of DATE;

CREATE TABLE fund_portfolio_holdings (
    portfolio_id TEXT NOT NULL,
    position     INT NOT NULL,
    as_of        DATE NOT NULL,
    isin         TEXT,
    name         TEXT NOT NULL,
    holding_type TEXT,
    industry     TEXT,
    pct_nav      NUMERIC(10,4) NOT NULL,
    PRIMARY KEY (portfolio_id, position)
);
CREATE INDEX idx_fund_portfolio_holdings_isin ON fund_portfolio_holdings (isin);
