import datetime as dt

from pipeline.splits import detect_splits

D = dt.date


def series(closes):
    return [(D(2025, 1, 1) + dt.timedelta(days=i), c) for i, c in enumerate(closes)]


def test_one_to_five_split_is_detected():
    assert detect_splits(series([500, 505, 498, 100.2, 101, 99])) == [(D(2025, 1, 4), 5)]


def test_bonus_two_for_one_is_a_factor_of_three():
    assert detect_splits(series([240, 243, 81.5, 80])) == [(D(2025, 1, 3), 3)]


def test_one_for_one_bonus_halves_the_price():
    assert detect_splits(series([1700, 1690, 846, 850])) == [(D(2025, 1, 3), 2)]


def test_ordinary_crash_is_not_a_split():
    assert detect_splits(series([100, 99, 72, 70])) == []


def test_drop_far_from_any_ratio_is_not_a_split():
    assert detect_splits(series([100, 100, 41, 40])) == []


if __name__ == "__main__":
    for t in (test_one_to_five_split_is_detected, test_bonus_two_for_one_is_a_factor_of_three,
              test_one_for_one_bonus_halves_the_price, test_ordinary_crash_is_not_a_split, test_drop_far_from_any_ratio_is_not_a_split):
        t()
        print(f"ok  {t.__name__}")
