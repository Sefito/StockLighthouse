# Backend Tests

This directory contains unit tests for the StockLighthouse backend components.

## Test Structure

```
tests/
├── test_analyzer.py      # Tests for sector aggregation and analytics (27 tests)
├── test_ingestor.py      # Tests for YFinance data ingestion (19 tests)
├── test_normalizer.py    # Tests for data normalization (32 tests)
└── pytest.ini            # Pytest configuration
```

**Total: 78 tests**

## Running Tests

### Prerequisites

```bash
cd backend
pip install -r requirements.txt
```

### Run All Tests

```bash
cd backend
pytest
```

The `pytest.ini` configuration automatically sets `PYTHONPATH=src`, so you don't need to set it manually.

### Run Specific Test File

```bash
cd backend
pytest tests/test_normalizer.py -v
```

### Run Specific Test

```bash
cd backend
pytest tests/test_normalizer.py::test_normalize_minimal -v
```

### Run Tests with Coverage

```bash
cd backend
pytest --cov=stocklighthouse --cov-report=html
```

View coverage report: `open htmlcov/index.html`

### Run Tests in Parallel

```bash
cd backend
pip install pytest-xdist
pytest -n auto
```

## Test Categories

### Normalizer Tests (32 tests)

Tests for `stocklighthouse/normalizer.py`:

**Edge Cases:**
- Missing fields handling
- Zero/negative values
- NaN and infinity handling
- Empty data dictionaries
- Null values

**Type Safety:**
- Invalid numeric types
- String conversions
- Whitespace handling

**Feature Tests:**
- Market inference from exchange codes
- Dividend yield conversion (percentage to decimal)
- Price field fallbacks
- PE ratio fallbacks
- Symbol normalization

**Real-World:**
- Actual yfinance data samples
- Complete data sets

### Analyzer Tests (27 tests)

Tests for `stocklighthouse/analyzer.py`:

**Sector Aggregation:**
- Empty lists
- Single/multiple stocks
- Median calculations
- None value handling
- Unknown sector grouping
- Top tickers by market cap
- Average dividend yield
- Result sorting

**Weighted Averages:**
- PE ratio weighted by market cap
- Per-sector weighted averages
- None value handling
- Zero market cap handling

**Real-World Scenarios:**
- Multi-sector analysis
- Complex aggregations

### Ingestor Tests (19 tests)

Tests for `stocklighthouse/ingest/yfinance_ingestor.py`:

**Cache Functionality:**
- Cache entry expiration
- Cache hit/miss
- Cache storage and retrieval
- Cache clearing

**Data Fetching:**
- Successful fetches
- Fallback to fast_info
- Missing ticker handling
- Partial data handling

**Retry Logic:**
- Exponential backoff
- Retry exhaustion
- Network error handling

**Batch Operations:**
- Multiple symbol fetching
- Cache utilization
- Symbol normalization

## Writing New Tests

### Test Naming Convention

- Test files: `test_<module>.py`
- Test functions: `test_<function>_<scenario>`
- Test classes: `Test<ClassName>`

Example:
```python
def test_normalize_handles_missing_data():
    """Test that normalizer handles missing data gracefully."""
    pass
```

### Test Structure

```python
import pytest
from stocklighthouse.normalizer import normalize

def test_normalize_minimal():
    """Test normalization with minimal complete data."""
    # Arrange
    raw = {
        "regularMarketPrice": 100.0,
        "previousClose": 95.0,
    }
    
    # Act
    result = normalize("FOO", raw)
    
    # Assert
    assert result.price == 100.0
    assert result.previous_close == 95.0
```

### Using Fixtures

```python
import pytest

@pytest.fixture
def sample_stock_data():
    """Provide sample stock data for tests."""
    return {
        "regularMarketPrice": 150.0,
        "previousClose": 148.0,
        "marketCap": 2000000000000,
        "sector": "Technology"
    }

def test_with_fixture(sample_stock_data):
    """Test using fixture data."""
    result = normalize("AAPL", sample_stock_data)
    assert result.sector == "Technology"
```

### Mocking External APIs

