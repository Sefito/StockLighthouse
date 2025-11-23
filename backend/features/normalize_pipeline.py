"""
Normalization pipeline for feature generation.

Handles:
- Corporate action adjustments (splits/dividends)
- Feature computation with standardized naming
- Missing data handling (forward fill, backfill)
- Output to parquet format
"""
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Optional, Dict, Any
import logging

try:
    from backend.features.indicators import compute_all_indicators
except ImportError:
    from features.indicators import compute_all_indicators

logger = logging.getLogger(__name__)


def adjust_for_splits(df: pd.DataFrame, split_ratio: float = 1.0) -> pd.DataFrame:
    """
    Adjust price and volume data for stock splits.
    
    Args:
        df: DataFrame with price/volume columns
        split_ratio: Split ratio (e.g., 2.0 for 2-for-1 split)
        
    Returns:
        Adjusted DataFrame
    """
    result = df.copy()
    
    # Adjust prices (divide by split ratio)
    price_columns = ['open', 'high', 'low', 'close']
    for col in price_columns:
        if col in result.columns:
            result[col] = result[col].astype(float) / split_ratio
    
    # Adjust volume (multiply by split ratio)
    if 'volume' in result.columns:
        result['volume'] = result['volume'].astype(float) * split_ratio
    
    return result


def adjust_for_dividends(df: pd.DataFrame, dividend_amount: float) -> pd.DataFrame:
    """
    Adjust price data for dividend payments.
    
    Args:
        df: DataFrame with price columns
        dividend_amount: Dividend amount per share
        
    Returns:
        Adjusted DataFrame
    """
    result = df.copy()
    
    # Adjust prices (subtract dividend)
    price_columns = ['open', 'high', 'low', 'close']
    for col in price_columns:
        if col in result.columns:
            result[col] = result[col] - dividend_amount
    
    return result


def apply_corporate_actions(df: pd.DataFrame, 
                           actions: Optional[Dict[str, Any]] = None) -> pd.DataFrame:
    """
    Apply corporate action adjustments to price data.
    
    Args:
        df: DataFrame with price/volume data
        actions: Dictionary with 'splits' and 'dividends' information
                 Format: {'splits': [(date, ratio), ...], 
                         'dividends': [(date, amount), ...]}
        
    Returns:
        Adjusted DataFrame
    """
    if not actions:
        return df
    
    result = df.copy()
    
    # Convert to float to avoid dtype warnings
    price_columns = ['open', 'high', 'low', 'close']
    for col in price_columns:
        if col in result.columns:
            result[col] = result[col].astype(float)
    if 'volume' in result.columns:
        result['volume'] = result['volume'].astype(float)
    
    # Apply splits
    if 'splits' in actions:
        for split_date, split_ratio in actions['splits']:
            mask = result.index < pd.to_datetime(split_date)
            if mask.any():
                result.loc[mask] = adjust_for_splits(result.loc[mask], split_ratio)
    
    # Apply dividends
    if 'dividends' in actions:
        for div_date, div_amount in actions['dividends']:
            mask = result.index < pd.to_datetime(div_date)
            if mask.any():
                result.loc[mask] = adjust_for_dividends(result.loc[mask], div_amount)
    
    return result


def handle_missing_data(df: pd.DataFrame, 
                       method: str = 'ffill',
                       limit: Optional[int] = None) -> pd.DataFrame:
    """
    Handle missing data in the DataFrame.
    
    Args:
        df: DataFrame with potential missing values
        method: 'ffill' (forward fill), 'bfill' (backward fill), or 'interpolate'
        limit: Maximum number of consecutive NaN values to fill
        
    Returns:
        DataFrame with missing values handled
    """
    result = df.copy()
    
    if method == 'ffill':
        result = result.ffill(limit=limit)
    elif method == 'bfill':
        result = result.bfill(limit=limit)
    elif method == 'interpolate':
        result = result.interpolate(method='linear', limit=limit)
    else:
        logger.warning(f"Unknown method '{method}', using forward fill")
        result = result.ffill(limit=limit)
    
    return result


def load_price_data(input_path: Path) -> pd.DataFrame:
    """
    Load price data from parquet file.
    
    Args:
        input_path: Path to prices.parquet file
        
    Returns:
        DataFrame with price data
    """
    if input_path.suffix == '.parquet':
        df = pd.read_parquet(input_path)
    elif input_path.suffix == '.csv':
        df = pd.read_csv(input_path)
    else:
        raise ValueError(f"Unsupported file format: {input_path.suffix}")
    
    # Ensure date column is datetime and set as index if needed
    if 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date'])
        if df.index.name != 'date':
            df = df.set_index('date')
    
    return df


