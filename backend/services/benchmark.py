import bisect
import calendar
import datetime as dt

from services.ledger import xirr


def close_on(series: list[tuple[dt.date, float]], day: dt.date) -> float | None:
    if not series:
        return None
    i = bisect.bisect_right([d for d, _ in series], day) - 1
    return series[max(i, 0)][1]


def months_back(day: dt.date, months: int) -> dt.date:
    y, m = divmod(day.year * 12 + day.month - 1 - months, 12)
    return dt.date(y, m + 1, min(day.day, calendar.monthrange(y, m + 1)[1]))


def _change(now: float, then: float | None) -> float | None:
    return (now / then - 1) * 100 if then else None


def period_changes(series: list[tuple[dt.date, float]]) -> dict:
    if not series:
        return {"day_pct": None, "month_pct": None, "year_pct": None}
    last_date, last = series[-1]
    prev = series[-2][1] if len(series) > 1 else None
    return {
        "day_pct": _change(last, prev),
        "month_pct": _change(last, close_on(series, months_back(last_date, 1))),
        "year_pct": _change(last, close_on(series, months_back(last_date, 12))),
    }


def index_equivalent(flows: list[tuple[dt.date | None, float]], series: list[tuple[dt.date, float]], today: dt.date) -> dict:
    dated = [(d, a) for d, a in flows if d is not None]
    if not dated or not series:
        return {"value": None, "xirr": None}
    units = sum(-a / close_on(series, d) for d, a in dated)
    value = units * series[-1][1]
    return {"value": value, "xirr": xirr(dated + [(today, value)])}
