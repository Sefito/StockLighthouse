"""
Unit tests for normalization pipeline.

Tests corporate action adjustments, feature generation, and coverage checks.
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile

from backend.features.normalize_pipeline import (
    adjust_for_splits,
    adjust_for_dividends,
    apply_corporate_actions,
    handle_missing_data,
    normalize_and_generate_features,
    process_multi_ticker_data,
    check_feature_coverage
)


class TestCorporateActions:
    """Tests for corporate action adjustments."""
    
    def test_adjust_for_splits_basic(self):
        """Test basic split adjustment."""
        df = pd.DataFrame({
            'open': [100, 100, 100],
            'high': [105, 105, 105],
            'low': [95, 95, 95],
            'close': [100, 100, 100],
            'volume': [1000, 1000, 1000]
        })
        
        result = adjust_for_splits(df, 2.0)
        
        # Prices should be halved
        assert result['close'].iloc[0] == 50.0
        assert result['high'].iloc[0] == 52.5
        assert result['low'].iloc[0] == 47.5
        
        # Volume should be doubled
        assert result['volume'].iloc[0] == 2000
    
    def test_adjust_for_splits_no_split(self):
        """Test that ratio of 1.0 doesn't change data."""
        df = pd.DataFrame({
            'close': [100.0, 100.0, 100.0],
            'volume': [1000.0, 1000.0, 1000.0]
        })
        
        result = adjust_for_splits(df, 1.0)
        
        pd.testing.assert_frame_equal(result, df)
    
    def test_adjust_for_dividends_basic(self):
        """Test basic dividend adjustment."""
        df = pd.DataFrame({
            'open': [100, 100, 100],
            'high': [105, 105, 105],
            'low': [95, 95, 95],
            'close': [100, 100, 100]
        })
        
        result = adjust_for_dividends(df, 2.0)
        
        # All prices should be reduced by dividend amount
        assert result['close'].iloc[0] == 98.0
        assert result['high'].iloc[0] == 103.0
        assert result['low'].iloc[0] == 93.0
    
    def test_apply_corporate_actions_splits(self):
        """Test applying splits with dates."""
        dates = pd.date_range('2020-01-01', periods=10, freq='D')
        df = pd.DataFrame({
            'close': [100] * 10,
            'volume': [1000] * 10
        }, index=dates)
        
        actions = {
            'splits': [('2020-01-06', 2.0)]
        }
        
        result = apply_corporate_actions(df, actions)
        
        # Dates before split should be adjusted
        assert result.loc['2020-01-01', 'close'] == 50.0
        assert result.loc['2020-01-01', 'volume'] == 2000
        
        # Dates on/after split should be unchanged
        assert result.loc['2020-01-06', 'close'] == 100.0
        assert result.loc['2020-01-06', 'volume'] == 1000
    
    def test_apply_corporate_actions_dividends(self):
        """Test applying dividends with dates."""
        dates = pd.date_range('2020-01-01', periods=10, freq='D')
        df = pd.DataFrame({
            'close': [100] * 10
        }, index=dates)
        
        actions = {
            'dividends': [('2020-01-06', 1.0)]
        }
        
        result = apply_corporate_actions(df, actions)
        
        # Dates before dividend should be adjusted
        assert result.loc['2020-01-01', 'close'] == 99.0
        
        # Dates on/after dividend should be unchanged
        assert result.loc['2020-01-06', 'close'] == 100.0
    
    def test_apply_corporate_actions_none(self):
        """Test that None actions doesn't change data."""
        df = pd.DataFrame({
            'close': [100, 100, 100]
        })
        
        result = apply_corporate_actions(df, None)
        
        pd.testing.assert_frame_equal(result, df)


