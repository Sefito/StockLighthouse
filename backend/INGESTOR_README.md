# StockLighthouse YFinance Ingestor

This module provides a robust, production-ready stock data ingestor using the yfinance library.

## Features

- **Batch Fetching**: Efficiently fetch multiple stock symbols in a single request
- **Exponential Backoff**: Automatic retry with exponential backoff for transient failures
- **In-Memory Caching**: TTL-based cache to reduce redundant API calls during development
- **Fallback Support**: Graceful degradation to fast_info when full info is unavailable
- **Type Safety**: Full Pydantic models for inputs and outputs
- **Comprehensive Testing**: 19 unit tests covering edge cases and error scenarios

## Installation

```bash
cd backend
pip install -r requirements.txt
```

## Quick Start

### Basic Usage

```python
from stocklighthouse.ingest.yfinance_ingestor import YFinanceIngestor
from stocklighthouse.models import IngestorRequest

# Initialize the ingestor
ingestor = YFinanceIngestor(
    cache_ttl_seconds=300,  # 5 minute cache
    max_retries=3,           # Retry up to 3 times
    initial_backoff=1.0,     # Start with 1 second backoff
    backoff_multiplier=2.0   # Double backoff each retry
)

# Fetch multiple symbols
request = IngestorRequest(
    symbols=["AAPL", "MSFT", "GOOGL"],
    use_cache=True
)

response = ingestor.fetch(request)

# Process results
for ticker in response.tickers:
    if ticker.success:
        print(f"{ticker.symbol}: {ticker.raw_data}")
    else:
        print(f"{ticker.symbol} failed: {ticker.error}")

print(f"Fetched: {response.fetched_count}, Cached: {response.cached_count}, Failed: {response.failed_count}")
```

### Single Symbol Fetch

```python
# Convenience method for single symbol
ticker_data = ingestor.fetch_single("AAPL", use_cache=True)

if ticker_data.success:
    print(f"Price: {ticker_data.raw_data['info']['regularMarketPrice']}")
else:
    print(f"Error: {ticker_data.error}")
```

## Data Models

### IngestorRequest
```python
class IngestorRequest(BaseModel):
    symbols: list[str]       # List of stock symbols to fetch
    use_cache: bool = True   # Whether to use cached data
```

### TickerData
```python
class TickerData(BaseModel):
    symbol: str                           # Stock symbol
    success: bool                         # Whether fetch succeeded
    raw_data: Optional[Dict[str, Any]]   # Full info data if available
    fast_info: Optional[Dict[str, Any]]  # Fast info fallback
    error: Optional[str]                  # Error message if failed
```

### IngestorResponse
```python
class IngestorResponse(BaseModel):
    tickers: list[TickerData]  # List of ticker results
    fetched_count: int          # Number of newly fetched tickers
    cached_count: int           # Number of cached tickers used
    failed_count: int           # Number of failed fetches
```

## Cache Management

```python
# Clear cache when needed
ingestor.clear_cache()

# Check cache status
# Cache automatically expires based on TTL
# Expired entries are removed on next access
```

## Error Handling

The ingestor handles various error scenarios:

1. **Network Failures**: Automatic retry with exponential backoff
2. **Missing Ticker Info**: Falls back to fast_info
3. **Invalid Symbols**: Returns TickerData with success=False and error message
4. **Partial Data**: Successfully processes available tickers, marks others as failed

Example error handling:

```python
response = ingestor.fetch(request)

for ticker in response.tickers:
    if not ticker.success:
        # Handle error
        if "delisted" in ticker.error.lower():
            print(f"{ticker.symbol} is no longer listed")
        elif "network" in ticker.error.lower():
            print(f"{ticker.symbol} had a network error")
        else:
            print(f"{ticker.symbol} failed: {ticker.error}")
```

## Running Tests

```bash
cd backend
PYTHONPATH=/home/runner/work/StockLighthouse/StockLighthouse/backend/src pytest tests/test_ingestor.py -v
```

All tests use mocked HTTP responses to avoid network dependencies.

## Demo Script

A demonstration script is provided to fetch sample data:

```bash
cd /home/runner/work/StockLighthouse/StockLighthouse
python scripts/demo_fetch.py
```

This will:
1. Fetch 10 popular stock symbols
2. Write raw JSON data to `data/samples/`
3. Generate a summary report in `data/samples/fetch_summary.json`

### Demo Output Structure

Individual ticker files (e.g., `aapl.json`):
```json
{
  "symbol": "AAPL",
  "success": true,
  "raw_data": {
    "symbol": "AAPL",
    "info": { /* full yfinance info */ },
    "source": "yfinance",
    "fetch_time": "2025-11-23T15:30:00.000000"
  },
  "fast_info": null
}
```

Summary file (`fetch_summary.json`):
```json
{
  "fetch_time": "2025-11-23T15:30:00.000000",
  "symbols": [
    {"symbol": "AAPL", "success": true, "file": "aapl.json"},
    {"symbol": "INVALID", "success": false, "error": "ticker not found"}
  ],
  "statistics": {
    "total": 10,
    "successful": 9,
    "failed": 1
  }
}
```

## Configuration Options

| Parameter | Default | Description |
|-----------|---------|-------------|
| `cache_ttl_seconds` | 300 | Cache entry time-to-live in seconds |
| `max_retries` | 3 | Maximum retry attempts for failed requests |
| `initial_backoff` | 1.0 | Initial backoff delay in seconds |
| `backoff_multiplier` | 2.0 | Multiplier for exponential backoff |

## Integration with Normalizer

The ingestor returns raw provider data that can be normalized using the `normalizer` module:

```python
from stocklighthouse.normalizer import normalize

# Fetch raw data
ticker_data = ingestor.fetch_single("AAPL")

if ticker_data.success and ticker_data.raw_data:
    # Normalize to StockKPIs
    kpis = normalize("AAPL", ticker_data.raw_data["info"])
    print(f"Price: {kpis.price}, Sector: {kpis.sector}")
```

## Performance Considerations

1. **Batch Fetching**: Fetch multiple symbols at once to optimize performance
2. **Cache Usage**: Enable caching during development to avoid rate limits
3. **Retry Configuration**: Adjust retry parameters based on your error rates
4. **Network Isolation**: Tests mock HTTP to avoid network dependencies

## Limitations

- No API key required (uses free yfinance)
- Subject to Yahoo Finance rate limits
- Network access required (except in tests with mocks)
- Fast info provides limited data compared to full info

## Future Enhancements

Potential improvements for future versions:

- Persistent cache using local parquet files
- Rate limiting to respect provider limits
- Async/concurrent fetching for better performance
- Additional provider support (Alpha Vantage, Polygon.io, etc.)
- Historical data fetching
- Real-time streaming data support
