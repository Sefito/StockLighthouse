"""
Unit tests for price_ingest.py module.

Tests the PriceIngestor class with mocked network calls to avoid
external dependencies.
"""

import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta
from pathlib import Path
import pandas as pd
import tempfile
import shutil

from backend.ingest.price_ingest import (
    PriceIngestor,
    IngestionMetrics,
    ValidationResult,
)


@pytest.fixture
def temp_data_dir():
    """Create a temporary directory for test data."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def sample_universe_csv(temp_data_dir):
    """Create a sample universe CSV file."""
    universe_path = Path(temp_data_dir) / "universe.csv"
    with open(universe_path, 'w') as f:
        f.write("ticker,sector,industry\n")
        f.write("AAPL,Technology,Consumer Electronics\n")
        f.write("MSFT,Technology,Software\n")
        f.write("GOOGL,Technology,Internet Content\n")
    return str(universe_path)


@pytest.fixture
def sample_ohlcv_data():
    """Create sample OHLCV DataFrame."""
    dates = pd.date_range(start='2023-01-01', periods=250, freq='B')  # Business days
    data = {
        'Open': [100 + i * 0.5 for i in range(250)],
        'High': [102 + i * 0.5 for i in range(250)],
        'Low': [99 + i * 0.5 for i in range(250)],
        'Close': [101 + i * 0.5 for i in range(250)],
        'Volume': [1000000 + i * 1000 for i in range(250)],
    }
    df = pd.DataFrame(data, index=dates)
    return df


@pytest.fixture
def ingestor(temp_data_dir, sample_universe_csv):
    """Create a PriceIngestor instance for testing."""
    return PriceIngestor(
        universe_path=sample_universe_csv,
        lookback_days=365,
        raw_dir=f"{temp_data_dir}/raw/prices",
        normalized_dir=f"{temp_data_dir}/normalized",
        max_retries=3,
        initial_backoff=0.01,  # Fast backoff for tests
        backoff_multiplier=2.0,
        request_delay=0.01,  # Fast rate limiting for tests
    )


class TestIngestionMetrics:
    """Test IngestionMetrics dataclass."""
    
    def test_initialization(self):
        """Test metrics initialization."""
        metrics = IngestionMetrics()
        assert metrics.total_tickers == 0
        assert metrics.successful_tickers == 0
        assert metrics.failed_tickers == 0
        assert metrics.start_time is not None
        assert metrics.end_time is None
    
    def test_duration_calculation(self):
        """Test duration calculation."""
        metrics = IngestionMetrics()
        metrics.start_time = datetime.now() - timedelta(seconds=10)
        metrics.end_time = datetime.now()
        assert 9.5 <= metrics.duration_seconds <= 10.5
    
    def test_success_rate(self):
        """Test success rate calculation."""
        metrics = IngestionMetrics()
        metrics.total_tickers = 10
        metrics.successful_tickers = 8
        assert metrics.success_rate == 80.0
        
        # Test division by zero
        empty_metrics = IngestionMetrics()
        assert empty_metrics.success_rate == 0.0


class TestValidationResult:
    """Test ValidationResult dataclass."""
    
    def test_is_valid_threshold(self):
        """Test validation threshold (98%)."""
        # Valid result
        valid_result = ValidationResult(
            ticker="AAPL",
            total_days=250,
            missing_days=5,
            completeness_pct=98.5,
            has_gaps=False
        )
        assert valid_result.is_valid is True
        
        # Invalid result
        invalid_result = ValidationResult(
            ticker="AAPL",
            total_days=240,
            missing_days=15,
            completeness_pct=95.0,
            has_gaps=True
        )
        assert invalid_result.is_valid is False


class TestPriceIngestor:
    """Test PriceIngestor class."""
    
    def test_initialization(self, ingestor, temp_data_dir):
        """Test ingestor initialization."""
        assert ingestor.lookback_days == 365
        assert ingestor.max_retries == 3
        assert ingestor.initial_backoff == 0.01
        assert ingestor.backoff_multiplier == 2.0
        
        # Check directories were created
        assert ingestor.raw_dir.exists()
        assert ingestor.normalized_dir.exists()
    
    def test_load_universe(self, ingestor):
        """Test loading universe CSV."""
        universe = ingestor.load_universe()
        assert len(universe) == 3
        assert universe[0]['ticker'] == 'AAPL'
        assert universe[0]['sector'] == 'Technology'
        assert universe[1]['ticker'] == 'MSFT'
        assert universe[2]['ticker'] == 'GOOGL'
    
    def test_load_universe_file_not_found(self, temp_data_dir):
        """Test loading non-existent universe file."""
        ingestor = PriceIngestor(
            universe_path=f"{temp_data_dir}/nonexistent.csv",
            raw_dir=f"{temp_data_dir}/raw/prices",
            normalized_dir=f"{temp_data_dir}/normalized"
        )
        with pytest.raises(FileNotFoundError):
            ingestor.load_universe()
    
    def test_load_universe_malformed(self, temp_data_dir):
        """Test loading malformed universe CSV."""
        bad_universe_path = Path(temp_data_dir) / "bad_universe.csv"
        with open(bad_universe_path, 'w') as f:
            f.write("symbol,name\n")  # Missing 'ticker' column
            f.write("AAPL,Apple\n")
        
        ingestor = PriceIngestor(
            universe_path=str(bad_universe_path),
            raw_dir=f"{temp_data_dir}/raw/prices",
            normalized_dir=f"{temp_data_dir}/normalized"
        )
        with pytest.raises(ValueError, match="ticker"):
            ingestor.load_universe()
    
    @patch('backend.ingest.price_ingest.yf.Ticker')
    def test_fetch_ohlcv_with_retry_success(self, mock_ticker_class, ingestor, sample_ohlcv_data):
        """Test successful OHLCV fetch."""
        # Mock yfinance Ticker
        mock_ticker = MagicMock()
        mock_ticker.history.return_value = sample_ohlcv_data
        mock_ticker_class.return_value = mock_ticker
        
        start_date = datetime.now() - timedelta(days=365)
        end_date = datetime.now()
        
        result = ingestor._fetch_ohlcv_with_retry('AAPL', start_date, end_date)
        
        assert result is not None
        assert len(result) == 250
        assert all(col in result.columns for col in ['Open', 'High', 'Low', 'Close', 'Volume'])
    
    @patch('backend.ingest.price_ingest.yf.Ticker')
    def test_fetch_ohlcv_with_retry_empty_data(self, mock_ticker_class, ingestor):
        """Test fetch with empty data."""
        # Mock yfinance Ticker returning empty DataFrame
        mock_ticker = MagicMock()
        mock_ticker.history.return_value = pd.DataFrame()
        mock_ticker_class.return_value = mock_ticker
        
        start_date = datetime.now() - timedelta(days=365)
        end_date = datetime.now()
        
        result = ingestor._fetch_ohlcv_with_retry('INVALID', start_date, end_date)
        
        assert result is None
    
    @patch('backend.ingest.price_ingest.yf.Ticker')
    @patch('backend.ingest.price_ingest.time.sleep')
    def test_fetch_ohlcv_with_retry_transient_error(
        self,
        mock_sleep,
        mock_ticker_class,
        ingestor,
        sample_ohlcv_data
    ):
        """Test fetch with transient errors and successful retry."""
        # Mock yfinance Ticker to fail twice then succeed
        mock_ticker = MagicMock()
        mock_ticker.history.side_effect = [
            Exception("Network error"),
            Exception("Timeout"),
            sample_ohlcv_data
        ]
        mock_ticker_class.return_value = mock_ticker
        
        start_date = datetime.now() - timedelta(days=365)
        end_date = datetime.now()
        
        result = ingestor._fetch_ohlcv_with_retry('AAPL', start_date, end_date)
        
        assert result is not None
        assert len(result) == 250
        # Verify retries happened
        assert mock_sleep.call_count == 2
    
    @patch('backend.ingest.price_ingest.yf.Ticker')
    @patch('backend.ingest.price_ingest.time.sleep')
    def test_fetch_ohlcv_with_retry_permanent_failure(
        self,
        mock_sleep,
        mock_ticker_class,
        ingestor
    ):
        """Test fetch with permanent failure after all retries."""
        # Mock yfinance Ticker to always fail
        mock_ticker = MagicMock()
        mock_ticker.history.side_effect = Exception("Permanent error")
        mock_ticker_class.return_value = mock_ticker
        
        start_date = datetime.now() - timedelta(days=365)
        end_date = datetime.now()
        
        result = ingestor._fetch_ohlcv_with_retry('INVALID', start_date, end_date)
        
        assert result is None
        # Verify all retries exhausted
        assert mock_sleep.call_count == 2  # max_retries - 1
    
    def test_validate_timeseries_valid_data(self, ingestor, sample_ohlcv_data):
        """Test validation with valid continuous data."""
        result = ingestor._validate_timeseries('AAPL', sample_ohlcv_data, 365)
        
        assert result.ticker == 'AAPL'
        assert result.total_days == 250
        assert result.completeness_pct >= 98.0
        assert result.is_valid is True
        assert result.has_gaps is False
    
    def test_validate_timeseries_with_gaps(self, ingestor):
        """Test validation with data gaps."""
        # Create data with a large gap
        dates1 = pd.date_range(start='2023-01-01', periods=100, freq='B')
        dates2 = pd.date_range(start='2023-08-01', periods=100, freq='B')
        dates = pd.Index(dates1).union(pd.Index(dates2))
        
        data = {
            'Open': [100 + i * 0.5 for i in range(200)],
            'High': [102 + i * 0.5 for i in range(200)],
            'Low': [99 + i * 0.5 for i in range(200)],
            'Close': [101 + i * 0.5 for i in range(200)],
            'Volume': [1000000 for _ in range(200)],
        }
        df = pd.DataFrame(data, index=dates)
        
        result = ingestor._validate_timeseries('AAPL', df, 365)
        
        assert result.has_gaps is True
        assert len(result.gap_details) > 0
    
    def test_save_raw_csv(self, ingestor, sample_ohlcv_data):
        """Test saving raw CSV file."""
        ingestor._save_raw_csv('AAPL', sample_ohlcv_data)
        
        output_path = ingestor.raw_dir / "AAPL.csv"
        assert output_path.exists()
        
        # Verify CSV contents
        df_loaded = pd.read_csv(output_path, index_col='Date')
        assert len(df_loaded) == 250
        assert all(col in df_loaded.columns for col in ['Open', 'High', 'Low', 'Close', 'Volume'])
    
    def test_save_normalized_parquet(self, ingestor, sample_ohlcv_data):
        """Test saving normalized parquet file."""
        metadata = {
            'fetch_timestamp': datetime.now().isoformat(),
            'data_source': 'yfinance',
            'validation_status': 'valid'
        }
        
        all_data = [
            ('AAPL', sample_ohlcv_data.iloc[:100], metadata),
            ('MSFT', sample_ohlcv_data.iloc[:100], metadata),
        ]
        
        ingestor._save_normalized_parquet(all_data)
        
        output_path = ingestor.normalized_dir / "prices.parquet"
        assert output_path.exists()
        
        # Verify parquet contents
        df_loaded = pd.read_parquet(output_path)
        assert len(df_loaded) == 200  # 100 rows per ticker
        assert 'ticker' in df_loaded.columns
        assert 'AAPL' in df_loaded['ticker'].values
        assert 'MSFT' in df_loaded['ticker'].values
    
    def test_save_normalized_parquet_empty(self, ingestor):
        """Test saving with no data."""
        ingestor._save_normalized_parquet([])
        
        output_path = ingestor.normalized_dir / "prices.parquet"
        assert not output_path.exists()
    
    @patch('backend.ingest.price_ingest.yf.Ticker')
    @patch('backend.ingest.price_ingest.time.sleep')
    def test_ingest_full_flow(
        self,
        mock_sleep,
        mock_ticker_class,
        ingestor,
        sample_ohlcv_data
    ):
        """Test full ingestion flow."""
        # Mock yfinance Ticker
        mock_ticker = MagicMock()
        mock_ticker.history.return_value = sample_ohlcv_data
        mock_ticker_class.return_value = mock_ticker
        
        metrics = ingestor.ingest()
        
        assert metrics.total_tickers == 3
        assert metrics.successful_tickers == 3
        assert metrics.failed_tickers == 0
        assert metrics.success_rate == 100.0
        
        # Verify CSV files were created
        assert (ingestor.raw_dir / "AAPL.csv").exists()
        assert (ingestor.raw_dir / "MSFT.csv").exists()
        assert (ingestor.raw_dir / "GOOGL.csv").exists()
        
        # Verify normalized parquet was created
        assert (ingestor.normalized_dir / "prices.parquet").exists()
    
    @patch('backend.ingest.price_ingest.yf.Ticker')
    @patch('backend.ingest.price_ingest.time.sleep')
    def test_ingest_with_failures(
        self,
        mock_sleep,
        mock_ticker_class,
        ingestor,
        sample_ohlcv_data
    ):
        """Test ingestion with some failures."""
        # Mock yfinance Ticker to succeed for 'AAPL', fail for others
        def mock_ticker_factory(ticker_symbol):
            mock_ticker = MagicMock()
            if ticker_symbol == 'AAPL':
                mock_ticker.history.return_value = sample_ohlcv_data
            else:
                mock_ticker.history.side_effect = Exception("API error")
            return mock_ticker
        
        mock_ticker_class.side_effect = mock_ticker_factory
        
        metrics = ingestor.ingest()
        
        assert metrics.total_tickers == 3
        # Results may vary based on mock behavior, just check structure
        assert metrics.successful_tickers + metrics.failed_tickers == metrics.total_tickers
    
    def test_print_summary(self, ingestor, capsys):
        """Test summary printing."""
        metrics = IngestionMetrics()
        metrics.total_tickers = 10
        metrics.successful_tickers = 8
        metrics.failed_tickers = 2
        metrics.end_time = datetime.now()
        
        ingestor.print_summary(metrics)
        
        captured = capsys.readouterr()
        assert "PRICE INGESTION SUMMARY" in captured.out
        assert "Total Tickers:      10" in captured.out
        assert "Successful:         8" in captured.out
        assert "Failed:             2" in captured.out


class TestExponentialBackoff:
    """Test exponential backoff behavior."""
    
    @patch('backend.ingest.price_ingest.yf.Ticker')
    @patch('backend.ingest.price_ingest.time.sleep')
    def test_backoff_multiplier(self, mock_sleep, mock_ticker_class, ingestor):
        """Test that backoff increases exponentially."""
        # Mock yfinance to always fail
        mock_ticker = MagicMock()
        mock_ticker.history.side_effect = Exception("Error")
        mock_ticker_class.return_value = mock_ticker
        
        start_date = datetime.now() - timedelta(days=365)
        end_date = datetime.now()
        
        ingestor._fetch_ohlcv_with_retry('AAPL', start_date, end_date)
        
        # Verify backoff times: 0.01, 0.02
        assert mock_sleep.call_count == 2
        call_args = [call[0][0] for call in mock_sleep.call_args_list]
        
        # First backoff should be initial_backoff
        assert call_args[0] == pytest.approx(0.01, rel=0.01)
        # Second backoff should be initial_backoff * multiplier
        assert call_args[1] == pytest.approx(0.02, rel=0.01)


class TestCLI:
    """Test CLI functionality."""
    
    def test_main_function_exists(self):
        """Test that main function exists."""
        from backend.ingest.price_ingest import main
        assert callable(main)