class TestMissingDataHandling:
    """Tests for missing data handling."""
    
    def test_handle_missing_data_ffill(self):
        """Test forward fill."""
        df = pd.DataFrame({
            'close': [100, np.nan, np.nan, 103, 104]
        })
        
        result = handle_missing_data(df, method='ffill')
        
        assert result['close'].iloc[1] == 100
        assert result['close'].iloc[2] == 100
        assert result['close'].iloc[3] == 103
    
    def test_handle_missing_data_bfill(self):
        """Test backward fill."""
        df = pd.DataFrame({
            'close': [100, np.nan, np.nan, 103, 104]
        })
        
        result = handle_missing_data(df, method='bfill')
        
        assert result['close'].iloc[1] == 103
        assert result['close'].iloc[2] == 103
    
    def test_handle_missing_data_limit(self):
        """Test fill with limit."""
        df = pd.DataFrame({
            'close': [100, np.nan, np.nan, np.nan, 104]
        })
        
        result = handle_missing_data(df, method='ffill', limit=2)
        
        # First two NaNs should be filled
        assert result['close'].iloc[1] == 100
        assert result['close'].iloc[2] == 100
        
        # Third NaN should remain (exceeds limit)
        assert pd.isna(result['close'].iloc[3])


class TestNormalizeAndGenerateFeatures:
    """Tests for the main normalization pipeline."""
    
    def test_normalize_and_generate_features_basic(self):
        """Test basic feature generation."""
        dates = pd.date_range('2020-01-01', periods=250, freq='D')
        df = pd.DataFrame({
            'open': 100 + np.random.randn(250).cumsum() * 0.5,
            'high': 101 + np.random.randn(250).cumsum() * 0.5,
            'low': 99 + np.random.randn(250).cumsum() * 0.5,
            'close': 100 + np.random.randn(250).cumsum() * 0.5,
            'volume': np.random.randint(1000000, 5000000, 250)
        }, index=dates)
        
        # Ensure high >= close >= low
        df['high'] = df[['open', 'high', 'low', 'close']].max(axis=1)
        df['low'] = df[['open', 'high', 'low', 'close']].min(axis=1)
        
        result = normalize_and_generate_features(df)
        
        # Check that indicators are present
        assert 'sma_10' in result.columns
        assert 'ema_20' in result.columns
        assert 'rsi_14' in result.columns
        assert 'macd' in result.columns
        
        # Check that we have the same number of rows
        assert len(result) == len(df)
    
    def test_normalize_and_generate_features_with_actions(self):
        """Test feature generation with corporate actions."""
        dates = pd.date_range('2020-01-01', periods=100, freq='D')
        df = pd.DataFrame({
            'close': [100] * 100,
            'high': [101] * 100,
            'low': [99] * 100,
            'volume': [1000000] * 100
        }, index=dates)
        
        actions = {
            'splits': [('2020-02-01', 2.0)]
        }
        
        result = normalize_and_generate_features(df, corporate_actions=actions)
        
        # Prices before split should be adjusted
        assert result.loc['2020-01-01', 'close'] == 50.0
        
        # Should still have indicators
        assert 'sma_10' in result.columns


