"""
Tests for scoring functions in sample_scoring.py
"""

import numpy as np
import pandas as pd
import pytest

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scoring.sample_scoring import (
    normalize_minmax,
    normalize_zscore,
    compute_weighted_score,
    apply_filters,
    get_top_k_with_explanations,
    create_explanation_text,
)


class TestNormalizeMinMax:
    """Tests for min-max normalization."""
    
    def test_basic_normalization(self):
        values = np.array([1, 2, 3, 4, 5])
        result = normalize_minmax(values)
        expected = np.array([0.0, 0.25, 0.5, 0.75, 1.0])
        np.testing.assert_array_almost_equal(result, expected)
    
    def test_all_same_values(self):
        values = np.array([5.0, 5.0, 5.0])
        result = normalize_minmax(values)
        expected = np.array([0.5, 0.5, 0.5])
        np.testing.assert_array_almost_equal(result, expected)
    
    def test_with_nan(self):
        values = np.array([1, 2, np.nan, 4, 5])
        result = normalize_minmax(values)
        assert np.isfinite(result[0])
        assert np.isfinite(result[1])
        # NaN is replaced with 0 (defensive behavior)
        assert result[2] == 0.0
    
    def test_with_infinity(self):
        values = np.array([1, 2, np.inf, 4, 5])
        result = normalize_minmax(values)
        assert np.isfinite(result[0])
        assert np.isfinite(result[1])
        # Infinity is replaced with 0 (defensive behavior)
        assert result[2] == 0.0
    
    def test_all_nan(self):
        values = np.array([np.nan, np.nan, np.nan])
        result = normalize_minmax(values)
        assert len(result) == 3
        # All NaNs become 0 (defensive behavior)
        np.testing.assert_array_equal(result, np.zeros(3))
    
    def test_negative_values(self):
        values = np.array([-2, -1, 0, 1, 2])
        result = normalize_minmax(values)
        expected = np.array([0.0, 0.25, 0.5, 0.75, 1.0])
        np.testing.assert_array_almost_equal(result, expected)


class TestNormalizeZScore:
    """Tests for z-score normalization."""
    
    def test_basic_normalization(self):
        values = np.array([1, 2, 3, 4, 5])
        result = normalize_zscore(values, clip_threshold=3.0)
        # Mean should be close to 0
        assert abs(result.mean()) < 0.1
        # Should be within [-3, 3] after clipping
        assert result.min() >= -3.0
        assert result.max() <= 3.0
    
    def test_all_same_values(self):
        values = np.array([5.0, 5.0, 5.0])
        result = normalize_zscore(values)
        expected = np.array([0.0, 0.0, 0.0])
        np.testing.assert_array_almost_equal(result, expected)
    
    def test_outlier_clipping(self):
        values = np.array([1, 2, 3, 100])  # 100 is an outlier
        result = normalize_zscore(values, clip_threshold=2.0)
        assert result.min() >= -2.0
        assert result.max() <= 2.0
    
    def test_with_nan(self):
        values = np.array([1, 2, np.nan, 4, 5])
        result = normalize_zscore(values)
        assert np.isfinite(result[0])
        assert np.isfinite(result[1])
        # NaN is replaced with 0 (defensive behavior)
        assert result[2] == 0.0
    
    def test_no_clipping(self):
        values = np.array([1, 2, 3, 4, 100])
        result = normalize_zscore(values, clip_threshold=0)
        # Should not clip
        assert len(result) == 5


