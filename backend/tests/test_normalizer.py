import pytest
from stocklighthouse.normalizer import normalize
from stocklighthouse.models import StockKPIs

def test_normalize_minimal():
    raw = {
        "regularMarketPrice": 100.0,
        "previousClose": 95.0,
        "marketCap": 1_000_000_000,
        "trailingPE": 20.0,
        "priceToBook": 3.0,
        "dividendYield": 0.02,
        "sector": "Technology"
    }
    res = normalize("FOO", raw)
    assert isinstance(res, StockKPIs)
    assert res.price == 100.0
    assert pytest.approx(res.change_pct, rel=1e-3) == (100.0 - 95.0) / 95.0 * 100
    assert res.sector == "Technology"

def test_normalize_missing_previous_close():
    raw = {
        "regularMarketPrice": 50.0,
        "marketCap": 200_000_000
    }
    res = normalize("BAR", raw)
    assert res.price == 50.0
    # change_pct may be None if previousClose is missing
    assert res.change_pct is None