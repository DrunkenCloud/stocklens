from pipeline.holdings import parse_portfolio_holdings


def row(code, qty, avg, exchange="NSE"):
    return {"stock_code": code, "exchange_code": exchange, "quantity": qty, "average_price": avg,
            "current_market_price": "0", "booked_profit_loss": "0"}


def test_parses_documented_shape():
    resp = {"Status": 200, "Error": None, "Success": [row("RELIND", "10", "1250.5"), row("ITC", "100", "410")]}
    assert parse_portfolio_holdings(resp) == [("ITC", 100.0, 410.0), ("RELIND", 10.0, 1250.5)]


def test_merges_duplicate_codes_with_qty_weighted_average():
    resp = {"Success": [row("ITC", "10", "400"), row("ITC", "30", "440", exchange="BSE")]}
    assert parse_portfolio_holdings(resp) == [("ITC", 40.0, 430.0)]


def test_drops_zero_quantity_and_derivatives():
    resp = {"Success": [row("ITC", "0", "400"), row("NIFTY", "50", "100", exchange="NFO"), row("TCS", "1", "3000")]}
    assert parse_portfolio_holdings(resp) == [("TCS", 1.0, 3000.0)]


def test_empty_portfolio_is_an_empty_list():
    assert parse_portfolio_holdings({"Success": [], "Status": 200, "Error": None}) == []


def test_unexpected_shape_raises_with_field_names():
    try:
        parse_portfolio_holdings({"Success": [{"symbol": "ITC", "qty": "5"}]})
    except ValueError as e:
        assert "qty" in str(e) and "symbol" in str(e), e
    else:
        raise AssertionError("expected ValueError")


def test_error_payload_raises_instead_of_returning_no_holdings():
    for resp in ({"Success": None, "Status": 500, "Error": "Something broke"}, {"Success": None, "Error": None}, None):
        try:
            parse_portfolio_holdings(resp)
        except ValueError:
            continue
        raise AssertionError(f"expected ValueError for {resp!r}")


if __name__ == "__main__":
    for t in (test_parses_documented_shape, test_merges_duplicate_codes_with_qty_weighted_average,
              test_drops_zero_quantity_and_derivatives, test_empty_portfolio_is_an_empty_list,
              test_unexpected_shape_raises_with_field_names, test_error_payload_raises_instead_of_returning_no_holdings):
        t()
        print(f"ok  {t.__name__}")