class TestComputeWeightedScore:
    """Tests for weighted score computation."""
    
    def test_basic_weighted_score(self):
        features = {
            'f1': np.array([0.5, 0.8]),
            'f2': np.array([0.3, 0.6])
        }
        weights = {'f1': 0.6, 'f2': 0.4}
        result = compute_weighted_score(features, weights)
        expected = np.array([0.5 * 0.6 + 0.3 * 0.4, 0.8 * 0.6 + 0.6 * 0.4])
        np.testing.assert_array_almost_equal(result, expected)
    
    def test_with_invert(self):
        features = {
            'f1': np.array([0.5, 0.8]),
            'f2': np.array([0.3, 0.6])
        }
        weights = {'f1': 0.6, 'f2': 0.4}
        result = compute_weighted_score(features, weights, invert_features=['f2'])
        # f2 should be inverted: 1 - value
        expected = np.array([0.5 * 0.6 + (1 - 0.3) * 0.4, 0.8 * 0.6 + (1 - 0.6) * 0.4])
        np.testing.assert_array_almost_equal(result, expected)
    
    def test_missing_feature(self):
        features = {
            'f1': np.array([0.5, 0.8])
        }
        weights = {'f1': 0.6, 'f2': 0.4}  # f2 doesn't exist
        result = compute_weighted_score(features, weights)
        # Should still work, just normalize by actual weight used
        expected = np.array([0.5, 0.8])
        np.testing.assert_array_almost_equal(result, expected)
    
    def test_empty_features(self):
        features = {}
        weights = {'f1': 0.6}
        with pytest.raises(ValueError):
            compute_weighted_score(features, weights)


class TestApplyFilters:
    """Tests for rule-based filtering."""
    
    def test_market_cap_filter(self):
        df = pd.DataFrame({
            'symbol': ['A', 'B', 'C'],
            'market_cap': [1e12, 5e8, 2e9]
        })
        result = apply_filters(df, min_market_cap=1e9)
        assert len(result) == 2
        assert 'A' in result['symbol'].values
        assert 'C' in result['symbol'].values
    
    def test_price_filter(self):
        df = pd.DataFrame({
            'symbol': ['A', 'B', 'C'],
            'price': [100, 3, 50]
        })
        result = apply_filters(df, min_price=5.0)
        assert len(result) == 2
        assert 'B' not in result['symbol'].values
    
    def test_volume_filter(self):
        df = pd.DataFrame({
            'symbol': ['A', 'B', 'C'],
            'avg_volume': [1e6, 5e4, 2e5]
        })
        result = apply_filters(df, min_avg_volume=1e5)
        assert len(result) == 2
        assert 'B' not in result['symbol'].values
    
    def test_pe_ratio_filter(self):
        df = pd.DataFrame({
            'symbol': ['A', 'B', 'C'],
            'pe_ratio': [15, 150, 25]
        })
        result = apply_filters(df, max_pe_ratio=100)
        assert len(result) == 2
        assert 'B' not in result['symbol'].values
    
    def test_pe_ratio_filter_with_nan(self):
        df = pd.DataFrame({
            'symbol': ['A', 'B', 'C'],
            'pe_ratio': [15, np.nan, 25]
        })
        result = apply_filters(df, max_pe_ratio=100)
        # NaN values should pass through
        assert len(result) == 3
    
    def test_exchange_filter(self):
        df = pd.DataFrame({
            'symbol': ['A', 'B', 'C'],
            'exchange': ['NMS', 'LSE', 'NYSE']
        })
        result = apply_filters(df, tradable_exchanges=['NMS', 'NYSE'])
        assert len(result) == 2
        assert 'B' not in result['symbol'].values
    
    def test_multiple_filters(self):
        df = pd.DataFrame({
            'symbol': ['A', 'B', 'C', 'D'],
            'price': [100, 3, 50, 200],
            'market_cap': [1e12, 5e8, 2e9, 3e12],
            'exchange': ['NMS', 'NMS', 'LSE', 'NYSE']
        })
        result = apply_filters(
            df,
            min_price=5.0,
            min_market_cap=1e9,
            tradable_exchanges=['NMS', 'NYSE']
        )
        assert len(result) == 2  # Only A and D
        assert set(result['symbol']) == {'A', 'D'}


