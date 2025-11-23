# StockLighthouse Normalizer

This module provides canonical KPI mapping and defensive parsing for yfinance raw payloads.

## Overview

The normalizer converts raw provider data (yfinance) into a standardized `StockKPIs` model with defensive parsing and unit conversions.

## Features

- **Canonical Schema**: Standardized `StockKPIs` pydantic model covering core KPIs
- **Defensive Parsing**: Safe type conversion handling NaN, infinity, None, and invalid data
- **Unit Conversions**: Automatic conversion of percentage to decimal (e.g., dividend yield)
- **Market Inference**: Automatic market region detection from exchange codes
- **Multiple Fallbacks**: Try multiple field names for each KPI
- **Edge Case Handling**: Zero/negative values, missing fields, empty strings

## Quick Start

### Basic Usage

```python
from stocklighthouse.normalizer import normalize
from stocklighthouse.ingest.yfinance_ingestor import YFinanceIngestor

# Fetch raw data
ingestor = YFinanceIngestor()
ticker_data = ingestor.fetch_single("AAPL")

if ticker_data.success and ticker_data.raw_data:
    # Normalize to canonical KPIs
    kpis = normalize("AAPL", ticker_data.raw_data["info"])
    
    print(f"Symbol: {kpis.symbol}")
    print(f"Price: ${kpis.price:.2f}")
    print(f"Change: {kpis.change_pct:+.2f}%")
    print(f"Market: {kpis.market}")
    print(f"Sector: {kpis.sector}")
```

### JSON Schema Export

```python
from stocklighthouse.models import StockKPIs
import json

# Export JSON schema
schema = StockKPIs.model_json_schema()
with open("kpis_schema.json", "w") as f:
    json.dump(schema, f, indent=2)
```

### Sample Normalization Script

```bash
# Run the demo script to see normalization in action
python sample_normalize.py
```

This will:
1. Load raw data from `data/samples/`
2. Normalize all tickers
3. Export results to `data/normalized/`
4. Display statistics and sample records

## Canonical Schema

The `StockKPIs` model includes the following fields:

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `symbol` | str | Stock ticker symbol (required) | "AAPL" |
| `price` | float? | Current market price | 150.25 |
| `previous_close` | float? | Previous day's closing price | 148.50 |
| `change_pct` | float? | Percentage change from previous close | 1.18 |
| `market_cap` | float? | Total market capitalization | 2400000000000 |
| `pe_ratio` | float? | Price-to-earnings ratio | 28.5 |
| `pb_ratio` | float? | Price-to-book ratio | 40.2 |
| `dividend_yield` | float? | Annual dividend yield (decimal) | 0.005 |
| `sector` | str? | Business sector | "Technology" |
| `market` | str? | Market region | "us_market" |
| `exchange` | str? | Stock exchange code | "NMS" |
| `currency` | str? | Currency code | "USD" |
| `industry` | str? | Industry classification | "Consumer Electronics" |

All fields except `symbol` are optional.

## Defensive Parsing

### Safe Type Conversion

```python
# Handles invalid data gracefully
raw = {
    "regularMarketPrice": "not_a_number",  # Returns None
    "previousClose": float('nan'),          # Returns None
    "marketCap": float('inf'),              # Returns None
}
kpis = normalize("TEST", raw)
# All numeric fields will be None
```

### Multiple Field Fallbacks

```python
# Tries multiple field names
raw = {"currentPrice": 100.0}  # No regularMarketPrice
kpis = normalize("TEST", raw)
# Will use currentPrice as fallback
assert kpis.price == 100.0
```

### Unit Conversions

```python
# Dividend yield conversion
raw = {"dividendYield": 0.38}  # yfinance format: 0.38%
kpis = normalize("TEST", raw)
assert kpis.dividend_yield == 0.0038  # Converted to decimal
```

## Market Inference

The normalizer automatically infers market region from exchange codes:

| Exchanges | Market |
|-----------|--------|
| NMS, NYSE, NASDAQ, AMEX | `us_market` |
| LSE, LON | `uk_market` |
| FRA, PAR, AMS, SWX | `eu_market` |
| TYO, HKG, SHH, SHZ | `asian_market` |

## Edge Cases

The normalizer handles various edge cases:

### Zero/Negative Previous Close

```python
raw = {
    "regularMarketPrice": 50.0,
    "previousClose": 0.0  # Zero
}
kpis = normalize("TEST", raw)
assert kpis.change_pct is None  # Avoids division by zero
```

