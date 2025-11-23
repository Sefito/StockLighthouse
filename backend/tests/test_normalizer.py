import pytest
from stocklighthouse.normalizer import normalize, _safe_float, _safe_string, _infer_market
from stocklighthouse.models import StockKPIs

def test_normalize_minimal():
    """Test normalization with minimal complete data."""
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
    """Test that change_pct is None when previous_close is missing."""
    raw = {
        "regularMarketPrice": 50.0,
        "marketCap": 200_000_000
    }
    res = normalize("BAR", raw)
    assert res.price == 50.0
    # change_pct should be None if previousClose is missing
    assert res.change_pct is None


def test_normalize_zero_previous_close():
    """Test that change_pct is None when previous_close is zero (avoid division by zero)."""
    raw = {
        "regularMarketPrice": 50.0,
        "previousClose": 0.0,
        "marketCap": 200_000_000
    }
    res = normalize("ZERO", raw)
    assert res.price == 50.0
    assert res.previous_close == 0.0
    assert res.change_pct is None  # Should not calculate to avoid division by zero


def test_normalize_negative_previous_close():
    """Test handling of negative previous_close (should not calculate change_pct)."""
    raw = {
        "regularMarketPrice": 50.0,
        "previousClose": -10.0
    }
    res = normalize("NEG", raw)
    assert res.price == 50.0
    assert res.previous_close == -10.0
    assert res.change_pct is None  # Should not calculate for negative values


def test_normalize_empty_data():
    """Test normalization with completely empty data dictionary."""
    raw = {}
    res = normalize("EMPTY", raw)
    assert res.symbol == "EMPTY"
    assert res.price is None
    assert res.previous_close is None
    assert res.change_pct is None
    assert res.market_cap is None
    assert res.pe_ratio is None
    assert res.pb_ratio is None
    assert res.dividend_yield is None
    assert res.sector is None
    assert res.market is None
    assert res.exchange is None
    assert res.currency is None
    assert res.industry is None


def test_normalize_null_values():
    """Test that None/null values in raw data are handled gracefully."""
    raw = {
        "regularMarketPrice": None,
        "previousClose": None,
        "marketCap": None,
        "trailingPE": None,
        "priceToBook": None,
        "dividendYield": None,
        "sector": None,
        "industry": None,
        "exchange": None,
        "currency": None
    }
    res = normalize("NULL", raw)
    assert res.symbol == "NULL"
    assert res.price is None
    assert res.previous_close is None
    assert res.market_cap is None


def test_normalize_all_fields():
    """Test normalization with all fields populated."""
    raw = {
        "regularMarketPrice": 150.25,
        "previousClose": 148.50,
        "marketCap": 2_400_000_000_000,
        "trailingPE": 28.5,
        "priceToBook": 40.2,
        "dividendYield": 0.005,
        "sector": "Technology",
        "industry": "Consumer Electronics",
        "exchange": "NMS",
        "currency": "USD"
    }
    res = normalize("AAPL", raw)
    assert res.symbol == "AAPL"
    assert res.price == 150.25
    assert res.previous_close == 148.50
    assert pytest.approx(res.change_pct, rel=1e-3) == ((150.25 - 148.50) / 148.50) * 100
    assert res.market_cap == 2_400_000_000_000
    assert res.pe_ratio == 28.5
    assert res.pb_ratio == 40.2
    assert res.dividend_yield == 0.005
    assert res.sector == "Technology"
    assert res.industry == "Consumer Electronics"
    assert res.exchange == "NMS"
    assert res.currency == "USD"
    assert res.market == "us_market"


def test_normalize_price_fallback():
    """Test that normalize falls back to currentPrice when regularMarketPrice is missing."""
    raw = {
        "currentPrice": 75.5,
        "previousClose": 74.0,
        "sector": "Healthcare"
    }
    res = normalize("MED", raw)
    assert res.price == 75.5
    assert pytest.approx(res.change_pct, rel=1e-3) == ((75.5 - 74.0) / 74.0) * 100


def test_normalize_pe_ratio_fallback():
    """Test PE ratio fallback to forwardPE when trailingPE is missing."""
    raw = {
        "regularMarketPrice": 100.0,
        "forwardPE": 25.0
    }
    res = normalize("FWD", raw)
    assert res.pe_ratio == 25.0


def test_normalize_dividend_yield_percentage_conversion():
    """Test that dividend yield > 0.01 is converted from percentage to decimal."""
    raw = {
        "regularMarketPrice": 50.0,
        "dividendYield": 2.5  # 2.5% as a number > 0.01
    }
    res = normalize("DIV", raw)
    assert pytest.approx(res.dividend_yield, rel=1e-6) == 0.025


def test_normalize_dividend_yield_decimal():
    """Test that dividend yield <= 0.01 is kept as-is (already a decimal)."""
    raw = {
        "regularMarketPrice": 50.0,
        "dividendYield": 0.005  # Already as decimal (0.5%)
    }
    res = normalize("DIV2", raw)
    assert pytest.approx(res.dividend_yield, rel=1e-6) == 0.005


def test_normalize_dividend_yield_yfinance_format():
    """Test dividend yield conversion with typical yfinance format (0.38 = 0.38%)."""
    raw = {
        "regularMarketPrice": 271.49,
        "dividendYield": 0.38  # yfinance format: 0.38 means 0.38%
    }
    res = normalize("YFIN", raw)
    assert pytest.approx(res.dividend_yield, rel=1e-6) == 0.0038


def test_normalize_symbol_case_normalization():
    """Test that symbol is normalized to uppercase."""
    raw = {"regularMarketPrice": 100.0}
    res = normalize("aapl", raw)
    assert res.symbol == "AAPL"
    
    res2 = normalize("  MsFt  ", raw)
    assert res2.symbol == "MSFT"


