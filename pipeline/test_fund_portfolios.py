from pipeline.fund_portfolios import portfolio_rows

DOC = {
    "portfolio_id": "122639",
    "meta": {"as_of": "2026-10-31"},
    "holdings": [
        {"holding_type": "equity", "instrument": "HDFC Bank Limited", "isin": "INE040A01034", "industry": "Banks", "pct_nav": 7.49},
        {"holding_type": "money_market", "instrument": "Canara Bank (18/12/2026)", "isin": "INE476A16XX1", "industry": None, "pct_nav": 0.29},
        {"holding_type": "cash", "instrument": "Net Receivables", "isin": None, "industry": None, "pct_nav": None},
        {"holding_type": "equity", "instrument": "  Alphabet Inc A  ", "isin": "US02079K3059", "industry": "", "pct_nav": "3.10"},
    ],
}


def test_rows_keep_weights_and_drop_unweighted():
    rows = portfolio_rows(DOC)
    assert rows == [
        {"position": 0, "isin": "INE040A01034", "name": "HDFC Bank Limited", "holding_type": "equity", "industry": "Banks", "pct_nav": 7.49},
        {"position": 1, "isin": "INE476A16XX1", "name": "Canara Bank (18/12/2026)", "holding_type": "money_market", "industry": None, "pct_nav": 0.29},
        {"position": 3, "isin": "US02079K3059", "name": "Alphabet Inc A", "holding_type": "equity", "industry": None, "pct_nav": 3.10},
    ], rows


if __name__ == "__main__":
    test_rows_keep_weights_and_drop_unweighted()
    print("ok  test_rows_keep_weights_and_drop_unweighted")
