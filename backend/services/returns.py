import datetime as dt


def total_return_pct(close_start: float, close_end: float) -> float:
    return (close_end - close_start) / close_start * 100


def cagr_pct(close_start: float, close_end: float, date_start: dt.date, date_end: dt.date) -> float | None:
    years = (date_end - date_start).days / 365.25
    if years < 1:
        return None
    return ((close_end / close_start) ** (1 / years) - 1) * 100


def value_of_lump_sum(amount: float, close_start: float, close_end: float) -> float:
    units = amount / close_start
    return units * close_end


def max_drawdown_pct(closes: list[float]) -> float:
    running_peak = closes[0]
    max_dd = 0.0
    for c in closes:
        running_peak = max(running_peak, c)
        dd = (c - running_peak) / running_peak
        max_dd = min(max_dd, dd)
    return max_dd * 100


def best_worst_year(dates: list[dt.date], closes: list[float]) -> tuple[dict, dict]:
    by_year: dict[int, list[float]] = {}
    for d, c in zip(dates, closes):
        by_year.setdefault(d.year, []).append(c)

    year_return = {y: (cs[-1] - cs[0]) / cs[0] * 100 for y, cs in by_year.items()}
    best_year = max(year_return, key=year_return.get)
    worst_year = min(year_return, key=year_return.get)
    return (
        {"year": best_year, "return_pct": year_return[best_year]},
        {"year": worst_year, "return_pct": year_return[worst_year]},
    )


def compute_returns(dates: list[dt.date], closes: list[float], amount: float) -> dict:
    close_start, close_end = closes[0], closes[-1]
    date_start, date_end = dates[0], dates[-1]
    best_year, worst_year = best_worst_year(dates, closes)

    return {
        "date_start": date_start,
        "date_end": date_end,
        "close_start": close_start,
        "close_end": close_end,
        "total_return_pct": total_return_pct(close_start, close_end),
        "cagr_pct": cagr_pct(close_start, close_end, date_start, date_end),
        "max_drawdown_pct": max_drawdown_pct(closes),
        "best_year": best_year,
        "worst_year": worst_year,
        "amount_invested": amount,
        "value_now": value_of_lump_sum(amount, close_start, close_end),
    }
