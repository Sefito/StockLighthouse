"""
Unit tests for fundamentals_ingest.py module.

Tests the FundamentalsIngestor class with mocked network calls to avoid
external dependencies.
"""

import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime
from pathlib import Path
import pandas as pd
import tempfile
import shutil
import json

from backend.ingest.fundamentals_ingest import (
    FundamentalsIngestor,
    FundamentalsMetrics,
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
    return str(universe_path)


@pytest.fixture
def sample_quarterly_financials():
    """Create sample quarterly financials DataFrame."""
    dates = [
        pd.Timestamp('2023-12-31'),
        pd.Timestamp('2023-09-30'),
        pd.Timestamp('2023-06-30'),
        pd.Timestamp('2023-03-31'),
    ]
    data = {
        dates[0]: [100000000, 20000000, 15000000],
        dates[1]: [95000000, 18000000, 14000000],
        dates[2]: [90000000, 17000000, 13000000],
        dates[3]: [85000000, 16000000, 12000000],
    }
    index = ['Total Revenue', 'Operating Income', 'Net Income']
    return pd.DataFrame(data, index=index)


@pytest.fixture
def sample_quarterly_balance_sheet():
    """Create sample quarterly balance sheet DataFrame."""
    dates = [
        pd.Timestamp('2023-12-31'),
        pd.Timestamp('2023-09-30'),
        pd.Timestamp('2023-06-30'),
        pd.Timestamp('2023-03-31'),
    ]
    data = {
        dates[0]: [500000000, 100000000],
        dates[1]: [480000000, 95000000],
        dates[2]: [460000000, 90000000],
        dates[3]: [440000000, 85000000],
    }
    index = ['Total Assets', 'Total Debt']
    return pd.DataFrame(data, index=index)


@pytest.fixture
def sample_quarterly_cashflow():
    """Create sample quarterly cash flow DataFrame."""
    dates = [
        pd.Timestamp('2023-12-31'),
        pd.Timestamp('2023-09-30'),
        pd.Timestamp('2023-06-30'),
        pd.Timestamp('2023-03-31'),
    ]
    data = {
        dates[0]: [25000000],
        dates[1]: [23000000],
        dates[2]: [21000000],
        dates[3]: [19000000],
    }
    index = ['Free Cash Flow']
    return pd.DataFrame(data, index=index)


@pytest.fixture
def ingestor(temp_data_dir, sample_universe_csv):
    """Create a FundamentalsIngestor instance for testing."""
    return FundamentalsIngestor(
        universe_path=sample_universe_csv,
        raw_dir=f"{temp_data_dir}/raw/fundamentals",
        normalized_dir=f"{temp_data_dir}/normalized",
        max_retries=3,
        initial_backoff=0.01,  # Fast backoff for tests
        backoff_multiplier=2.0,
        request_delay=0.01,  # Fast rate limiting for tests
    )


class TestFundamentalsMetrics:
    """Test FundamentalsMetrics dataclass."""
    
    def test_initialization(self):
        """Test metrics initialization."""
        metrics = FundamentalsMetrics()
        assert metrics.total_tickers == 0
        assert metrics.successful_tickers == 0
        assert metrics.failed_tickers == 0
        assert metrics.total_quarters == 0
        assert metrics.start_time is not None
        assert metrics.end_time is None
    
    def test_success_rate(self):
        """Test success rate calculation."""
        metrics = FundamentalsMetrics()
        metrics.total_tickers = 10
        metrics.successful_tickers = 7
        assert metrics.success_rate == 70.0
        
        # Test division by zero
        empty_metrics = FundamentalsMetrics()
        assert empty_metrics.success_rate == 0.0


class TestFundamentalsIngestor:
    """Test FundamentalsIngestor class."""
    
    def test_initialization(self, ingestor, temp_data_dir):
        """Test ingestor initialization."""
        assert ingestor.max_retries == 3
        assert ingestor.initial_backoff == 0.01
        assert ingestor.backoff_multiplier == 2.0
        
        # Check directories were created
        assert ingestor.raw_dir.exists()
        assert ingestor.normalized_dir.exists()
    
    def test_load_universe(self, ingestor):
        """Test loading universe CSV."""
        universe = ingestor.load_universe()
        assert len(universe) == 2
        assert universe[0]['ticker'] == 'AAPL'
        assert universe[0]['sector'] == 'Technology'
        assert universe[1]['ticker'] == 'MSFT'
    
    def test_load_universe_file_not_found(self, temp_data_dir):
        """Test loading non-existent universe file."""
        ingestor = FundamentalsIngestor(
            universe_path=f"{temp_data_dir}/nonexistent.csv",
            raw_dir=f"{temp_data_dir}/raw/fundamentals",
            normalized_dir=f"{temp_data_dir}/normalized"
        )
        with pytest.raises(FileNotFoundError):
            ingestor.load_universe()
    
    def test_safe_get_value(self, ingestor, sample_quarterly_financials):
        """Test safe value extraction from DataFrame."""
        # Valid value
        value = ingestor._safe_get_value(
            sample_quarterly_financials,
            'Total Revenue',
            pd.Timestamp('2023-12-31')
        )
        assert value == 100000000
        
        # Non-existent row
        value = ingestor._safe_get_value(
            sample_quarterly_financials,
            'Non Existent',
            pd.Timestamp('2023-12-31')
        )
        assert value is None
        
        # Non-existent column
        value = ingestor._safe_get_value(
            sample_quarterly_financials,
            'Total Revenue',
            pd.Timestamp('2020-12-31')
        )
        assert value is None
    
    def test_extract_metrics(
        self,
        ingestor,
        sample_quarterly_financials,
        sample_quarterly_balance_sheet,
        sample_quarterly_cashflow
    ):
        """Test metrics extraction from financial statements."""
        quarters_data = ingestor._extract_metrics(
            'AAPL',
            sample_quarterly_financials,
            sample_quarterly_balance_sheet,
            sample_quarterly_cashflow
        )
        
        assert len(quarters_data) == 4
        
        # Check first quarter (most recent)
        q1 = quarters_data[0]
        assert q1['ticker'] == 'AAPL'
        assert q1['period'] == 'Q4'
        assert q1['fiscal_year'] == 2023
        assert 'metrics' in q1
        
        # Check metrics content
        metrics = q1['metrics']
        assert 'revenue' in metrics
        assert 'net_income' in metrics
        assert 'operating_margin' in metrics
        assert 'total_assets' in metrics
        assert 'total_debt' in metrics
        assert 'free_cash_flow' in metrics
        
        # Check operating margin calculation
        assert metrics['operating_margin'] is not None
        expected_margin = 20000000 / 100000000  # Operating Income / Revenue
        assert metrics['operating_margin'] == pytest.approx(expected_margin)
    
    def test_extract_metrics_empty_dataframes(self, ingestor):
        """Test metrics extraction with empty DataFrames."""
        quarters_data = ingestor._extract_metrics(
            'INVALID',
            pd.DataFrame(),
            pd.DataFrame(),
            pd.DataFrame()
        )
        
        assert quarters_data == []
    
    def test_extract_metrics_partial_data(
        self,
        ingestor,
        sample_quarterly_financials
    ):
        """Test metrics extraction with partial data."""
        quarters_data = ingestor._extract_metrics(
            'AAPL',
            sample_quarterly_financials,
            pd.DataFrame(),  # No balance sheet
            pd.DataFrame()   # No cash flow
        )
        
        assert len(quarters_data) == 4
        
        # Check that we still got income statement data
        q1 = quarters_data[0]
        assert 'revenue' in q1['metrics']
        assert 'net_income' in q1['metrics']
        
        # Balance sheet and cash flow metrics should be missing
        assert q1['metrics'].get('total_assets') is None
        assert q1['metrics'].get('free_cash_flow') is None
    
    @patch('backend.ingest.fundamentals_ingest.yf.Ticker')
    def test_fetch_fundamentals_with_retry_success(
        self,
        mock_ticker_class,
        ingestor,
        sample_quarterly_financials,
        sample_quarterly_balance_sheet,
        sample_quarterly_cashflow
    ):
        """Test successful fundamentals fetch."""
        # Mock yfinance Ticker
        mock_ticker = MagicMock()
        mock_ticker.quarterly_financials = sample_quarterly_financials
        mock_ticker.quarterly_balance_sheet = sample_quarterly_balance_sheet
        mock_ticker.quarterly_cashflow = sample_quarterly_cashflow
        mock_ticker_class.return_value = mock_ticker
        
        result = ingestor._fetch_fundamentals_with_retry('AAPL')
        
        assert result is not None
        assert len(result) == 4
        assert result[0]['ticker'] == 'AAPL'
    
    @patch('backend.ingest.fundamentals_ingest.yf.Ticker')
    def test_fetch_fundamentals_with_retry_no_data(self, mock_ticker_class, ingestor):
        """Test fetch with no data available."""
        # Mock yfinance Ticker returning None/empty DataFrames
        mock_ticker = MagicMock()
        mock_ticker.quarterly_financials = None
        mock_ticker.quarterly_balance_sheet = None
        mock_ticker.quarterly_cashflow = None
        mock_ticker_class.return_value = mock_ticker
        
        result = ingestor._fetch_fundamentals_with_retry('INVALID')
        
        assert result is None
    
    @patch('backend.ingest.fundamentals_ingest.yf.Ticker')
    @patch('backend.ingest.fundamentals_ingest.time.sleep')
    def test_fetch_fundamentals_with_retry_transient_error(
        self,
        mock_sleep,
        mock_ticker_class,
        ingestor,
        sample_quarterly_financials,
        sample_quarterly_balance_sheet,
        sample_quarterly_cashflow
    ):
        """Test fetch with transient errors and successful retry."""
        # Mock yfinance Ticker to fail once then succeed
        mock_ticker = MagicMock()
        
        # First call raises exception, second succeeds
        call_count = [0]
        def get_financials():
            call_count[0] += 1
            if call_count[0] == 1:
                raise Exception("Network error")
            return sample_quarterly_financials
        
        mock_ticker.quarterly_financials = property(lambda self: get_financials())
        mock_ticker.quarterly_balance_sheet = sample_quarterly_balance_sheet
        mock_ticker.quarterly_cashflow = sample_quarterly_cashflow
        mock_ticker_class.return_value = mock_ticker
        
        result = ingestor._fetch_fundamentals_with_retry('AAPL')
        
        # Should eventually succeed after retry
        assert mock_sleep.call_count >= 1
    
    @patch('backend.ingest.fundamentals_ingest.yf.Ticker')
    @patch('backend.ingest.fundamentals_ingest.time.sleep')
    def test_fetch_fundamentals_with_retry_permanent_failure(
        self,
        mock_sleep,
        mock_ticker_class,
        ingestor
    ):
        """Test fetch with permanent failure after all retries."""
        # Mock yfinance Ticker to always fail
        mock_ticker = MagicMock()
        mock_ticker.quarterly_financials = MagicMock(side_effect=Exception("Error"))
        mock_ticker_class.return_value = mock_ticker
        
        result = ingestor._fetch_fundamentals_with_retry('INVALID')
        
        assert result is None
        assert mock_sleep.call_count == 2  # max_retries - 1
    
    def test_save_normalized_parquet(self, ingestor):
        """Test saving normalized parquet file."""
        all_data = [
            {
                'ticker': 'AAPL',
                'report_date': '2023-12-31',
                'period': 'Q4',
                'fiscal_year': 2023,
                'metrics': {
                    'revenue': 100000000,
                    'net_income': 20000000,
                    'total_assets': 500000000,
                },
                'fetch_timestamp': datetime.now().isoformat(),
                'data_source': 'yfinance',
            },
            {
                'ticker': 'MSFT',
                'report_date': '2023-12-31',
                'period': 'Q4',
                'fiscal_year': 2023,
                'metrics': {
                    'revenue': 150000000,
                    'net_income': 30000000,
                },
                'fetch_timestamp': datetime.now().isoformat(),
                'data_source': 'yfinance',
            }
        ]
        
        ingestor._save_normalized_parquet(all_data)
        
        output_path = ingestor.normalized_dir / "fundamentals.parquet"
        assert output_path.exists()
        
        # Verify parquet contents
        df_loaded = pd.read_parquet(output_path)
        assert len(df_loaded) == 2
        assert 'ticker' in df_loaded.columns
        assert 'AAPL' in df_loaded['ticker'].values
        assert 'MSFT' in df_loaded['ticker'].values
        assert 'revenue' in df_loaded.columns
        assert 'metrics_json' in df_loaded.columns
    
    def test_save_normalized_parquet_empty(self, ingestor):
        """Test saving with no data."""
        ingestor._save_normalized_parquet([])
        
        output_path = ingestor.normalized_dir / "fundamentals.parquet"
        assert not output_path.exists()
    
    @patch('backend.ingest.fundamentals_ingest.yf.Ticker')
    @patch('backend.ingest.fundamentals_ingest.time.sleep')
    def test_ingest_full_flow(
        self,
        mock_sleep,
        mock_ticker_class,
        ingestor,
        sample_quarterly_financials,
        sample_quarterly_balance_sheet,
        sample_quarterly_cashflow
    ):
        """Test full ingestion flow."""
        # Mock yfinance Ticker
        mock_ticker = MagicMock()
        mock_ticker.quarterly_financials = sample_quarterly_financials
        mock_ticker.quarterly_balance_sheet = sample_quarterly_balance_sheet
        mock_ticker.quarterly_cashflow = sample_quarterly_cashflow
        mock_ticker_class.return_value = mock_ticker
        
        metrics = ingestor.ingest()
        
        assert metrics.total_tickers == 2
        assert metrics.successful_tickers == 2
        assert metrics.failed_tickers == 0
        assert metrics.total_quarters == 8  # 4 quarters * 2 tickers
        assert metrics.success_rate == 100.0
        
        # Verify normalized parquet was created
        assert (ingestor.normalized_dir / "fundamentals.parquet").exists()
    
    @patch('backend.ingest.fundamentals_ingest.yf.Ticker')
    @patch('backend.ingest.fundamentals_ingest.time.sleep')
    def test_ingest_with_failures(
        self,
        mock_sleep,
        mock_ticker_class,
        ingestor,
        sample_quarterly_financials
    ):
        """Test ingestion with some failures."""
        # First ticker succeeds, second fails
        call_count = [0]
        
        def get_ticker(*args, **kwargs):
            call_count[0] += 1
            mock_ticker = MagicMock()
            if call_count[0] == 1:
                # First ticker (AAPL) succeeds
                mock_ticker.quarterly_financials = sample_quarterly_financials
                mock_ticker.quarterly_balance_sheet = pd.DataFrame()
                mock_ticker.quarterly_cashflow = pd.DataFrame()
            else:
                # Second ticker (MSFT) fails
                mock_ticker.quarterly_financials = None
                mock_ticker.quarterly_balance_sheet = None
                mock_ticker.quarterly_cashflow = None
            return mock_ticker
        
        mock_ticker_class.side_effect = get_ticker
        
        metrics = ingestor.ingest()
        
        assert metrics.total_tickers == 2
        assert metrics.successful_tickers == 1
        assert metrics.failed_tickers == 1
        assert metrics.total_quarters == 4
    
    def test_print_summary(self, ingestor, capsys):
        """Test summary printing."""
        metrics = FundamentalsMetrics()
        metrics.total_tickers = 10
        metrics.successful_tickers = 8
        metrics.failed_tickers = 2
        metrics.total_quarters = 32
        metrics.end_time = datetime.now()
        
        ingestor.print_summary(metrics)
        
        captured = capsys.readouterr()
        assert "FUNDAMENTALS INGESTION SUMMARY" in captured.out
        assert "Total Tickers:      10" in captured.out
        assert "Successful:         8" in captured.out
        assert "Failed:             2" in captured.out
        assert "Total Quarters:     32" in captured.out


class TestExponentialBackoff:
    """Test exponential backoff behavior."""
    
    @patch('backend.ingest.fundamentals_ingest.yf.Ticker')
    @patch('backend.ingest.fundamentals_ingest.time.sleep')
    def test_backoff_multiplier(self, mock_sleep, mock_ticker_class, ingestor):
        """Test that backoff increases exponentially."""
        # Mock yfinance to always fail
        mock_ticker = MagicMock()
        mock_ticker.quarterly_financials = MagicMock(side_effect=Exception("Error"))
        mock_ticker_class.return_value = mock_ticker
        
        ingestor._fetch_fundamentals_with_retry('AAPL')
        
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
        from backend.ingest.fundamentals_ingest import main
        assert callable(main)


class TestMetricsJSONSerialization:
    """Test that metrics can be serialized to JSON."""
    
    def test_metrics_json_serialization(self, ingestor):
        """Test that metrics dict can be serialized to JSON."""
        metrics = {
            'revenue': 100000000,
            'net_income': 20000000,
            'operating_margin': 0.15,
        }
        
        json_str = json.dumps(metrics)
        assert json_str is not None
        
        # Deserialize and verify
        loaded = json.loads(json_str)
        assert loaded['revenue'] == 100000000
        assert loaded['net_income'] == 20000000
        assert loaded['operating_margin'] == 0.15