def normalize_and_generate_features(prices_df: pd.DataFrame,
                                   corporate_actions: Optional[Dict[str, Any]] = None,
                                   fill_method: str = 'ffill') -> pd.DataFrame:
    """
    Normalize prices and generate technical indicators.
    
    This is the main pipeline function that:
    1. Applies corporate action adjustments
    2. Handles missing data
    3. Computes all technical indicators
    
    Args:
        prices_df: DataFrame with OHLCV data (indexed by date)
        corporate_actions: Optional dict with corporate actions
        fill_method: Method for handling missing data ('ffill', 'bfill', 'interpolate')
        
    Returns:
        DataFrame with normalized prices and computed features
    """
    # Apply corporate actions
    if corporate_actions:
        logger.info("Applying corporate action adjustments")
        prices_df = apply_corporate_actions(prices_df, corporate_actions)
    
    # Handle missing data (before computing indicators)
    logger.info(f"Handling missing data with method: {fill_method}")
    prices_df = handle_missing_data(prices_df, method=fill_method, limit=5)
    
    # Compute all technical indicators
    logger.info("Computing technical indicators")
    features_df = compute_all_indicators(prices_df)
    
    # Apply forward fill to indicator columns to handle edge cases
    # (initial periods where indicators can't be computed)
    indicator_cols = [col for col in features_df.columns 
                     if col not in ['open', 'high', 'low', 'close', 'volume']]
    features_df[indicator_cols] = features_df[indicator_cols].ffill(limit=10)
    
    return features_df


def process_multi_ticker_data(data: Dict[str, pd.DataFrame],
                             corporate_actions: Optional[Dict[str, Dict[str, Any]]] = None,
                             output_path: Optional[Path] = None) -> pd.DataFrame:
    """
    Process multiple tickers and generate features for all.
    
    Args:
        data: Dictionary mapping ticker symbols to their price DataFrames
        corporate_actions: Optional dict mapping tickers to their corporate actions
        output_path: Optional path to save the output parquet file
        
    Returns:
        Combined DataFrame with ticker, date, and all features
    """
    all_features = []
    
    for ticker, prices_df in data.items():
        logger.info(f"Processing {ticker}")
        
        # Get corporate actions for this ticker if available
        ticker_actions = corporate_actions.get(ticker) if corporate_actions else None
        
        try:
            # Generate features
            features_df = normalize_and_generate_features(prices_df, ticker_actions)
            
            # Add ticker column
            features_df['ticker'] = ticker
            
            # Reset index to make date a column
            features_df = features_df.reset_index()
            
            # Rename index column to 'date' if it's not already named
            if features_df.columns[0] != 'date':
                features_df = features_df.rename(columns={features_df.columns[0]: 'date'})
            
            all_features.append(features_df)
            
        except Exception as e:
            logger.error(f"Error processing {ticker}: {e}")
            continue
    
    if not all_features:
        raise ValueError("No tickers were successfully processed")
    
    # Combine all tickers
    combined_df = pd.concat(all_features, ignore_index=True)
    
    # Reorder columns: ticker, date, then features
    if 'date' in combined_df.columns:
        cols = ['ticker', 'date'] + [col for col in combined_df.columns 
                                      if col not in ['ticker', 'date']]
        combined_df = combined_df[cols]
    
    # Sort by ticker and date
    combined_df = combined_df.sort_values(['ticker', 'date'])
    
    # Save to parquet if output path provided
    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        combined_df.to_parquet(output_path, index=False)
        logger.info(f"Saved features to {output_path}")
    
    return combined_df


def check_feature_coverage(df: pd.DataFrame, threshold: float = 0.95) -> Dict[str, Any]:
    """
    Check feature coverage per trading date.
    
    Acceptance criteria: >95% of tickers should have features for each date.
    
    Args:
        df: DataFrame with ticker, date, and feature columns
        threshold: Minimum coverage threshold (default: 0.95)
        
    Returns:
        Dictionary with coverage statistics
    """
    if len(df) == 0:
        # Handle empty DataFrame
        return {
            'by_date': pd.DataFrame(columns=['date', 'total_tickers', 'tickers_with_features', 'coverage', 'meets_threshold']),
            'dates_meeting_threshold': 0,
            'total_dates': 0,
            'percentage_dates_meeting_threshold': 0,
            'average_coverage': 0,
            'min_coverage': 0,
            'max_coverage': 0
        }
    
    # Group by date
    by_date = df.groupby('date')
    
    # Count total tickers and tickers with non-null features for each date
    coverage_stats = []
    
    # Get feature columns (exclude ticker, date, and base OHLCV)
    feature_cols = [col for col in df.columns 
                   if col not in ['ticker', 'date', 'open', 'high', 'low', 'close', 'volume']]
    
    for date, group in by_date:
        total_tickers = len(group)
        
        # Count tickers with at least one non-null feature
        tickers_with_features = group[feature_cols].notna().any(axis=1).sum()
        
        coverage = tickers_with_features / total_tickers if total_tickers > 0 else 0
        
        coverage_stats.append({
            'date': date,
            'total_tickers': total_tickers,
            'tickers_with_features': tickers_with_features,
            'coverage': coverage,
            'meets_threshold': coverage >= threshold
        })
    
    coverage_df = pd.DataFrame(coverage_stats)
    
    # Overall statistics
    dates_meeting_threshold = coverage_df['meets_threshold'].sum() if len(coverage_df) > 0 else 0
    total_dates = len(coverage_df)
    
    return {
        'by_date': coverage_df,
        'dates_meeting_threshold': dates_meeting_threshold,
        'total_dates': total_dates,
        'percentage_dates_meeting_threshold': dates_meeting_threshold / total_dates if total_dates > 0 else 0,
        'average_coverage': coverage_df['coverage'].mean() if len(coverage_df) > 0 else 0,
        'min_coverage': coverage_df['coverage'].min() if len(coverage_df) > 0 else 0,
        'max_coverage': coverage_df['coverage'].max() if len(coverage_df) > 0 else 0
    }