class TestProcessMultiTickerData:
    """Tests for multi-ticker processing."""
    
    def test_process_multi_ticker_data_basic(self):
        """Test processing multiple tickers."""
        dates = pd.date_range('2020-01-01', periods=100, freq='D')
        
        data = {
            'AAPL': pd.DataFrame({
                'close': 100 + np.random.randn(100).cumsum() * 0.5,
                'high': 101 + np.random.randn(100).cumsum() * 0.5,
                'low': 99 + np.random.randn(100).cumsum() * 0.5,
                'volume': np.random.randint(1000000, 5000000, 100)
            }, index=dates),
            'MSFT': pd.DataFrame({
                'close': 200 + np.random.randn(100).cumsum() * 0.5,
                'high': 201 + np.random.randn(100).cumsum() * 0.5,
                'low': 199 + np.random.randn(100).cumsum() * 0.5,
                'volume': np.random.randint(1000000, 5000000, 100)
            }, index=dates)
        }
        
        # Fix high/low
        for ticker in data:
            data[ticker]['high'] = data[ticker][['high', 'low', 'close']].max(axis=1)
            data[ticker]['low'] = data[ticker][['high', 'low', 'close']].min(axis=1)
        
        result = process_multi_ticker_data(data)
        
        # Should have data for both tickers
        assert 'AAPL' in result['ticker'].values
        assert 'MSFT' in result['ticker'].values
        
        # Should have ticker and date columns
        assert 'ticker' in result.columns
        assert 'date' in result.columns
        
        # Should have indicators
        assert 'sma_10' in result.columns
        
        # Should have 200 total rows (100 per ticker)
        assert len(result) == 200
    
    def test_process_multi_ticker_data_with_output(self):
        """Test saving to parquet."""
        dates = pd.date_range('2020-01-01', periods=50, freq='D')
        
        data = {
            'TEST': pd.DataFrame({
                'close': 100 + np.random.randn(50).cumsum() * 0.5,
                'high': 101 + np.random.randn(50).cumsum() * 0.5,
                'low': 99 + np.random.randn(50).cumsum() * 0.5,
                'volume': np.random.randint(1000000, 5000000, 50)
            }, index=dates)
        }
        
        data['TEST']['high'] = data['TEST'][['high', 'low', 'close']].max(axis=1)
        data['TEST']['low'] = data['TEST'][['high', 'low', 'close']].min(axis=1)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "features.parquet"
            
            result = process_multi_ticker_data(data, output_path=output_path)
            
            # File should be created
            assert output_path.exists()
            
            # Should be able to read it back
            loaded = pd.read_parquet(output_path)
            assert len(loaded) == len(result)


class TestFeatureCoverage:
    """Tests for feature coverage checking."""
    
    def test_check_feature_coverage_high(self):
        """Test coverage check with high coverage."""
        # Create data with all features present
        dates = pd.date_range('2020-01-01', periods=10, freq='D')
        data = []
        
        for date in dates:
            for ticker in ['A', 'B', 'C', 'D', 'E']:
                data.append({
                    'ticker': ticker,
                    'date': date,
                    'close': 100,
                    'sma_10': 100,
                    'rsi_14': 50
                })
        
        df = pd.DataFrame(data)
        
        coverage = check_feature_coverage(df, threshold=0.95)
        
        # All dates should meet threshold
        assert coverage['dates_meeting_threshold'] == coverage['total_dates']
        assert coverage['average_coverage'] == 1.0
    
    def test_check_feature_coverage_low(self):
        """Test coverage check with low coverage."""
        # Create data with many missing features
        dates = pd.date_range('2020-01-01', periods=10, freq='D')
        data = []
        
        for date in dates:
            for i, ticker in enumerate(['A', 'B', 'C', 'D', 'E']):
                data.append({
                    'ticker': ticker,
                    'date': date,
                    'close': 100,
                    'sma_10': 100 if i < 2 else np.nan,  # Only 2/5 have features
                    'rsi_14': 50 if i < 2 else np.nan
                })
        
        df = pd.DataFrame(data)
        
        coverage = check_feature_coverage(df, threshold=0.95)
        
        # No dates should meet the 95% threshold (only 40% have features)
        assert coverage['dates_meeting_threshold'] == 0
        assert coverage['average_coverage'] < 0.5
    
    def test_check_feature_coverage_empty(self):
        """Test coverage check with empty DataFrame."""
        df = pd.DataFrame(columns=['ticker', 'date', 'close', 'sma_10'])
        
        coverage = check_feature_coverage(df)
        
        assert coverage['total_dates'] == 0


class TestEdgeCases:
    """Tests for edge cases in the pipeline."""
    
    def test_empty_ticker_dict(self):
        """Test with empty ticker dictionary."""
        with pytest.raises(ValueError, match="No tickers were successfully processed"):
            process_multi_ticker_data({})
    
    def test_missing_close_column(self):
        """Test with missing required column."""
        df = pd.DataFrame({
            'open': [100, 101, 102]
        })
        
        # Should raise KeyError when trying to compute indicators
        with pytest.raises(KeyError):
            normalize_and_generate_features(df)
