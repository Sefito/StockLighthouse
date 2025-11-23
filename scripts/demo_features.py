#!/usr/bin/env python3
"""
Demo script for feature generation pipeline.

This script demonstrates:
1. Generating sample price data
2. Applying corporate actions
3. Computing technical indicators
4. Checking feature coverage
5. Saving to parquet

Usage:
    python scripts/demo_features.py
"""
import sys
from pathlib import Path
import pandas as pd
import numpy as np

# Add backend to path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from features.indicators import compute_all_indicators
from features.normalize_pipeline import (
    process_multi_ticker_data,
    check_feature_coverage,
    normalize_and_generate_features
)


def generate_sample_price_data(ticker: str, days: int = 250) -> pd.DataFrame:
    """
    Generate realistic sample price data for testing.
    
    Args:
        ticker: Stock symbol
        days: Number of trading days to generate
        
    Returns:
        DataFrame with OHLCV data
    """
    # Generate dates (trading days only)
    dates = pd.date_range(end='2024-01-01', periods=days, freq='B')
    
    # Start with a base price and add random walk
    base_price = 100 if ticker == 'AAPL' else (200 if ticker == 'MSFT' else 150)
    
    # Generate close prices using geometric Brownian motion
    np.random.seed(hash(ticker) % 2**32)
    returns = np.random.normal(0.0005, 0.02, days)
    prices = base_price * np.exp(np.cumsum(returns))
    
    # Generate OHLC from close prices
    df = pd.DataFrame({
        'close': prices
    }, index=dates)
    
    # High is close + some random amount
    df['high'] = df['close'] * (1 + np.abs(np.random.normal(0, 0.01, days)))
    
    # Low is close - some random amount
    df['low'] = df['close'] * (1 - np.abs(np.random.normal(0, 0.01, days)))
    
    # Open is somewhere between previous close and current close
    df['open'] = df['close'].shift(1).fillna(df['close'].iloc[0]) * (1 + np.random.normal(0, 0.005, days))
    
    # Volume with some randomness
    base_volume = 1000000 if ticker == 'AAPL' else (800000 if ticker == 'MSFT' else 600000)
    df['volume'] = np.random.randint(int(base_volume * 0.5), int(base_volume * 1.5), days)
    
    # Ensure high >= close >= low
    df['high'] = df[['open', 'high', 'low', 'close']].max(axis=1)
    df['low'] = df[['open', 'high', 'low', 'close']].min(axis=1)
    
    return df


def main():
    """Main execution."""
    print("=" * 80)
    print("Feature Generation Pipeline Demo")
    print("=" * 80)
    
    # Setup paths
    base_dir = Path(__file__).parent.parent
    output_dir = base_dir / "data" / "features"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate sample data for multiple tickers
    print("\n1. Generating sample price data...")
    print("-" * 80)
    
    tickers = ['AAPL', 'MSFT', 'GOOGL']
    data = {}
    
    for ticker in tickers:
        print(f"   Generating {ticker} price data (250 trading days)")
        data[ticker] = generate_sample_price_data(ticker, days=250)
    
    print(f"\n   ✓ Generated data for {len(tickers)} tickers")
    
    # Process with feature generation
    print("\n2. Computing technical indicators...")
    print("-" * 80)
    
    # Define some corporate actions for demonstration
    corporate_actions = {
        'AAPL': {
            'splits': [('2023-08-01', 2.0)]  # 2-for-1 split
        }
    }
    
    output_path = output_dir / "daily_features.parquet"
    
    features_df = process_multi_ticker_data(
        data,
        corporate_actions=corporate_actions,
        output_path=output_path
    )
    
    print(f"\n   ✓ Computed {len(features_df.columns) - 2} features per ticker")
    print(f"   ✓ Total rows: {len(features_df)}")
    
    # Check feature coverage
    print("\n3. Checking feature coverage...")
    print("-" * 80)
    
    coverage = check_feature_coverage(features_df, threshold=0.95)
    
    print(f"   Average coverage:        {coverage['average_coverage']:.1%}")
    print(f"   Min coverage:            {coverage['min_coverage']:.1%}")
    print(f"   Max coverage:            {coverage['max_coverage']:.1%}")
    print(f"   Dates meeting threshold: {coverage['dates_meeting_threshold']}/{coverage['total_dates']}")
    print(f"   Percentage:              {coverage['percentage_dates_meeting_threshold']:.1%}")
    
    if coverage['percentage_dates_meeting_threshold'] >= 0.95:
        print("\n   ✓ PASSED: >95% of dates meet feature coverage threshold")
    else:
        print("\n   ⚠ WARNING: Feature coverage below 95% threshold")
    
    # Display sample features
    print("\n4. Sample features (last 5 days for AAPL)...")
    print("-" * 80)
    
    aapl_features = features_df[features_df['ticker'] == 'AAPL'].tail(5)
    
    # Select interesting columns to display
    display_cols = ['ticker', 'date', 'close', 'sma_50', 'rsi_14', 'macd', 'volatility_30']
    
    for col in display_cols:
        if col in aapl_features.columns:
            print(f"\n{col}:")
            if col in ['ticker', 'date']:
                for val in aapl_features[col].values:
                    print(f"  {val}")
            else:
                for val in aapl_features[col].values:
                    if pd.notna(val):
                        print(f"  {val:,.2f}")
                    else:
                        print(f"  N/A")
    
    # Summary statistics
    print("\n5. Indicator statistics across all tickers...")
    print("-" * 80)
    
    indicator_cols = ['sma_10', 'sma_50', 'rsi_14', 'macd', 'atr_14', 'momentum_20']
    
    print(f"\n{'Indicator':<20} {'Mean':<12} {'Std':<12} {'Coverage':<12}")
    print("-" * 80)
    
    for col in indicator_cols:
        if col in features_df.columns:
            values = features_df[col].dropna()
            coverage_pct = (len(values) / len(features_df)) * 100
            
            if len(values) > 0:
                print(f"{col:<20} {values.mean():>11.2f} {values.std():>11.2f} {coverage_pct:>10.1f}%")
            else:
                print(f"{col:<20} {'N/A':>11} {'N/A':>11} {coverage_pct:>10.1f}%")
    
    # Save summary
    print("\n6. Output files...")
    print("-" * 80)
    print(f"   Features saved to: {output_path}")
    print(f"   File size:         {output_path.stat().st_size / 1024:.1f} KB")
    
    # Test reading back
    test_df = pd.read_parquet(output_path)
    print(f"   Verified readback: {len(test_df)} rows")
    
    print("\n" + "=" * 80)
    print("✓ Feature generation pipeline completed successfully!")
    print("=" * 80)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
