import math

import pandas as pd

from pipeline.yahoo_prices import history_bars, split_download


def frame(rows, tz="Asia/Kolkata"):
    index = pd.DatetimeIndex([pd.Timestamp(r[0], tz=tz) for r in rows], name="Date")
    return pd.DataFrame([r[1:] for r in rows], index=index, columns=["Open", "High", "Low", "Close", "Adj Close", "Volume"])


def test_history_bars_shape():
    df = frame([("2026-11-13 00:00", 1.0, 2.0, 0.5, 1.5, 1.4, 5.0)])
    assert history_bars(df) == [
        {"datetime": "2026-11-13 00:00:00", "open": 1.0, "high": 2.0, "low": 0.5, "close": 1.5, "volume": 5}
    ], history_bars(df)


def test_empty_history_gives_no_bars():
    assert history_bars(pd.DataFrame()) == []
    assert history_bars(None) == []


def test_nan_rows_dropped():
    df = frame([("2026-11-13 09:15", 1.0, 2.0, 0.5, math.nan, 1.4, 5.0), ("2026-11-13 09:16", 1.0, 2.0, 0.5, 1.7, 1.4, math.nan)])
    bars = history_bars(df)
    assert [b["close"] for b in bars] == [1.7], bars
    assert bars[0]["volume"] is None


def test_split_download_by_ticker():
    one = frame([("2026-11-13 09:15", 1.0, 2.0, 0.5, 1.5, 1.4, 5.0)])
    two = frame([("2026-11-13 09:15", 9.0, 9.0, 9.0, math.nan, 9.0, 1.0)])
    both = pd.concat({"BEL.NS": one, "^NSEI": two}, axis=1)
    out = split_download(both, ["BEL.NS", "^NSEI", "MISSING.NS"])
    assert [b["close"] for b in out["BEL.NS"]] == [1.5]
    assert out["^NSEI"] == [] and out["MISSING.NS"] == []


if __name__ == "__main__":
    for name, t in list(globals().items()):
        if name.startswith("test_"):
            t()
            print(f"ok  {name}")