```python
from unittest.mock import Mock, patch

@patch('stocklighthouse.ingest.yfinance_ingestor.yf.Ticker')
def test_fetch_ticker(mock_ticker_class):
    """Test ticker fetching with mocked yfinance."""
    # Setup mock
    mock_ticker = Mock()
    mock_ticker.info = {"regularMarketPrice": 150.0}
    mock_ticker_class.return_value = mock_ticker
    
    # Test
    ingestor = YFinanceIngestor()
    result = ingestor.fetch_single("AAPL")
    
    # Assert
    assert result.success is True
```

### Parametrized Tests

```python
import pytest

@pytest.mark.parametrize("exchange,expected_market", [
    ("NMS", "us_market"),
    ("NYSE", "us_market"),
    ("LSE", "uk_market"),
    ("TYO", "asian_market"),
])
def test_market_inference(exchange, expected_market):
    """Test market inference for various exchanges."""
    result = _infer_market(exchange)
    assert result == expected_market
```

## Test Coverage Goals

### Current Coverage
- **Normalizer:** ~95% (32 tests)
- **Analyzer:** ~90% (27 tests)
- **Ingestor:** ~85% (19 tests)

### Target Coverage
- Overall: >80%
- Critical modules: >90%
- Utility functions: >95%

## Continuous Integration

Tests run automatically on:
- Push to `master` branch
- Pull requests to `master` branch

CI configuration: `.github/workflows/agents_ci.yml`

### CI Test Command

```bash
cd backend
PYTHONPATH=src pytest tests/ -v
```

## Debugging Tests

### Run with Detailed Output

```bash
pytest -vv
```

### Show Print Statements

```bash
pytest -s
```

### Stop on First Failure

```bash
pytest -x
```

### Run Last Failed Tests

```bash
pytest --lf
```

### Debug with pdb

```bash
pytest --pdb
```

This will drop into debugger on failure.

## Best Practices

### DO ✅

- **Write descriptive test names** that explain what's being tested
- **Use docstrings** to document test purpose
- **Test edge cases** (None, empty, zero, negative)
- **Mock external dependencies** (yfinance, network calls)
- **Keep tests independent** - no test should depend on another
- **Use fixtures** for reusable test data
- **Assert specific values** rather than just "truthy"
- **Test error conditions** and exceptions

### DON'T ❌

- **Don't make real API calls** - always mock external services
- **Don't use time.sleep()** - use proper waits or mocks
- **Don't test implementation details** - test behavior
- **Don't write brittle tests** that break on minor changes
- **Don't skip tests** without good reason
- **Don't ignore warnings** - fix or suppress appropriately

## Troubleshooting

### Import Errors

**Problem:** `ModuleNotFoundError: No module named 'stocklighthouse'`

**Solution:** Run from backend directory:
```bash
cd backend
pytest
```

The `pytest.ini` sets `PYTHONPATH=src` automatically.

### Mock Not Working

**Problem:** Mock isn't being used

**Solution:** Ensure you're patching the correct import path:
```python
# Correct - patch where it's used
@patch('stocklighthouse.ingest.yfinance_ingestor.yf.Ticker')

# Wrong - patch where it's defined
@patch('yfinance.Ticker')
```

### Flaky Tests

**Problem:** Tests pass/fail intermittently

**Solution:**
- Remove time-dependent logic
- Mock time/dates
- Ensure test isolation
- Check for shared state

### Slow Tests

**Problem:** Tests take too long

**Solution:**
- Use mocks instead of real API calls
- Run tests in parallel: `pytest -n auto`
- Profile slow tests: `pytest --durations=10`

## Related Documentation

- [Main Testing Guide](../../tests/README.md)
- [QA Checklist](../../tests/QA_CHECKLIST.md)
- [API Documentation](../INGESTOR_README.md)
- [Normalizer Documentation](../../NORMALIZER_README.md)

## Contributing

When adding new tests:

1. Follow existing test patterns
2. Maintain high coverage (>80%)
3. Write clear, descriptive names
4. Add docstrings
5. Mock external dependencies
6. Update this README if adding new test categories
