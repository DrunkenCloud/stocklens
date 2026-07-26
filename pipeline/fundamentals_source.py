"""Fundamentals from Yahoo Finance (yfinance). See 06_DECISIONS.md D8 for why
this source was picked over hand-scraping Screener.in/NSE (02_DATA_SOURCES.md
left the exact source open - "pick one primary, keep a fallback").

Field scaling below is confirmed against live data (RELIANCE/ITC/TCS/HDFCBANK),
not assumed from docs - see the M1 Breeze lesson on why that matters:
- roe, op_margin, rev_growth_1y come back as fractions (0.29 = 29%) -> *100.
- debt_to_equity comes back pre-scaled by 100. Confirmed via TCS/ITC, both
  famously near-zero-debt: their raw values (10.2, 3.3) only make sense as
  "ratio * 100"; as a plain ratio they'd imply absurd 10x/3x leverage.
- dividend_yield is already a plain percent (ITC's 5.64 matches its real
  ~5.6% yield directly, no scaling needed).
- pe, pb, rev_ttm, market_cap: plain ratios/amounts, used as-is.
"""
import yfinance as yf


def _pct(fraction: float | None) -> float | None:
    return fraction * 100 if fraction is not None else None


def _cagr_from_endpoints(oldest: float, latest: float, years: int) -> float | None:
    """Pure: CAGR% between two revenue figures years apart."""
    if oldest is None or latest is None or oldest <= 0:
        return None
    return ((latest / oldest) ** (1 / years) - 1) * 100


def _rev_cagr_3y(ticker: yf.Ticker) -> float | None:
    try:
        revenue = ticker.financials.loc["Total Revenue"].dropna().sort_index()
    except (KeyError, AttributeError):
        return None
    if len(revenue) < 4:
        return None  # need ~4 annual figures to span a 3yr CAGR
    return _cagr_from_endpoints(revenue.iloc[-4], revenue.iloc[-1], years=3)


def fetch_fundamentals(symbol: str) -> dict:
    """symbol: plain NSE ticker (companies.symbol). Yahoo's NSE convention is
    '{ticker}.NS' - confirmed live, no per-symbol mapping needed (unlike Breeze).
    Raises ValueError if Yahoo has no listing for the symbol; caller isolates
    per-symbol failures.
    """
    ticker = yf.Ticker(f"{symbol}.NS")
    info = ticker.info
    if info.get("regularMarketPrice") is None:
        raise ValueError(f"no Yahoo Finance data for {symbol}.NS")

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
