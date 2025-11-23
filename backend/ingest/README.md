# StockLighthouse Ingestion System

This document describes the comprehensive daily market data ingestion system for StockLighthouse.

## Overview

The ingestion system provides production-ready modules for fetching and storing market data from Yahoo Finance:

1. **Price Ingestion** (`backend/ingest/price_ingest.py`) - Daily OHLCV data
2. **Fundamentals Ingestion** (`backend/ingest/fundamentals_ingest.py`) - Quarterly financial data

Both modules feature:
- Exponential backoff with configurable retries
- Rate limiting to respect provider limits
- Comprehensive data validation
- Detailed logging and error tracking
- Progress reporting
- CLI interfaces

## Installation

Install dependencies:

```bash
cd backend
pip install -r requirements.txt
```

Dependencies include:
- `yfinance` - Yahoo Finance data provider
- `pandas` - Data manipulation
- `pyarrow` - Parquet file support
- `pydantic` - Data validation

## Quick Start

### Price Ingestion

Fetch daily OHLCV data for all tickers in the universe:

```bash
# From project root
python backend/ingest/price_ingest.py

# With custom parameters
python backend/ingest/price_ingest.py --universe data/universe.csv --lookback-days 365
```

**Output:**
- Raw CSV files: `data/raw/prices/{ticker}.csv`
- Normalized parquet: `data/normalized/prices.parquet`
- Validation log: `data/raw/prices/validation.log`
- Failures log: `data/raw/prices/failures.log`

### Fundamentals Ingestion

Fetch quarterly fundamentals for all tickers:

```bash
# From project root
python backend/ingest/fundamentals_ingest.py

# With custom universe
python backend/ingest/fundamentals_ingest.py --universe data/universe.csv
```

**Output:**
- Normalized parquet: `data/normalized/fundamentals.parquet`
- Failures log: `data/raw/fundamentals/failures.log`

## Module Documentation

### PriceIngestor

**Features:**
- Fetches daily OHLCV (Open, High, Low, Close, Volume) data
- Validates data completeness (98% threshold)
- Detects gaps in timeseries
- Saves both raw CSV and normalized Parquet formats
- Tracks validation and failure metrics

**Usage as Library:**

```python
from backend.ingest.price_ingest import PriceIngestor

# Create ingestor
ingestor = PriceIngestor(
    universe_path="data/universe.csv",
    lookback_days=365,
    max_retries=3,
    initial_backoff=1.0,
    backoff_multiplier=2.0,
    request_delay=0.1
)

# Run ingestion
metrics = ingestor.ingest()

# Print summary
ingestor.print_summary(metrics)
```

**Configuration:**
- `universe_path`: Path to CSV with ticker,sector,industry columns
- `lookback_days`: Historical data window (default: 365)
- `raw_dir`: Raw CSV output directory (default: data/raw/prices)
- `normalized_dir`: Parquet output directory (default: data/normalized)
- `max_retries`: Maximum retry attempts (default: 3)
- `initial_backoff`: Initial backoff in seconds (default: 1.0)
- `backoff_multiplier`: Exponential backoff multiplier (default: 2.0)
- `request_delay`: Delay between requests in seconds (default: 0.1)

### FundamentalsIngestor

**Features:**
- Fetches quarterly financial statements (income, balance sheet, cash flow)
- Extracts key metrics: revenue, net_income, eps, total_assets, total_debt, free_cash_flow, operating_margin
- Handles missing quarterly data gracefully
- Saves normalized Parquet format with JSON metrics

**Usage as Library:**

```python
from backend.ingest.fundamentals_ingest import FundamentalsIngestor

# Create ingestor
ingestor = FundamentalsIngestor(
    universe_path="data/universe.csv",
    max_retries=3,
    initial_backoff=1.0,
    backoff_multiplier=2.0,
    request_delay=0.1
)

# Run ingestion
metrics = ingestor.ingest()

# Print summary
ingestor.print_summary(metrics)
```

**Configuration:**
- `universe_path`: Path to CSV with ticker,sector,industry columns
- `raw_dir`: Raw data and logs directory (default: data/raw/fundamentals)
- `normalized_dir`: Parquet output directory (default: data/normalized)
- `max_retries`: Maximum retry attempts (default: 3)
- `initial_backoff`: Initial backoff in seconds (default: 1.0)
- `backoff_multiplier`: Exponential backoff multiplier (default: 2.0)
- `request_delay`: Delay between requests in seconds (default: 0.1)

