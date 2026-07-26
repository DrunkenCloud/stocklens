"""Self-check for pure logic in fundamentals_source.py. Run: python -m pipeline.test_fundamentals_source"""
from pipeline.fundamentals_source import _cagr_from_endpoints, _pct


def test_pct():
    assert abs(_pct(0.2934) - 29.34) < 1e-9
    assert _pct(None) is None


def test_cagr_from_endpoints():
    # revenue doubling over 3 years -> ~25.99% CAGR
    result = _cagr_from_endpoints(100, 200, years=3)
    assert abs(result - 25.99) < 0.1
    assert _cagr_from_endpoints(None, 200, years=3) is None
    assert _cagr_from_endpoints(0, 200, years=3) is None
    assert _cagr_from_endpoints(-10, 200, years=3) is None


if __name__ == "__main__":
    test_pct()
    test_cagr_from_endpoints()
    print("ok")
