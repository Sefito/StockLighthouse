# Scoring Pipeline

The StockLighthouse scoring pipeline computes composite buy scores by combining technical and fundamental indicators with configurable weights. It produces top-K buy candidates with explainability features.

## Overview

The scoring pipeline:
1. Loads feature data from `data/features/daily_features.parquet`
2. Applies rule-based filters (market cap, volume, price, exchange)
3. Normalizes features using z-score or min-max normalization
4. Computes technical and fundamental sub-scores with weighted features
5. Combines sub-scores into a composite score
6. Generates explanations for top candidates showing feature contributions
7. Saves results to parquet files and Redis cache

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│         Scoring Pipeline (scoring_service.py)           │
└────────────────────┬────────────────────────────────────┘
                     │
      ┌──────────────┼──────────────┐
      │              │              │
┌─────▼──────┐ ┌────▼─────┐ ┌─────▼──────┐
│   Loader   │ │ Filters  │ │ Normalizer │
└─────┬──────┘ └────┬─────┘ └─────┬──────┘
      │              │              │
      └──────────────┼──────────────┘
                     │
      ┌──────────────┼──────────────┐
      │              │              │
┌─────▼──────┐ ┌────▼─────┐ ┌─────▼──────┐
│  Tech      │ │  Fund    │ │ Composite  │
│  Scorer    │ │  Scorer  │ │  Scorer    │
└─────┬──────┘ └────┬─────┘ └─────┬──────┘
      │              │              │
      └──────────────┼──────────────┘
                     │
      ┌──────────────┼──────────────┐
      │              │              │
┌─────▼──────┐ ┌────▼─────┐ ┌─────▼──────┐
│ Explainer  │ │  Parquet │ │   Redis    │
│            │ │  Output  │ │   Cache    │
└────────────┘ └──────────┘ └────────────┘
```

## Configuration

Configuration is stored in `config/scoring.yaml`:

### Composite Weights
```yaml
composite_weights:
  technical: 0.6    # Weight for technical score
  fundamental: 0.4  # Weight for fundamental score
```

### Technical Features
```yaml
technical_features:
  rsi:
    weight: 0.25
    optimal_range: [30, 70]  # Oversold/overbought levels
  macd_signal:
    weight: 0.20
    direction: positive  # Positive signal is bullish
  # ... more features
```

### Fundamental Features
```yaml
fundamental_features:
  pe_ratio:
    weight: 0.25
    direction: negative  # Lower P/E is better
    max_threshold: 50    # Filter extreme values
  # ... more features
```

### Filters
```yaml
filters:
  min_market_cap: 1000000000   # $1B minimum
  min_avg_volume: 100000       # 100k shares/day
  min_price: 5.0               # No penny stocks
  max_pe_ratio: 100            # Filter extreme valuations
  tradable_exchanges:
    - NMS   # NASDAQ
    - NYSE  # NYSE
```

## Usage

### Command Line

```bash
# Run with default settings
python3 backend/scoring/scoring_service.py

# Specify custom paths
python3 backend/scoring/scoring_service.py \
  --features data/features/daily_features.parquet \
  --fundamentals data/fundamentals/latest.parquet \
  --date 2025-11-24 \
  --config config/scoring.yaml
```

### Python API

```python
from backend.scoring.scoring_service import ScoringService

# Initialize service
service = ScoringService(config_path='config/scoring.yaml')

# Run pipeline
result_df = service.run_scoring_pipeline(
    features_path='data/features/daily_features.parquet',
    fundamentals_path='data/fundamentals/latest.parquet',
    date_str='2025-11-24'
)

