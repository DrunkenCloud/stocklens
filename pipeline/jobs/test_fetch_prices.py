import datetime as dt

from pipeline.jobs.fetch_prices import BACKFILL_START, date_windows, incremental_from_date, normalize_row


def test_incremental_from_date():
    today = dt.date(2026, 7, 19)
    assert incremental_from_date(None, today, backfill=False) == BACKFILL_START
    assert incremental_from_date(dt.date(2026, 7, 15), today, backfill=False) == dt.date(2026, 7, 15)
    assert incremental_from_date(dt.date(2026, 7, 15), today, backfill=True) == BACKFILL_START


def test_normalize_row():
    raw = {"datetime": "2026-07-15 00:00:00", "open": "100.5", "high": "102", "low": "99", "close": "101", "volume": "5000"}
    date, open_, high, low, close, volume = normalize_row(raw)
    assert date == dt.date(2026, 7, 15)
    assert close == 101.0
    assert open_ == 100.5
    assert volume == 5000


def test_normalize_row_missing_optional_fields():
    raw = {"datetime": "2026-07-15T00:00:00.000Z", "close": "101"}
    date, open_, high, low, close, volume = normalize_row(raw)
    assert date == dt.date(2026, 7, 15)
    assert open_ is None
    assert volume is None


def test_date_windows_cover_range_without_overlap():
    d = dt.date
    assert date_windows(d(2024, 1, 1), d(2024, 1, 10), 4) == [
        (d(2024, 1, 1), d(2024, 1, 4)), (d(2024, 1, 5), d(2024, 1, 8)), (d(2024, 1, 9), d(2024, 1, 10))]
    assert date_windows(d(2024, 1, 1), d(2024, 1, 1), 4) == [(d(2024, 1, 1), d(2024, 1, 1))]


if __name__ == "__main__":
    test_incremental_from_date()
    test_normalize_row()
    test_normalize_row_missing_optional_fields()
    test_date_windows_cover_range_without_overlap()
    print("ok")
