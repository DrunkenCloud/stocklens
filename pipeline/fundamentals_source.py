import yfinance as yf


def _pct(fraction: float | None) -> float | None:
    return fraction * 100 if fraction is not None else None


def _cagr_from_endpoints(oldest: float, latest: float, years: int) -> float | None:
    if oldest is None or latest is None or oldest <= 0:
        return None
    return ((latest / oldest) ** (1 / years) - 1) * 100


def _rev_cagr_3y(ticker: yf.Ticker) -> float | None:
    try:
        revenue = ticker.financials.loc["Total Revenue"].dropna().sort_index()
    except (KeyError, AttributeError):
        return None
    if len(revenue) < 4:
        return None
    return _cagr_from_endpoints(revenue.iloc[-4], revenue.iloc[-1], years=3)


def yahoo_tickers(symbol: str, exchange: str, bse_code: str | None) -> list[str]:
    if exchange == "NSE":
        return [f"{symbol}.NS"]
    return [f"{symbol}.BO"] + ([f"{bse_code}.BO"] if bse_code else [])


def fetch_fundamentals(symbol: str, exchange: str = "NSE", bse_code: str | None = None) -> dict:
    for name in yahoo_tickers(symbol, exchange, bse_code):
        ticker = yf.Ticker(name)
        info = ticker.info
        if info.get("regularMarketPrice") is not None:
            break
    else:
        raise ValueError(f"no Yahoo Finance data for {symbol} ({exchange})")

    debt_to_equity = info.get("debtToEquity")

    return {
        "pe": info.get("trailingPE"),
        "pb": info.get("priceToBook"),
        "roe": _pct(info.get("returnOnEquity")),
        "op_margin": _pct(info.get("operatingMargins")),
        "rev_ttm": info.get("totalRevenue"),
        "rev_growth_1y": _pct(info.get("revenueGrowth")),
        "rev_cagr_3y": _rev_cagr_3y(ticker),
        "debt_to_equity": debt_to_equity / 100 if debt_to_equity is not None else None,
        "dividend_yield": info.get("dividendYield"),
        "market_cap": info.get("marketCap"),
        "raw": info,
    }
