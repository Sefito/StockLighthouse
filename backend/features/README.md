# Feature Generation Module

This module provides technical indicator computation and feature engineering for stock data.

## Overview

The feature generation pipeline processes normalized price data and computes a comprehensive set of technical indicators for time series analysis and machine learning applications.

## Features

### Technical Indicators

- **SMA** (Simple Moving Average): 10, 50, 200 day periods
- **EMA** (Exponential Moving Average): 20, 50 day periods
- **RSI** (Relative Strength Index): 14 day period
- **MACD** (Moving Average Convergence Divergence): 12, 26, 9 parameters
- **ATR** (Average True Range): 14 day period
- **ADX** (Average Directional Index): 14 day period
- **Momentum**: 20 day percentage change
- **Volatility**: 30 day rolling standard deviation
- **OBV** (On-Balance Volume)

### Pipeline Functions

- **Corporate Action Adjustments**: Automatically adjust historical prices for stock splits and dividends
- **Missing Data Handling**: Forward fill, backward fill, and interpolation strategies
- **Multi-Ticker Processing**: Efficiently process multiple tickers in batch
- **Feature Coverage Checking**: Validate data quality against acceptance criteria

## Quick Start

```python
from backend.features.indicators import compute_all_indicators
from backend.features.normalize_pipeline import (
    process_multi_ticker_data,
    check_feature_coverage
)
import pandas as pd

# Load price data
prices_df = pd.read_parquet('data/normalized/prices.parquet')

# Compute all indicators
features_df = compute_all_indicators(prices_df)

# Process multiple tickers
data = {
    'AAPL': aapl_prices,
    'MSFT': msft_prices
}

features = process_multi_ticker_data(
    data,
    output_path='data/features/daily_features.parquet'
)

# Check coverage
coverage = check_feature_coverage(features)
print(f"Coverage: {coverage['average_coverage']:.1%}")
```

## Module Structure

```
backend/features/
├── __init__.py              # Module initialization
├── indicators.py            # Technical indicator implementations
└── normalize_pipeline.py    # Pipeline orchestration and corporate actions
```

## Running Tests

```bash
# Run all feature tests
PYTHONPATH=. pytest tests/indicators_test.py tests/test_normalize_pipeline.py -v

# Run indicator tests only
PYTHONPATH=. pytest tests/indicators_test.py -v

# Run pipeline tests only
PYTHONPATH=. pytest tests/test_normalize_pipeline.py -v
```

All 50 tests should pass:
- 32 indicator tests
- 18 pipeline tests

## Demo Script

Run the feature generation demo:

```bash
python scripts/demo_features.py
```

This will:
1. Generate sample price data for AAPL, MSFT, GOOGL
2. Compute all technical indicators
3. Apply corporate action adjustments
4. Check feature coverage (should be 100%)
5. Save results to `data/features/daily_features.parquet`

## Output Format

Features are saved in parquet format with the following schema:

| Column | Type | Description |
|--------|------|-------------|
| `ticker` | string | Stock symbol |
| `date` | datetime | Trading date |
| `open` | float | Opening price |
| `high` | float | High price |
| `low` | float | Low price |
| `close` | float | Closing price |
| `volume` | float | Trading volume |
| `sma_10` | float | 10-day simple moving average |
| `sma_50` | float | 50-day simple moving average |
| `sma_200` | float | 200-day simple moving average |
| `ema_20` | float | 20-day exponential moving average |
| `ema_50` | float | 50-day exponential moving average |
| `rsi_14` | float | 14-day relative strength index |
| `macd` | float | MACD line |
| `macd_signal` | float | MACD signal line |
| `macd_histogram` | float | MACD histogram |
| `atr_14` | float | 14-day average true range |
| `atr_volatility` | float | ATR normalized by price |
| `adx_14` | float | 14-day average directional index |
| `momentum_20` | float | 20-day momentum |
| `volatility_30` | float | 30-day volatility |
| `obv` | float | On-balance volume |

## Corporate Actions

The pipeline supports automatic adjustments for:

### Stock Splits