### Missing Fields

```python
raw = {}  # Empty data
kpis = normalize("TEST", raw)
# All optional fields are None
assert kpis.price is None
assert kpis.sector is None
```

### Empty Strings

```python
raw = {
    "sector": "",
    "industry": "   "  # Only whitespace
}
kpis = normalize("TEST", raw)
assert kpis.sector is None
assert kpis.industry is None
```

## Testing

The normalizer has comprehensive test coverage:

```bash
cd backend
PYTHONPATH=backend/src pytest tests/test_normalizer.py -v
```

### Test Categories

- **Edge Cases**: Missing fields, zero/negative values, NaN, infinity
- **Type Safety**: Invalid data types, string conversions
- **Feature Tests**: Market inference, dividend yield conversion, fallbacks
- **Real-World**: Actual yfinance data samples

All 32 normalizer tests pass.

## Example Output

### Normalized JSON

```json
{
  "symbol": "AAPL",
  "price": 271.49,
  "previous_close": 266.25,
  "change_pct": 1.97,
  "market_cap": 4029017227264.0,
  "pe_ratio": 36.34,
  "pb_ratio": 54.40,
  "dividend_yield": 0.0038,
  "sector": "Technology",
  "market": "us_market",
  "exchange": "NMS",
  "currency": "USD",
  "industry": "Consumer Electronics"
}
```

## Integration Example

```python
from stocklighthouse.ingest.yfinance_ingestor import YFinanceIngestor
from stocklighthouse.normalizer import normalize
from stocklighthouse.models import IngestorRequest

# Initialize ingestor
ingestor = YFinanceIngestor(cache_ttl_seconds=300)

# Fetch multiple symbols
request = IngestorRequest(symbols=["AAPL", "MSFT", "GOOGL"], use_cache=True)
response = ingestor.fetch(request)

# Normalize all successful fetches
normalized_kpis = []
for ticker in response.tickers:
    if ticker.success and ticker.raw_data:
        kpis = normalize(ticker.symbol, ticker.raw_data["info"])
        normalized_kpis.append(kpis)

# Process normalized data
for kpis in normalized_kpis:
    print(f"{kpis.symbol}: ${kpis.price:.2f} ({kpis.change_pct:+.2f}%)")
```

## API Reference

### `normalize(symbol: str, raw_data: Dict[str, Any]) -> StockKPIs`

Normalize raw provider data into standardized StockKPIs.

**Parameters:**
- `symbol`: Stock symbol (required, will be uppercased and stripped)
- `raw_data`: Raw data from provider (e.g., yfinance info dict)

**Returns:**
- `StockKPIs`: Normalized KPIs with all optional fields possibly None

**Example:**
```python
raw = {
    "regularMarketPrice": 100.0,
    "previousClose": 95.0,
    "sector": "Technology"
}
kpis = normalize("AAPL", raw)
```

### Helper Functions

#### `_safe_float(value: Any) -> Optional[float]`

Safely convert value to float, handling NaN, infinity, and invalid types.

#### `_safe_string(value: Any) -> Optional[str]`

Safely convert value to string, trimming whitespace and handling empty strings.

#### `_infer_market(exchange: Optional[str]) -> Optional[str]`

Infer market region from exchange code.

## Field Mappings

### Price Fields

| StockKPIs Field | yfinance Fields (in order) |
|-----------------|----------------------------|
| `price` | `regularMarketPrice`, `currentPrice`, `price` |
| `previous_close` | `previousClose` |

### Ratio Fields

| StockKPIs Field | yfinance Fields (in order) |
|-----------------|----------------------------|
| `pe_ratio` | `trailingPE`, `forwardPE` |
| `pb_ratio` | `priceToBook`, `priceBookRatio` |

### Other Fields

| StockKPIs Field | yfinance Fields |
|-----------------|-----------------|
| `market_cap` | `marketCap` |
| `dividend_yield` | `dividendYield` (converted from %) |
| `sector` | `sector` |
| `industry` | `industry` |
| `exchange` | `exchange` |
| `currency` | `currency` |

## Configuration

### Dividend Yield Threshold

```python
DIVIDEND_YIELD_PERCENTAGE_THRESHOLD = 0.01
```

Values above this threshold are assumed to be percentages and converted to decimals.

## Future Enhancements

Potential improvements:
- Support for additional data providers (Alpha Vantage, Polygon.io)
- Historical data normalization
- More sophisticated market inference
- Validation rules for data quality
- Configurable field mappings
