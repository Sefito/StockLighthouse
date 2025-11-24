"""
Generate sample daily features for testing the scoring pipeline.

This script creates synthetic feature data that mimics real stock data
with technical and fundamental indicators.
"""

import pandas as pd
import numpy as np
from datetime import datetime

# Set seed for reproducibility
np.random.seed(42)

# Sample tickers (mix of different sectors)
tickers = [
    # Technology
    'AAPL', 'MSFT', 'GOOGL', 'META', 'NVDA', 'TSLA', 'AMD', 'INTC',
    # Healthcare
    'JNJ', 'UNH', 'PFE', 'ABBV', 'TMO', 'LLY',
    # Finance
    'JPM', 'BAC', 'WFC', 'GS', 'MS', 'C',
    # Consumer
    'WMT', 'HD', 'MCD', 'NKE', 'COST', 'SBUX',
    # Energy
    'XOM', 'CVX', 'COP', 'SLB',
    # Industrials
    'CAT', 'BA', 'HON', 'UPS', 'GE',
    # Others
    'DIS', 'V', 'MA', 'PYPL', 'NFLX',
]

n = len(tickers)

# Generate base data
data = {
    'symbol': tickers,
    
    # Basic stock info
    'price': np.random.uniform(50, 500, n),
    'market_cap': np.random.uniform(1e9, 3e12, n),
    'avg_volume': np.random.uniform(1e5, 5e7, n),
    'exchange': np.random.choice(['NMS', 'NYQ', 'NYSE'], n),
    
    # Technical indicators (raw values)
    'rsi': np.random.uniform(20, 80, n),  # RSI: 0-100
    'macd_signal': np.random.uniform(-5, 5, n),  # MACD signal
    'volume_trend': np.random.uniform(-0.3, 0.5, n),  # Volume change %
    'price_momentum': np.random.uniform(-0.2, 0.3, n),  # Price momentum
    'moving_avg_cross': np.random.uniform(-10, 10, n),  # SMA50 - SMA200
    'bollinger_position': np.random.uniform(0, 1, n),  # 0=lower band, 1=upper band
    
    # Fundamental indicators (raw values)
    'pe_ratio': np.random.uniform(5, 40, n),
    'pb_ratio': np.random.uniform(0.5, 8, n),
    'roe': np.random.uniform(0.05, 0.30, n),  # Return on equity
    'debt_to_equity': np.random.uniform(0.1, 2.5, n),
    'earnings_growth': np.random.uniform(-0.1, 0.4, n),  # Earnings growth rate
    'dividend_yield': np.random.uniform(0, 0.05, n),  # Dividend yield as decimal
}

df = pd.DataFrame(data)

# Add some variety to exchanges
df.loc[df['symbol'].isin(['GOOGL', 'META', 'NVDA', 'TSLA']), 'exchange'] = 'NMS'
df.loc[df['symbol'].isin(['JPM', 'BAC', 'WFC', 'C']), 'exchange'] = 'NYSE'

# Make some stocks have better technical indicators (oversold RSI, positive momentum)
strong_tech = df['symbol'].isin(['AAPL', 'MSFT', 'NVDA', 'JPM', 'UNH'])
df.loc[strong_tech, 'rsi'] = np.random.uniform(25, 40, strong_tech.sum())  # Oversold
df.loc[strong_tech, 'macd_signal'] = np.random.uniform(1, 5, strong_tech.sum())  # Positive
df.loc[strong_tech, 'price_momentum'] = np.random.uniform(0.1, 0.3, strong_tech.sum())  # Positive

# Make some stocks have better fundamentals (low P/E, high ROE)
strong_fund = df['symbol'].isin(['JNJ', 'WMT', 'JPM', 'HD', 'CAT'])
df.loc[strong_fund, 'pe_ratio'] = np.random.uniform(10, 18, strong_fund.sum())  # Low P/E
df.loc[strong_fund, 'roe'] = np.random.uniform(0.18, 0.30, strong_fund.sum())  # High ROE
df.loc[strong_fund, 'pb_ratio'] = np.random.uniform(2, 4, strong_fund.sum())  # Reasonable P/B

# Make some stocks fail filters (low price, low volume)
df.loc[df['symbol'].isin(['PYPL', 'NFLX']), 'price'] = np.random.uniform(2, 4, 2)  # Test low-price filter
df.loc[df['symbol'].isin(['SLB', 'GE']), 'avg_volume'] = np.random.uniform(5e4, 8e4, 2)  # Low volume

# Round to reasonable precision
df['price'] = df['price'].round(2)
df['market_cap'] = df['market_cap'].round(0)
df['avg_volume'] = df['avg_volume'].round(0)
df['rsi'] = df['rsi'].round(2)
df['macd_signal'] = df['macd_signal'].round(3)
df['volume_trend'] = df['volume_trend'].round(3)
df['price_momentum'] = df['price_momentum'].round(3)
df['moving_avg_cross'] = df['moving_avg_cross'].round(2)
df['bollinger_position'] = df['bollinger_position'].round(3)
df['pe_ratio'] = df['pe_ratio'].round(2)
df['pb_ratio'] = df['pb_ratio'].round(2)
df['roe'] = df['roe'].round(3)
df['debt_to_equity'] = df['debt_to_equity'].round(2)
df['earnings_growth'] = df['earnings_growth'].round(3)
df['dividend_yield'] = df['dividend_yield'].round(4)

# Add some NaN values to test robustness (5% missing data)
for col in ['pe_ratio', 'pb_ratio', 'roe', 'dividend_yield']:
    mask = np.random.rand(n) < 0.05
    df.loc[mask, col] = np.nan

# Save to parquet
output_path = 'data/features/daily_features.parquet'
df.to_parquet(output_path, index=False)

print(f"✓ Generated {len(df)} sample stocks with features")
print(f"✓ Saved to {output_path}")
print(f"\nSample data:")
print(df.head(10))
print(f"\nData info:")
print(df.info())
print(f"\nSummary statistics:")
print(df.describe())