# Access results
print(result_df.nlargest(10, 'composite_score')[
    ['symbol', 'composite_score', 'tech_score', 'fund_score']
])
```

## Output Files

### Ranks Parquet
`data/ranks/{date}_ranks.parquet`

Contains all scored stocks with:
- `symbol`: Stock ticker
- `composite_score`: Combined score (0-1)
- `tech_score`: Technical sub-score (0-1)
- `fund_score`: Fundamental sub-score (0-1)
- `norm_{feature}`: Normalized feature values
- All original features

### Explanations JSON
`data/ranks/{date}_explanations.json`

Contains detailed explanations for top-K candidates:
```json
{
  "AAPL": {
    "composite_score": 0.85,
    "tech_score": 0.90,
    "fund_score": 0.75,
    "contributions": {
      "norm_rsi": 0.80,
      "norm_pe_ratio": 0.70,
      ...
    },
    "explanation": "AAPL scored 0.85 (tech: 0.90, fund: 0.75). Top factors: rsi (0.80), pe_ratio (0.70), ..."
  }
}
```

### Redis Cache
Key: `top_candidates/daily` (configurable)

Cached for 24 hours (configurable TTL)

Contains top 50 candidates (configurable) in JSON format.

## Features

### Input Features Expected

**Technical Indicators:**
- `rsi`: Relative Strength Index (0-100)
- `macd_signal`: MACD signal line
- `volume_trend`: Volume change percentage
- `price_momentum`: Short-term price momentum
- `moving_avg_cross`: SMA50 - SMA200 difference
- `bollinger_position`: Position within Bollinger Bands (0-1)

**Fundamental Indicators:**
- `pe_ratio`: Price-to-earnings ratio
- `pb_ratio`: Price-to-book ratio
- `roe`: Return on equity (decimal)
- `debt_to_equity`: Debt-to-equity ratio
- `earnings_growth`: Earnings growth rate (decimal)
- `dividend_yield`: Dividend yield (decimal)

**Required Metadata:**
- `symbol`: Stock ticker (required)
- `price`: Current price (for filtering)
- `market_cap`: Market capitalization (for filtering)
- `avg_volume`: Average daily volume (for filtering)
- `exchange`: Exchange code (for filtering)

## Normalization

Two normalization methods are supported:

### Z-Score Normalization (default)
```python
# Converts to mean=0, std=1, clips outliers
normalized = (value - mean) / std
normalized = clip(normalized, -3, 3)
# Then maps to [0, 1] range
normalized = (normalized + 3) / 6
```

### Min-Max Normalization
```python
# Scales to [0, 1] range
normalized = (value - min) / (max - min)
```

## Scoring Algorithm

### Technical Score
```python
tech_score = Σ(weight_i × normalized_feature_i)
```

Features with `direction: negative` are inverted: `1 - normalized_value`

### Fundamental Score
```python
fund_score = Σ(weight_i × normalized_feature_i)
```

Features with `direction: negative` (e.g., P/E ratio) are inverted.

### Composite Score
```python
composite_score = w_tech × tech_score + w_fund × fund_score
```

Where weights are from `composite_weights` in config (default: 0.6/0.4).

## Performance

### SLA Targets
- Runtime: < 2 minutes for 500 tickers (S&P 500 scale)
- Typical: ~0.2 seconds for 40 tickers

### Optimizations
- Vectorized NumPy operations
- Efficient pandas operations
- Parquet format for fast I/O
- Redis caching for top candidates

## Testing

Run tests:
```bash
cd backend
PYTHONPATH=. pytest tests/test_scoring.py -v
```

Test coverage:
- Normalization functions (min-max, z-score)
- Weighted scoring with feature inversion
- Rule-based filtering
- Top-K selection
- Explanation generation
- End-to-end integration

## Error Handling

### Defensive Programming
- NaN and infinity values → replaced with 0
- Missing features → skipped with weight renormalization
- Empty data → returns zeros
- Redis unavailable → continues without caching

### Graceful Degradation
- Missing fundamental data → fundamental score = 0
- Insufficient features → uses available features only
- Filter violations → excludes ticker from scoring

## Extensibility

### Adding New Features

1. Add feature to config:
```yaml
technical_features:
  my_new_feature:
    weight: 0.15
    direction: positive
```

2. Ensure feature exists in input parquet file

3. Feature automatically included in scoring

### Custom Normalization

Modify `normalize_features()` in `ScoringService`:
```python
def normalize_features(self, df, feature_list):
    # Custom normalization logic
    pass
```

### Custom Filters

Add to `apply_rule_filters()`:
```python
def apply_rule_filters(self, df):
    filtered = apply_filters(df, ...)
    # Additional custom filtering
    return filtered
```

## Examples

### Generate Sample Data
```bash
python3 scripts/generate_sample_features.py
```

### Run Scoring Pipeline
```bash
cd /home/runner/work/StockLighthouse/StockLighthouse
python3 backend/scoring/scoring_service.py \
  --features data/features/daily_features.parquet \
  --date $(date +%Y-%m-%d)
```

### View Results
```python
import pandas as pd
import json

# Load ranks
df = pd.read_parquet('data/ranks/2025-11-24_ranks.parquet')
print(df.nlargest(10, 'composite_score'))

# Load explanations
with open('data/ranks/2025-11-24_explanations.json') as f:
    explanations = json.load(f)
    print(explanations['AAPL'])
```

## Troubleshooting

### Redis Connection Failed
```
⚠ Redis not available: Error -3 connecting to redis:6379
```
**Solution**: Redis is optional. Pipeline continues without caching. To enable Redis:
```bash
docker-compose up redis
```

### Missing Features
```
⚠ Feature 'rsi' not found, skipping
```
**Solution**: Ensure input parquet file contains all required features.

### No Stocks Pass Filters
```
Filtered out 40 stocks (40 -> 0)
```
**Solution**: Adjust filter thresholds in `config/scoring.yaml`

## References

- Configuration: `config/scoring.yaml`
- Sample Scoring: `backend/scoring/sample_scoring.py`
- Scoring Service: `backend/scoring/scoring_service.py`
- Tests: `backend/tests/test_scoring.py`
- Sample Data Generator: `scripts/generate_sample_features.py`