## Data Schemas

### Prices Parquet Schema

```
ticker: string
Date: timestamp
Open: float
High: float
Low: float
Close: float
Volume: int64
fetch_timestamp: string (ISO 8601)
data_source: string ("yfinance")
validation_status: string ("valid" or "invalid")
```

### Fundamentals Parquet Schema

```
ticker: string
report_date: string (YYYY-MM-DD)
period: string (Q1/Q2/Q3/Q4)
fiscal_year: int
revenue: float (nullable)
net_income: float (nullable)
eps: float (nullable)
total_assets: float (nullable)
total_debt: float (nullable)
free_cash_flow: float (nullable)
operating_margin: float (nullable)
fetch_timestamp: string (ISO 8601)
data_source: string ("yfinance")
metrics_json: string (JSON)
```

## Data Validation

### Price Data Validation

The price ingestor validates:

1. **Completeness**: Target 98% of expected trading days
   - Approximately 252 trading days per year
   - Accounts for weekends and holidays

2. **Gaps Detection**: Flags gaps > 5 days between consecutive trading days
   - Normal weekends/holidays are not flagged
   - Extended gaps are logged with details

3. **Data Quality**: Ensures all required columns present (Open, High, Low, Close, Volume)

**Example Validation Log:**
```
2024-11-23 19:00:00 - VALID - AAPL - Total: 252, Missing: 3, Completeness: 98.82%, Gaps: 0
2024-11-23 19:00:05 - INVALID - XYZ - Total: 200, Missing: 55, Completeness: 78.43%, Gaps: 2
2024-11-23 19:00:05 - XYZ - Gap of 30 days between 2024-05-15 and 2024-06-15
```

## Error Handling

### Retry Logic

Both ingestors use exponential backoff:

1. **First attempt**: Immediate
2. **Second attempt**: After 1.0s backoff
3. **Third attempt**: After 2.0s backoff (1.0 * 2.0)

### Failure Logging

All failures are logged with:
- Timestamp
- Ticker symbol
- Error message

**Example Failure Log:**
```
2024-11-23T19:00:00 - INVALID - Empty or None DataFrame returned
2024-11-23T19:00:05 - XYZ - No quarterly data available
```

## Testing

Run the comprehensive test suite:

```bash
cd backend

# Run all tests
python -m pytest tests/ -v

# Run price ingestion tests only
python -m pytest tests/test_price_ingest.py -v

# Run fundamentals ingestion tests only
python -m pytest tests/test_fundamentals_ingest.py -v

# Run with coverage
python -m pytest tests/ --cov=ingest --cov-report=html
```

**Test Coverage:**
- 43 unit tests for ingestion modules
- All network calls mocked
- Retry logic validated
- Data validation tested
- Error handling verified
- File output formats checked

## Production Considerations

### Rate Limiting

Default configuration respects Yahoo Finance limits:
- 0.1 second delay between requests
- ~600 requests per minute maximum
- For 25 tickers: ~3 seconds total

### Data Freshness

Recommended schedule:
- **Prices**: Daily after market close (e.g., 5:00 PM ET)
- **Fundamentals**: Quarterly after earnings releases

### Monitoring

Monitor these metrics:
- Success rate (target: >95%)
- Duration
- Failed tickers
- Validation status

### Scaling

For larger universes:
- Increase `request_delay` to avoid rate limits
- Consider batching (100 tickers per batch)
- Use caching for development/testing

## Troubleshooting

### Common Issues

1. **ImportError: No module named 'backend'**
   - Solution: Run from project root, not backend directory

2. **Empty DataFrame for ticker**
   - Cause: Delisted stock or invalid symbol
   - Check failures log for details

3. **Low completeness percentage**
   - Cause: Recently IPO'd stock or limited history
   - Review validation log for gap details

4. **Rate limit errors**
   - Solution: Increase `request_delay` parameter
   - Reduce batch size

### Debug Mode

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## License

Part of the StockLighthouse project. See LICENSE file for details.

## Support

For issues or questions:
1. Check troubleshooting section
2. Review validation and failure logs
3. Open an issue on GitHub
