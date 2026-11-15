import datetime as dt

from pipeline.jobs.fetch_live import day_bar


def bar(t, o, h, l, c, v):
    return {"datetime": f"2026-11-13 {t}", "open": str(o), "high": str(h), "low": str(l), "close": str(c), "volume": str(v)}


def test_minute_bars_merge_into_todays_daily_bar():
    bars = [bar("09:16:00", 101, 103, 100, 102, 10), bar("09:15:00", 100, 101, 99, 101, 5), bar("09:17:00", 102, 104, 101, 103.5, 7)]
    assert day_bar(bars, dt.date(2026, 11, 13)) == {
        "datetime": "2026-11-13 09:15:00", "open": 100.0, "high": 104.0, "low": 99.0, "close": 103.5, "volume": 22}


def test_bars_from_other_days_are_ignored_and_no_bars_means_no_row():
    bars = [{**bar("15:29:00", 90, 91, 89, 90.5, 3), "datetime": "2026-11-12 15:29:00"}, bar("09:15:00", 100, 101, 99, 101, 5)]
    assert day_bar(bars, dt.date(2026, 11, 13))["open"] == 100.0
    assert day_bar(bars[:1], dt.date(2026, 11, 13)) is None
    assert day_bar([], dt.date(2026, 11, 13)) is None


if __name__ == "__main__":
    for name, t in list(globals().items()):
        if name.startswith("test_"):
            t()
            print(f"ok  {name}")