def test_normalize_market_inference_us():
    """Test market inference for US exchanges."""
    for exchange in ["NMS", "NYSE", "NYQ", "NASDAQ", "AMEX"]:
        raw = {"regularMarketPrice": 100.0, "exchange": exchange}
        res = normalize("TEST", raw)
        assert res.market == "us_market", f"Failed for exchange {exchange}"
        assert res.exchange == exchange


def test_normalize_market_inference_uk():
    """Test market inference for UK exchanges."""
    raw = {"regularMarketPrice": 100.0, "exchange": "LSE"}
    res = normalize("UK", raw)
    assert res.market == "uk_market"
    assert res.exchange == "LSE"


def test_normalize_market_inference_eu():
    """Test market inference for European exchanges."""
    for exchange in ["FRA", "PAR", "AMS"]:
        raw = {"regularMarketPrice": 100.0, "exchange": exchange}
        res = normalize("EU", raw)
        assert res.market == "eu_market", f"Failed for exchange {exchange}"


def test_normalize_market_inference_asian():
    """Test market inference for Asian exchanges."""
    for exchange in ["TYO", "HKG", "SHH"]:
        raw = {"regularMarketPrice": 100.0, "exchange": exchange}
        res = normalize("ASIA", raw)
        assert res.market == "asian_market", f"Failed for exchange {exchange}"


def test_normalize_market_inference_unknown():
    """Test that unknown exchanges result in None market."""
    raw = {"regularMarketPrice": 100.0, "exchange": "UNKNOWN_EXCH"}
    res = normalize("UNK", raw)
    assert res.market is None
    assert res.exchange == "UNKNOWN_EXCH"


def test_normalize_string_fields_whitespace():
    """Test that string fields are trimmed of whitespace."""
    raw = {
        "regularMarketPrice": 100.0,
        "sector": "  Technology  ",
        "industry": "  Software  ",
        "exchange": " NMS ",
        "currency": " USD "
    }
    res = normalize("TRIM", raw)
    assert res.sector == "Technology"
    assert res.industry == "Software"
    assert res.exchange == "NMS"
    assert res.currency == "USD"


def test_normalize_string_fields_empty():
    """Test that empty string fields become None."""
    raw = {
        "regularMarketPrice": 100.0,
        "sector": "",
        "industry": "   ",  # Only whitespace
        "exchange": "",
        "currency": ""
    }
    res = normalize("EMPTY_STR", raw)
    assert res.sector is None
    assert res.industry is None
    assert res.exchange is None
    assert res.currency is None
    assert res.market is None  # Should be None since exchange is None


def test_safe_float_nan():
    """Test that NaN values are converted to None."""
    assert _safe_float(float('nan')) is None


def test_safe_float_infinity():
    """Test that infinity values are converted to None."""
    assert _safe_float(float('inf')) is None
    assert _safe_float(float('-inf')) is None


def test_safe_float_string_conversion():
    """Test string to float conversion."""
    assert _safe_float("123.45") == 123.45
    assert _safe_float("invalid") is None


def test_safe_float_none():
    """Test that None input returns None."""
    assert _safe_float(None) is None


def test_safe_string_none():
    """Test that None input returns None."""
    assert _safe_string(None) is None


def test_safe_string_empty():
    """Test that empty strings return None."""
    assert _safe_string("") is None
    assert _safe_string("   ") is None


def test_safe_string_number_conversion():
    """Test that numbers are converted to strings."""
    assert _safe_string(123) == "123"
    assert _safe_string(45.67) == "45.67"


def test_infer_market_none():
    """Test that None exchange returns None market."""
    assert _infer_market(None) is None


def test_infer_market_empty():
    """Test that empty exchange returns None market."""
    assert _infer_market("") is None


def test_normalize_invalid_numeric_types():
    """Test that invalid numeric types (strings, objects) are handled."""
    raw = {
        "regularMarketPrice": "not_a_number",
        "previousClose": "also_not_a_number",
        "marketCap": {"complex": "object"},
        "trailingPE": [1, 2, 3]
    }
    res = normalize("INVALID", raw)
    assert res.price is None
    assert res.previous_close is None
    assert res.market_cap is None
    assert res.pe_ratio is None


def test_normalize_pb_ratio_alternate_field():
    """Test PB ratio extraction from alternate field name."""
    raw = {
        "regularMarketPrice": 100.0,
        "priceBookRatio": 5.5
    }
    res = normalize("PBR", raw)
    assert res.pb_ratio == 5.5


def test_normalize_real_world_sample():
    """Test normalization with real-world-like data (based on actual yfinance output)."""
    raw = {
        "regularMarketPrice": 271.49,
        "previousClose": 266.25,
        "marketCap": 4029017227264,
        "trailingPE": 36.344044,
        "priceToBook": 54.39591,
        "dividendYield": 0.0038,
        "sector": "Technology",
        "industry": "Consumer Electronics",
        "exchange": "NMS",
        "currency": "USD"
    }
    res = normalize("AAPL", raw)
    assert res.symbol == "AAPL"
    assert res.price == 271.49
    assert res.previous_close == 266.25
    assert pytest.approx(res.change_pct, rel=1e-2) == ((271.49 - 266.25) / 266.25) * 100
    assert res.market_cap == 4029017227264
    assert res.pe_ratio == 36.344044
    assert res.pb_ratio == 54.39591
    assert res.dividend_yield == 0.0038
    assert res.sector == "Technology"
    assert res.industry == "Consumer Electronics"
    assert res.exchange == "NMS"
    assert res.currency == "USD"
    assert res.market == "us_market"