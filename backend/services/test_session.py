"""Self-check for session_state. Run (from backend/): python -m services.test_session"""
import datetime as dt

from services.session import session_state

IST = dt.timezone(dt.timedelta(hours=5, minutes=30))


def at(y, m, d, hh, mm=0):
    return dt.datetime(y, m, d, hh, mm, tzinfo=IST)


def test_never_logged_in():
    assert session_state(None, None, at(2026, 11, 15, 10)) == "never"


def test_same_ist_day_is_valid():
    assert session_state(at(2026, 11, 15, 0, 5), None, at(2026, 11, 15, 23, 59)) == "valid"


def test_previous_ist_day_is_expired_even_if_under_24h():
    # Breeze tokens die at midnight IST; 23:50 -> 00:10 is 20 minutes but a new day.
    assert session_state(at(2026, 11, 14, 23, 50), None, at(2026, 11, 15, 0, 10)) == "expired"


def test_marked_invalid_is_expired():
    assert session_state(at(2026, 11, 15, 9), at(2026, 11, 15, 9, 30), at(2026, 11, 15, 10)) == "expired"


def test_utc_timestamps_compare_by_ist_date():
    # 20:00 UTC on the 14th = 01:30 IST on the 15th -> same IST day as 10:00 IST on the 15th
    captured = dt.datetime(2026, 11, 14, 20, 0, tzinfo=dt.timezone.utc)
    assert session_state(captured, None, at(2026, 11, 15, 10)) == "valid"


if __name__ == "__main__":
    for t in (test_never_logged_in, test_same_ist_day_is_valid, test_previous_ist_day_is_expired_even_if_under_24h,
              test_marked_invalid_is_expired, test_utc_timestamps_compare_by_ist_date):
        t()
        print(f"ok  {t.__name__}")
