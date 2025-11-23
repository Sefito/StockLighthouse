# Sector Analyzer API Documentation

The analyzer module provides sector aggregation and derived metrics functionality for stock analysis.

## Features

- **Sector Aggregation**: Group stocks by sector with comprehensive statistics
- **Weighted Averages**: Calculate market-cap weighted P/E ratios
- **Unknown Sector Handling**: Gracefully handles stocks without sector information
- **Robust Data Handling**: Handles missing/None values appropriately

## Quick Start

```python
from stocklighthouse.models import StockKPIs
from stocklighthouse.analyzer import sector_aggregate, weighted_average_pe

# Create stock data
stocks = [
    StockKPIs(symbol="AAPL", sector="Technology", pe_ratio=28.5, market_cap=2.4e12),
    StockKPIs(symbol="MSFT", sector="Technology", pe_ratio=30.2, market_cap=2.1e12),
    StockKPIs(symbol="JNJ", sector="Healthcare", pe_ratio=15.5, market_cap=0.4e12),
]

# Aggregate by sector
summaries = sector_aggregate(stocks)
for summary in summaries:
    print(f"{summary.sector}: {summary.count} stocks, median P/E: {summary.median_pe}")

# Calculate weighted average P/E
weighted_pe = weighted_average_pe(stocks)
print(f"Market-cap weighted P/E: {weighted_pe:.2f}")
```

## API Reference

### `sector_aggregate(stocks: list[StockKPIs]) -> list[SectorSummary]`

Aggregates stock data by sector and computes summary statistics.

**Parameters:**
- `stocks`: List of StockKPIs objects to aggregate

**Returns:**
- List of SectorSummary objects, sorted by count (descending) then sector name

**Example:**
```python
summaries = sector_aggregate(stocks)
for summary in summaries:
    print(f"{summary.sector}:")
    print(f"  Count: {summary.count}")
    print(f"  Median P/E: {summary.median_pe}")
    print(f"  Top 3 tickers: {summary.top_tickers}")
```

### `SectorSummary` Model

Contains aggregated statistics for a sector:

- `sector` (str): Sector name (or "Unknown" for stocks without sector)
- `count` (int): Number of stocks in the sector
- `median_pe` (float | None): Median price-to-earnings ratio
- `median_pb` (float | None): Median price-to-book ratio
- `median_market_cap` (float | None): Median market capitalization
- `avg_dividend_yield` (float | None): Average dividend yield (as decimal, e.g., 0.02 = 2%)
- `top_tickers` (list[tuple[str, float | None]]): Top 3 tickers by market cap (symbol, market_cap pairs)

### `weighted_average_pe(stocks: list[StockKPIs]) -> float | None`

Calculates market-cap weighted average P/E ratio.

**Parameters:**
- `stocks`: List of StockKPIs objects

**Returns:**
- Weighted average P/E ratio, or None if no valid stocks

**Example:**
```python
weighted_pe = weighted_average_pe(stocks)
if weighted_pe:
    print(f"Weighted P/E: {weighted_pe:.2f}")
```

### `weighted_average_pe_by_sector(stocks: list[StockKPIs]) -> dict[str, float | None]`

Calculates market-cap weighted average P/E ratio for each sector.

**Parameters:**
- `stocks`: List of StockKPIs objects

**Returns:**
- Dictionary mapping sector name to weighted average P/E ratio

**Example:**
```python
sector_weighted = weighted_average_pe_by_sector(stocks)
for sector, weighted_pe in sector_weighted.items():
    if weighted_pe:
        print(f"{sector}: {weighted_pe:.2f}")
```

## Data Handling

### Missing Values

All aggregation functions handle missing/None values gracefully:

- Median calculations only consider non-None values
- Stocks without market cap are included after top 3 in top_tickers
- If all values for a metric are None, the result is None

### Unknown Sectors

Stocks with `sector=None` or missing sector are grouped under the "Unknown" sector:

```python
stocks = [
    StockKPIs(symbol="A", sector=None, pe_ratio=20.0),
    StockKPIs(symbol="B", sector="Tech", pe_ratio=30.0),
]
summaries = sector_aggregate(stocks)
# Results in 2 summaries: "Tech" and "Unknown"
```

## Demo Script

Run the included demo to see the analyzer in action:

```bash
cd /path/to/StockLighthouse
python scripts/demo_analyzer.py
```

This demo:
1. Analyzes sample stock data
2. Shows sector aggregation results
3. Displays weighted averages
4. Loads and summarizes the sample sectors JSON file

## Sample Output

See `data/aggregates/sample_sectors.json` for an example of sector aggregation output with 28 stocks across 8 sectors.

## Testing

Run the comprehensive test suite:

```bash
cd backend
PYTHONPATH=src pytest tests/test_analyzer.py -v
```

The test suite includes 27 tests covering:
- Empty list handling
- Single and multiple sectors
- Median and average calculations
- None/missing value handling
- Unknown sector aggregation
- Edge cases
- Real-world scenarios

## Notes

- All market cap values are in absolute numbers (e.g., 2.4e12 for $2.4 trillion)
- Dividend yields are stored as decimals (e.g., 0.02 for 2%)
- Summaries are sorted by stock count (descending), then alphabetically by sector
- Top tickers are limited to 3 per sector
