import datetime as dt

FACTORS = (2, 3, 4, 5, 10, 20)
TOLERANCE = 0.06


def detect_splits(closes: list[tuple[dt.date, float]]) -> list[tuple[dt.date, int]]:
    found = []
    for (_, prev), (day, cur) in zip(closes, closes[1:]):
        if not prev or not cur:
            continue
        ratio = prev / cur
        for factor in FACTORS:
            if abs(ratio / factor - 1) < TOLERANCE:
                found.append((day, factor))
                break
    return found
