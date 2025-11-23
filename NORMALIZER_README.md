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

## Feature Generation Pipeline

The normalization pipeline has been extended to include technical indicator computation and feature engineering for time series analysis.

### Overview

The feature generation module processes normalized price data and computes technical indicators including:
- **SMA** (Simple Moving Average): 10, 50, 200 day
- **EMA** (Exponential Moving Average): 20, 50 day
- **RSI** (Relative Strength Index): 14 day
- **MACD** (Moving Average Convergence Divergence): 12, 26, 9
- **ATR** (Average True Range): 14 day
- **ADX** (Average Directional Index): 14 day
- **Momentum**: 20 day percentage change
- **Volatility**: 30 day rolling standard deviation
- **OBV** (On-Balance Volume)

### Pipeline Steps

```python
from backend.features.normalize_pipeline import (
    normalize_and_generate_features,
    process_multi_ticker_data
)
import pandas as pd

# Step 1: Load price data
prices_df = pd.read_parquet('data/normalized/prices.parquet')

# Step 2: Apply corporate actions and generate features
features_df = normalize_and_generate_features(
    prices_df,
    corporate_actions={
        'splits': [('2020-08-31', 4.0)],  # 4-for-1 split
        'dividends': [('2021-02-05', 0.22)]  # $0.22 dividend
    }
)

# Step 3: Process multiple tickers
data = {
    'AAPL': aapl_prices,
    'MSFT': msft_prices,
    'GOOGL': googl_prices
}

combined_features = process_multi_ticker_data(
    data,
    output_path='data/features/daily_features.parquet'
)
```

### Corporate Action Adjustments

The pipeline automatically adjusts historical prices for:

**Stock Splits**:
- Divides historical prices by split ratio
- Multiplies historical volume by split ratio
- Example: 2-for-1 split → prices halved, volume doubled

**Dividends**:
- Subtracts dividend amount from historical prices
- Ensures price continuity for technical analysis

### Missing Data Handling

The pipeline handles missing data using configurable strategies:
- **Forward Fill** (default): Carries forward last known value
- **Backward Fill**: Uses next available value
- **Interpolation**: Linear interpolation between points
- **Limit**: Maximum consecutive NaN values to fill (default: 5)

### Feature Standardization

All features follow standardized naming conventions:

| Feature | Column Name | Description |
|---------|------------|-------------|
| SMA 10-day | `sma_10` | 10-period simple moving average |
| SMA 50-day | `sma_50` | 50-period simple moving average |
| SMA 200-day | `sma_200` | 200-period simple moving average |
| EMA 20-day | `ema_20` | 20-period exponential moving average |
| EMA 50-day | `ema_50` | 50-period exponential moving average |
| RSI 14-day | `rsi_14` | 14-period relative strength index (0-100) |
| MACD Line | `macd` | MACD line (12,26) |
| MACD Signal | `macd_signal` | 9-period signal line |
| MACD Histogram | `macd_histogram` | MACD - Signal |
| ATR 14-day | `atr_14` | 14-period average true range |
| ATR Volatility | `atr_volatility` | ATR normalized by price |
| ADX 14-day | `adx_14` | 14-period average directional index |
| Momentum 20-day | `momentum_20` | 20-day percentage change |
| Volatility 30-day | `volatility_30` | 30-day rolling standard deviation |
| OBV | `obv` | On-balance volume |

### Output Format

Features are saved to `data/features/daily_features.parquet` with schema:

```
ticker (string): Stock symbol
date (datetime): Trading date
open, high, low, close (float): OHLC prices
volume (float): Trading volume
sma_10, sma_50, sma_200 (float): Simple moving averages
ema_20, ema_50 (float): Exponential moving averages
rsi_14 (float): Relative strength index
macd, macd_signal, macd_histogram (float): MACD indicators
atr_14, atr_volatility (float): ATR indicators
adx_14 (float): Average directional index
momentum_20 (float): Momentum indicator
volatility_30 (float): Volatility measure
obv (float): On-balance volume
```

### Quality Assurance

The pipeline includes coverage checking to ensure data quality:

```python
from backend.features.normalize_pipeline import check_feature_coverage

coverage = check_feature_coverage(features_df, threshold=0.95)

print(f"Dates meeting 95% threshold: {coverage['dates_meeting_threshold']}/{coverage['total_dates']}")
print(f"Average coverage: {coverage['average_coverage']:.2%}")
```

**Acceptance Criteria**: For each trading date, features should exist for >95% of tickers.

### Running Tests

Comprehensive test suite for all indicators:

```bash
cd /home/runner/work/StockLighthouse/StockLighthouse
PYTHONPATH=. pytest tests/indicators_test.py -v
PYTHONPATH=. pytest tests/test_normalize_pipeline.py -v
```

All 50 tests validate:
- Correct indicator calculations with known values
- Edge case handling (insufficient data, missing columns, NaN values)
- Corporate action adjustments
- Feature coverage requirements
- Multi-ticker processing

### Example Usage

Complete pipeline example:

```python
from backend.features.indicators import compute_all_indicators
from backend.features.normalize_pipeline import (
    process_multi_ticker_data,
    check_feature_coverage
)
import pandas as pd

# Load price data for multiple tickers
tickers = ['AAPL', 'MSFT', 'GOOGL']
data = {}

for ticker in tickers:
    df = pd.read_parquet(f'data/normalized/{ticker}_prices.parquet')
    data[ticker] = df

# Process all tickers with feature generation
features_df = process_multi_ticker_data(
    data,
    output_path='data/features/daily_features.parquet'
)

# Check coverage
coverage = check_feature_coverage(features_df)
print(f"Feature coverage: {coverage['average_coverage']:.1%}")
print(f"Dates meeting threshold: {coverage['percentage_dates_meeting_threshold']:.1%}")

# Sample output
print(features_df[['ticker', 'date', 'close', 'sma_50', 'rsi_14', 'macd']].head())
```
