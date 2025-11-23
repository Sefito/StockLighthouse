# StockLighthouse

A stock data ingestion and analysis platform with robust data fetching, normalization, and caching capabilities.

## Features

- **YFinance Ingestor**: Fetch stock data with retry logic, caching, and fallback support
- **Data Normalization**: Convert raw provider data to standardized KPIs
- **Type Safety**: Full Pydantic models for data validation
- **Comprehensive Testing**: 21+ unit tests with mocked HTTP

## Quick Start

### Installation

```bash
cd backend
pip install -r requirements.txt
```

### Run Demo

Fetch sample data for 10 popular stocks:

```bash
python scripts/demo_fetch.py
```

### Run Tests

```bash
cd backend
PYTHONPATH=backend/src pytest tests/ -v
```

## Documentation

- [YFinance Ingestor API Documentation](backend/INGESTOR_README.md) - Complete API reference and usage examples

## Project Structure

```
StockLighthouse/
├── backend/
│   ├── src/
│   │   └── stocklighthouse/
│   │       ├── ingest/
│   │       │   └── yfinance_ingestor.py  # Main ingestor
│   │       ├── models.py                  # Pydantic data models
│   │       └── normalizer.py             # Data normalization
│   ├── tests/
│   │   ├── test_ingestor.py              # Ingestor tests
│   │   └── test_normalizer.py            # Normalizer tests
│   └── requirements.txt
├── scripts/
│   └── demo_fetch.py                      # Demo script
└── data/
    └── samples/                           # Sample output data

```

## Basic Usage

```python
from stocklighthouse.ingest.yfinance_ingestor import YFinanceIngestor
from stocklighthouse.models import IngestorRequest

# Initialize ingestor
ingestor = YFinanceIngestor(cache_ttl_seconds=300)

# Fetch stock data
request = IngestorRequest(symbols=["AAPL", "MSFT"], use_cache=True)
response = ingestor.fetch(request)

# Process results
for ticker in response.tickers:
    if ticker.success:
        print(f"{ticker.symbol}: Success")
    else:
        print(f"{ticker.symbol}: {ticker.error}")
```

For detailed API documentation and advanced usage, see [backend/INGESTOR_README.md](backend/INGESTOR_README.md).