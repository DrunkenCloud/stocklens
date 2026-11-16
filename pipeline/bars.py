import datetime as dt


def day_bar(bars: list[dict], day: dt.date) -> dict | None:
    prefix = day.isoformat()
    today = sorted((b for b in bars if b["datetime"].startswith(prefix)), key=lambda b: b["datetime"])
    if not today:
        return None
    return {
        "datetime": today[0]["datetime"],
        "open": float(today[0]["open"]),
        "high": max(float(b["high"]) for b in today),
        "low": min(float(b["low"]) for b in today),
        "close": float(today[-1]["close"]),
        "volume": sum(int(float(b.get("volume") or 0)) for b in today),
    }
