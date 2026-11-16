import datetime as dt

from services.benchmark import close_on, index_equivalent, period_changes

D = dt.date
SERIES = [(D(2025, 11, 14), 10.0), (D(2025, 11, 17), 11.0), (D(2026, 10, 16), 11.5), (D(2026, 11, 13), 11.8), (D(2026, 11, 16), 12.0)]


def test_flow_on_holiday_uses_previous_close():
    assert close_on(SERIES, D(2025, 11, 16)) == 10.0
    assert close_on(SERIES, D(2025, 11, 17)) == 11.0
    assert close_on(SERIES, D(2020, 1, 1)) == 10.0
    assert close_on([], D(2025, 1, 1)) is None


def test_index_equivalent_matches_simple_growth():
    out = index_equivalent([(D(2025, 11, 16), -100.0)], SERIES, D(2026, 11, 16))
    assert round(out["value"], 6) == 120.0, out
    assert abs(out["xirr"] - 20.0) < 0.01, out


def test_sell_removes_units():
    out = index_equivalent([(D(2025, 11, 14), -100.0), (D(2025, 11, 17), 55.0)], SERIES, D(2026, 11, 16))
    assert round(out["value"], 6) == 60.0, out


def test_undated_flows_are_skipped():
    out = index_equivalent([(None, -500.0), (D(2025, 11, 14), -100.0)], SERIES, D(2026, 11, 16))
    assert round(out["value"], 6) == 120.0, out


def test_no_flows_or_no_series():
    assert index_equivalent([], SERIES, D(2026, 11, 16)) == {"value": None, "xirr": None}
    assert index_equivalent([(D(2025, 11, 14), -1.0)], [], D(2026, 11, 16)) == {"value": None, "xirr": None}


def test_period_changes():
    out = period_changes(SERIES)
    assert round(out["day_pct"], 4) == round((12.0 / 11.8 - 1) * 100, 4)
    assert round(out["month_pct"], 4) == round((12.0 / 11.5 - 1) * 100, 4)
    assert round(out["year_pct"], 4) == 20.0
    assert period_changes([]) == {"day_pct": None, "month_pct": None, "year_pct": None}


if __name__ == "__main__":
    for name, t in list(globals().items()):
        if name.startswith("test_"):
            t()
            print(f"ok  {name}")
