"""
Sample scoring functions for StockLighthouse.

This module provides baseline scoring functionality including:
- Feature normalization (min-max and z-score)
- Weighted score computation
- Rule-based filtering
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple


def normalize_minmax(values: np.ndarray) -> np.ndarray:
    """
    Normalize values to [0, 1] range using min-max scaling.
    
    Args:
        values: Array of numeric values to normalize
        
    Returns:
        Normalized array in [0, 1] range. Returns zeros if all values are equal.
        
    Example:
        >>> normalize_minmax(np.array([1, 2, 3, 4, 5]))
        array([0.  , 0.25, 0.5 , 0.75, 1.  ])
    """
    values = np.array(values, dtype=float)
    
    # Handle NaN and infinite values
    valid_mask = np.isfinite(values)
    if not valid_mask.any():
        return np.zeros_like(values)
    
    valid_values = values[valid_mask]
    min_val = np.min(valid_values)
    max_val = np.max(valid_values)
    
    # Handle case where all values are the same
    if max_val == min_val:
        result = np.zeros_like(values)
        result[valid_mask] = 0.5  # Middle value for equal values
        return result
    
    # Normalize
    result = np.zeros_like(values)
    result[valid_mask] = (valid_values - min_val) / (max_val - min_val)
    
    return result


def normalize_zscore(values: np.ndarray, clip_threshold: float = 3.0) -> np.ndarray:
    """
    Normalize values using z-score (standard score).
    
    Converts values to have mean=0 and std=1, then optionally clips outliers.
    
    Args:
        values: Array of numeric values to normalize
        clip_threshold: Maximum absolute z-score (clips outliers beyond this)
        
    Returns:
        Normalized z-scores, clipped to [-clip_threshold, +clip_threshold]
        
    Example:
        >>> normalize_zscore(np.array([1, 2, 3, 4, 5]))
        array([-1.41421356, -0.70710678,  0.        ,  0.70710678,  1.41421356])
    """
    values = np.array(values, dtype=float)
    
    # Handle NaN and infinite values
    valid_mask = np.isfinite(values)
    if not valid_mask.any():
        return np.zeros_like(values)
    
    valid_values = values[valid_mask]
    mean_val = np.mean(valid_values)
    std_val = np.std(valid_values)
    
    # Handle case where all values are the same
    if std_val == 0:
        return np.zeros_like(values)
    
    # Compute z-scores
    result = np.zeros_like(values)
    result[valid_mask] = (valid_values - mean_val) / std_val
    
    # Clip outliers
    if clip_threshold > 0:
        result = np.clip(result, -clip_threshold, clip_threshold)
    
    return result


def compute_weighted_score(
    features: Dict[str, np.ndarray],
    weights: Dict[str, float],
    invert_features: Optional[List[str]] = None
) -> np.ndarray:
    """
    Compute weighted score from multiple features.
    
    Args:
        features: Dictionary mapping feature names to normalized arrays
        weights: Dictionary mapping feature names to weights (should sum to 1.0)
        invert_features: List of feature names to invert (1 - value)
                        Useful for features where lower is better
        
    Returns:
        Weighted composite score array
        
    Example:
        >>> features = {'f1': np.array([0.5, 0.8]), 'f2': np.array([0.3, 0.6])}
        >>> weights = {'f1': 0.6, 'f2': 0.4}
        >>> compute_weighted_score(features, weights)
        array([0.42, 0.72])
    """
    if not features:
        raise ValueError("Features dictionary cannot be empty")
    
    invert_features = invert_features or []
    
    # Get array length from first feature
    first_key = next(iter(features))
    n = len(features[first_key])
    
    # Initialize score array
    score = np.zeros(n)
    total_weight = 0.0
    
    # Compute weighted sum
    for feature_name, weight in weights.items():
        if feature_name not in features:
            continue
            
        feature_values = np.array(features[feature_name], dtype=float)
        
        # Invert if specified
        if feature_name in invert_features:
            feature_values = 1.0 - feature_values
        
        score += weight * feature_values
        total_weight += weight
    
    # Normalize by actual total weight used
    # This ensures scores remain in [0, 1] range even when some features are missing
    # For example, if only 0.7 of the total weight is available, we divide by 0.7
    # rather than the nominal 1.0, so the final score still spans [0, 1]
    if total_weight > 0:
        score /= total_weight
    
    return score


def apply_filters(
    df: pd.DataFrame,
    min_market_cap: Optional[float] = None,
    min_avg_volume: Optional[float] = None,
    min_price: Optional[float] = None,
    max_pe_ratio: Optional[float] = None,
    tradable_exchanges: Optional[List[str]] = None
) -> pd.DataFrame:
    """
    Apply rule-based filters to remove non-tradable stocks.
    
    Args:
        df: DataFrame with stock data
        min_market_cap: Minimum market capitalization
        min_avg_volume: Minimum average daily volume
        min_price: Minimum stock price
        max_pe_ratio: Maximum P/E ratio
        tradable_exchanges: List of acceptable exchange codes
        
    Returns:
        Filtered DataFrame
        
    Example:
        >>> df = pd.DataFrame({
        ...     'symbol': ['AAPL', 'PENNY'],
        ...     'price': [150.0, 2.0],
        ...     'market_cap': [2e12, 1e8]
        ... })
        >>> filtered = apply_filters(df, min_price=5.0, min_market_cap=1e9)
        >>> list(filtered['symbol'])
        ['AAPL']
    """
    result = df.copy()
    initial_count = len(result)
    
    # Apply market cap filter
    if min_market_cap is not None and 'market_cap' in result.columns:
        result = result[result['market_cap'] >= min_market_cap]
    
    # Apply volume filter
    if min_avg_volume is not None and 'avg_volume' in result.columns:
        result = result[result['avg_volume'] >= min_avg_volume]
    
    # Apply price filter
    if min_price is not None and 'price' in result.columns:
        result = result[result['price'] >= min_price]
    
    # Apply P/E ratio filter
    if max_pe_ratio is not None and 'pe_ratio' in result.columns:
        result = result[
            (result['pe_ratio'].isna()) | (result['pe_ratio'] <= max_pe_ratio)
        ]
    
    # Apply exchange filter
    if tradable_exchanges and 'exchange' in result.columns:
        result = result[result['exchange'].isin(tradable_exchanges)]
    
    filtered_count = initial_count - len(result)
    if filtered_count > 0:
        print(f"Filtered out {filtered_count} stocks ({initial_count} -> {len(result)})")
    
    return result


def get_top_k_with_explanations(
    df: pd.DataFrame,
    score_column: str,
    feature_columns: List[str],
    k: int = 100
) -> pd.DataFrame:
    """
    Get top K stocks by score with per-feature contributions.
    
    Args:
        df: DataFrame with scores and features
        score_column: Name of the score column to rank by
        feature_columns: List of feature columns to include in explanations
        k: Number of top stocks to return
        
    Returns:
        DataFrame with top K stocks sorted by score
        
    Example:
        >>> df = pd.DataFrame({
        ...     'symbol': ['A', 'B', 'C'],
        ...     'score': [0.9, 0.7, 0.8],
        ...     'f1': [0.8, 0.6, 0.7]
        ... })
        >>> top = get_top_k_with_explanations(df, 'score', ['f1'], k=2)
        >>> list(top['symbol'])
        ['A', 'C']
    """
    if score_column not in df.columns:
        raise ValueError(f"Score column '{score_column}' not found in DataFrame")
    
    # Sort by score descending
    result = df.sort_values(score_column, ascending=False).head(k).copy()
    
    return result


def create_explanation_text(
    row: pd.Series,
    feature_columns: List[str],
    top_n_features: int = 3
) -> str:
    """
    Create human-readable explanation for why a stock scored well.
    
    Args:
        row: DataFrame row containing stock data and scores
        feature_columns: List of feature columns to consider
        top_n_features: Number of top contributing features to mention
        
    Returns:
        Explanation string
        
    Example:
        >>> row = pd.Series({
        ...     'symbol': 'AAPL',
        ...     'composite_score': 0.85,
        ...     'tech_score': 0.90,
        ...     'fund_score': 0.75,
        ...     'rsi': 0.8,
        ...     'pe_ratio': 0.7
        ... })
        >>> create_explanation_text(row, ['rsi', 'pe_ratio'])
        'AAPL scored 0.85 (tech: 0.90, fund: 0.75). Top factors: rsi (0.80), pe_ratio (0.70)'
    """
    symbol = row.get('symbol', 'Unknown')
    composite = row.get('composite_score', 0)
    tech = row.get('tech_score', 0)
    fund = row.get('fund_score', 0)
    
    # Get top contributing features
    feature_values = []
    for feat in feature_columns:
        if feat in row and pd.notna(row[feat]):
            feature_values.append((feat, row[feat]))
    
    # Sort by absolute value (contribution)
    feature_values.sort(key=lambda x: abs(x[1]), reverse=True)
    top_features = feature_values[:top_n_features]
    
    # Build explanation
    explanation = f"{symbol} scored {composite:.2f} (tech: {tech:.2f}, fund: {fund:.2f})"
    
    if top_features:
        features_str = ", ".join([f"{name} ({val:.2f})" for name, val in top_features])
        explanation += f". Top factors: {features_str}"
    
    return explanation
