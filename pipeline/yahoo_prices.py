import datetime as dt
import math

import pandas as pd
import yfinance as yf

from pipeline.fundamentals_source import yahoo_tickers


def _num(v) -> float | None:
    if v is None:
        return None
    v = float(v)
    return None if math.isnan(v) else v


def history_bars(df) -> list[dict]:
    if df is None or df.empty:
        return []
    bars = []
    for ts, row in df.iterrows():
        close = _num(row.get("Close"))
        if close is None:
            continue
        volume = _num(row.get("Volume"))
        bars.append({
            "datetime": ts.strftime("%Y-%m-%d %H:%M:%S"),
            "open": _num(row.get("Open")) or close,
            "high": _num(row.get("High")) or close,
            "low": _num(row.get("Low")) or close,
            "close": close,
            "volume": int(volume) if volume is not None else None,
        })
    return bars


def split_download(df, tickers: list[str]) -> dict[str, list[dict]]:
    if df is None or df.empty:
        return {t: [] for t in tickers}
    if not isinstance(df.columns, pd.MultiIndex):
        return {t: history_bars(df) if len(tickers) == 1 else [] for t in tickers}
    present = set(df.columns.get_level_values(0))
    return {t: history_bars(df[t]) if t in present else [] for t in tickers}


def daily_bars(symbol: str, exchange: str, bse_code: str | None, start: dt.date) -> list[dict]:
    for ticker in yahoo_tickers(symbol, exchange, bse_code):
        bars = history_bars(yf.Ticker(ticker).history(start=start.isoformat(), interval="1d", auto_adjust=False))
        if bars:
            return bars
    raise ValueError(f"no Yahoo Finance prices for {symbol} ({exchange}) since {start}")


def minute_bars(tickers: dict[str, str], day: dt.date) -> dict[str, list[dict]]:
    if not tickers:
        return {}
    names = sorted(set(tickers.values()))
    df = yf.download(
        names, start=day.isoformat(), end=(day + dt.timedelta(days=1)).isoformat(), interval="1m",
        group_by="ticker", auto_adjust=False, progress=False, threads=True,
    )
    by_ticker = split_download(df, names)
    return {key: by_ticker[ticker] for key, ticker in tickers.items()}
