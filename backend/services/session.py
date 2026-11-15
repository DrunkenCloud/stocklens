import datetime as dt

IST = dt.timezone(dt.timedelta(hours=5, minutes=30))


def session_state(captured_at: dt.datetime | None, invalid_at: dt.datetime | None, now: dt.datetime) -> str:
    if captured_at is None:
        return "never"
    if invalid_at is not None or captured_at.astimezone(IST).date() < now.astimezone(IST).date():
        return "expired"
    return "valid"