class TestGetTopKWithExplanations:
    """Tests for getting top K stocks."""
    
    def test_basic_top_k(self):
        df = pd.DataFrame({
            'symbol': ['A', 'B', 'C', 'D'],
            'score': [0.9, 0.7, 0.8, 0.6],
            'f1': [0.8, 0.6, 0.7, 0.5]
        })
        result = get_top_k_with_explanations(df, 'score', ['f1'], k=2)
        assert len(result) == 2
        assert list(result['symbol']) == ['A', 'C']
    
    def test_k_larger_than_df(self):
        df = pd.DataFrame({
            'symbol': ['A', 'B'],
            'score': [0.9, 0.7]
        })
        result = get_top_k_with_explanations(df, 'score', [], k=10)
        assert len(result) == 2
    
    def test_missing_score_column(self):
        df = pd.DataFrame({
            'symbol': ['A', 'B'],
            'other': [0.9, 0.7]
        })
        with pytest.raises(ValueError):
            get_top_k_with_explanations(df, 'score', [], k=2)


class TestCreateExplanationText:
    """Tests for creating explanation text."""
    
    def test_basic_explanation(self):
        row = pd.Series({
            'symbol': 'AAPL',
            'composite_score': 0.85,
            'tech_score': 0.90,
            'fund_score': 0.75,
            'rsi': 0.8,
            'pe_ratio': 0.7
        })
        result = create_explanation_text(row, ['rsi', 'pe_ratio'])
        assert 'AAPL' in result
        assert '0.85' in result
        assert 'rsi' in result
        assert 'pe_ratio' in result
    
    def test_with_top_n_features(self):
        row = pd.Series({
            'symbol': 'MSFT',
            'composite_score': 0.75,
            'tech_score': 0.80,
            'fund_score': 0.65,
            'f1': 0.9,
            'f2': 0.1,
            'f3': 0.5
        })
        result = create_explanation_text(row, ['f1', 'f2', 'f3'], top_n_features=2)
        # Should include top 2 by absolute value
        assert 'f1' in result
        assert ('f2' in result or 'f3' in result)
    
    def test_with_nan_values(self):
        row = pd.Series({
            'symbol': 'TEST',
            'composite_score': 0.5,
            'tech_score': 0.6,
            'fund_score': 0.4,
            'f1': 0.8,
            'f2': np.nan,
            'f3': 0.3
        })
        result = create_explanation_text(row, ['f1', 'f2', 'f3'])
        assert 'TEST' in result
        assert 'f1' in result
        # f2 should be skipped (NaN)
        assert result.count('0.80') > 0  # f1 value


class TestIntegration:
    """Integration tests for the complete scoring workflow."""
    
    def test_end_to_end_scoring(self):
        # Create sample data
        df = pd.DataFrame({
            'symbol': ['A', 'B', 'C', 'D', 'E'],
            'price': [100, 50, 200, 3, 150],
            'market_cap': [1e12, 5e11, 2e12, 1e8, 8e11],
            'exchange': ['NMS', 'NYSE', 'NMS', 'NMS', 'NYSE'],
            'rsi': [35, 65, 45, 75, 40],
            'pe_ratio': [15, 25, 20, 200, 18]
        })
        
        # Apply filters
        filtered = apply_filters(
            df,
            min_price=5.0,
            min_market_cap=1e9,
            tradable_exchanges=['NMS', 'NYSE']
        )
        
        # Should filter out D (low price and market cap)
        assert len(filtered) == 4
        assert 'D' not in filtered['symbol'].values
        
        # Normalize features
        filtered['norm_rsi'] = normalize_minmax(filtered['rsi'].values)
        filtered['norm_pe'] = normalize_minmax(filtered['pe_ratio'].values)
        
        # Compute score
        features = {
            'norm_rsi': filtered['norm_rsi'].values,
            'norm_pe': filtered['norm_pe'].values
        }
        weights = {'norm_rsi': 0.6, 'norm_pe': 0.4}
        filtered['score'] = compute_weighted_score(features, weights)
        
        # Get top K
        top = get_top_k_with_explanations(filtered, 'score', ['norm_rsi', 'norm_pe'], k=2)
        
        assert len(top) == 2
        assert all(col in top.columns for col in ['symbol', 'score', 'norm_rsi', 'norm_pe'])