Adjusts historical prices and volumes to maintain continuity:
- Prices are divided by split ratio
- Volume is multiplied by split ratio

Example:
```python
actions = {
    'splits': [
        ('2020-08-31', 4.0),  # 4-for-1 split on Aug 31, 2020
    ]
}
```

### Dividends

Adjusts historical prices to account for dividend payments:
- Prices before ex-dividend date are reduced by dividend amount

Example:
```python
actions = {
    'dividends': [
        ('2021-02-05', 0.22),  # $0.22 dividend on Feb 5, 2021
    ]
}
```

## Missing Data Handling

Three strategies are available:

1. **Forward Fill** (default): Propagates last known value forward
2. **Backward Fill**: Uses next available value
3. **Interpolation**: Linear interpolation between points

All strategies support a `limit` parameter to restrict consecutive fills.

```python
from backend.features.normalize_pipeline import handle_missing_data

# Forward fill with limit of 5 consecutive values
df = handle_missing_data(df, method='ffill', limit=5)
```

## Acceptance Criteria

The pipeline validates against the following criteria:

- ✅ For each trading date, features should exist for >95% of tickers
- ✅ All indicator unit tests pass (50/50)
- ✅ Features use standardized naming convention
- ✅ Corporate actions are correctly applied
- ✅ Missing data is handled gracefully

## Implementation Notes

- All indicators are implemented using pure pandas/numpy (no external TA libraries)
- Indicators handle edge cases: NaN values, insufficient data, empty series
- All functions are thoroughly tested with known values
- Pipeline is optimized for batch processing of multiple tickers
- Parquet format used for efficient storage and fast loading

## API Reference

### indicators.py

#### `sma(series, period) -> Series`
Calculate Simple Moving Average.

#### `ema(series, period) -> Series`
Calculate Exponential Moving Average.

#### `rsi(series, period=14) -> Series`
Calculate Relative Strength Index.

#### `macd(series, fast=12, slow=26, signal=9) -> tuple[Series, Series, Series]`
Calculate MACD line, signal line, and histogram.

#### `atr(high, low, close, period=14) -> Series`
Calculate Average True Range.

#### `adx(high, low, close, period=14) -> Series`
Calculate Average Directional Index.

#### `momentum(series, period=20) -> Series`
Calculate momentum indicator.

#### `volatility(series, period=30) -> Series`
Calculate rolling volatility (standard deviation).

#### `obv(close, volume) -> Series`
Calculate On-Balance Volume.

#### `compute_all_indicators(df) -> DataFrame`
Compute all indicators in one pass. Requires columns: `close` (required), `high`, `low`, `volume` (optional).

### normalize_pipeline.py

#### `adjust_for_splits(df, split_ratio) -> DataFrame`
Adjust price and volume for stock splits.

#### `adjust_for_dividends(df, dividend_amount) -> DataFrame`
Adjust prices for dividend payments.

#### `apply_corporate_actions(df, actions) -> DataFrame`
Apply both splits and dividends based on dates.

#### `handle_missing_data(df, method='ffill', limit=None) -> DataFrame`
Handle missing data using specified strategy.

#### `normalize_and_generate_features(df, corporate_actions, fill_method='ffill') -> DataFrame`
Main pipeline: apply corporate actions, handle missing data, compute indicators.

#### `process_multi_ticker_data(data, corporate_actions, output_path) -> DataFrame`
Process multiple tickers and save to parquet.

#### `check_feature_coverage(df, threshold=0.95) -> dict`
Validate feature coverage against acceptance criteria.

## Contributing

When adding new indicators:

1. Implement the indicator function in `indicators.py`
2. Add the indicator to `compute_all_indicators()`
3. Write comprehensive tests in `tests/indicators_test.py`
4. Update this README with the new indicator
5. Update `NORMALIZER_README.md` if needed

All indicators should:
- Handle NaN values gracefully
- Use consistent naming convention
- Include docstrings with examples
- Be tested with known values
- Handle edge cases (empty data, insufficient periods)

## License

Part of the StockLighthouse project.
