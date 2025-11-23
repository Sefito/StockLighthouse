"""
Unit tests for YFinance ingestor.

Tests cover:
- Successful batch fetching
- Missing ticker info handling
- Partial data handling
- Cache functionality
- Retry logic with exponential backoff
"""
import time
from datetime import datetime, timedelta
from unittest.mock import Mock, MagicMock, patch

import pytest

from stocklighthouse.ingest.yfinance_ingestor import YFinanceIngestor, CacheEntry
from stocklighthouse.models import IngestorRequest, TickerData


class TestCacheEntry:
    """Tests for CacheEntry."""
    
    def test_cache_entry_not_expired(self):
        """Test that cache entry is not expired within TTL."""
        entry = CacheEntry(
            data={"test": "data"},
            timestamp=datetime.now(),
            ttl_seconds=300
        )
        assert not entry.is_expired()
        
    def test_cache_entry_expired(self):
        """Test that cache entry is expired after TTL."""
        entry = CacheEntry(
            data={"test": "data"},
            timestamp=datetime.now() - timedelta(seconds=301),
            ttl_seconds=300
        )
        assert entry.is_expired()


class TestYFinanceIngestor:
    """Tests for YFinanceIngestor."""
    
    def test_initialization(self):
        """Test ingestor initialization with custom parameters."""
        ingestor = YFinanceIngestor(
            cache_ttl_seconds=600,
            max_retries=5,
            initial_backoff=2.0,
            backoff_multiplier=3.0
        )
        assert ingestor.cache_ttl_seconds == 600
        assert ingestor.max_retries == 5
        assert ingestor.initial_backoff == 2.0
        assert ingestor.backoff_multiplier == 3.0
        assert len(ingestor._cache) == 0
        
    def test_clear_cache(self):
        """Test cache clearing."""
        ingestor = YFinanceIngestor()
        ingestor._cache["TEST"] = CacheEntry(
            data={"test": "data"},
            timestamp=datetime.now()
        )
        assert len(ingestor._cache) == 1
        ingestor.clear_cache()
        assert len(ingestor._cache) == 0
        
    def test_get_from_cache_hit(self):
        """Test successful cache retrieval."""
        ingestor = YFinanceIngestor()
        test_data = {"symbol": "AAPL", "price": 150.0}
        ingestor._cache["AAPL"] = CacheEntry(
            data=test_data,
            timestamp=datetime.now(),
            ttl_seconds=300
        )
        cached = ingestor._get_from_cache("AAPL")
        assert cached == test_data
        
    def test_get_from_cache_miss(self):
        """Test cache miss."""
        ingestor = YFinanceIngestor()
        cached = ingestor._get_from_cache("AAPL")
        assert cached is None
        
    def test_get_from_cache_expired(self):
        """Test expired cache entry is removed."""
        ingestor = YFinanceIngestor()
        test_data = {"symbol": "AAPL", "price": 150.0}
        ingestor._cache["AAPL"] = CacheEntry(
            data=test_data,
            timestamp=datetime.now() - timedelta(seconds=301),
            ttl_seconds=300
        )
        cached = ingestor._get_from_cache("AAPL")
        assert cached is None
        assert "AAPL" not in ingestor._cache
        
    def test_store_in_cache(self):
        """Test storing data in cache."""
        ingestor = YFinanceIngestor()
        test_data = {"symbol": "AAPL", "price": 150.0}
        ingestor._store_in_cache("AAPL", test_data)
        assert "AAPL" in ingestor._cache
        assert ingestor._cache["AAPL"].data == test_data
        
    @patch('stocklighthouse.ingest.yfinance_ingestor.yf.Ticker')
    def test_fetch_ticker_success_with_full_info(self, mock_ticker_class):
        """Test successful fetch with full info."""
        # Mock ticker with full info
        mock_ticker = Mock()
        mock_ticker.info = {
            "regularMarketPrice": 150.0,
            "previousClose": 148.0,
            "marketCap": 2000000000000,
            "sector": "Technology"
        }
        mock_ticker_class.return_value = mock_ticker
        
        ingestor = YFinanceIngestor(max_retries=1)
        result = ingestor._fetch_ticker_with_retry("AAPL")
        
        assert result.symbol == "AAPL"
        assert result.success is True
        assert result.raw_data is not None
        assert result.raw_data["symbol"] == "AAPL"
        assert "info" in result.raw_data
        assert result.error is None
        
    @patch('stocklighthouse.ingest.yfinance_ingestor.yf.Ticker')
    def test_fetch_ticker_fallback_to_fast_info(self, mock_ticker_class):
        """Test fallback to fast_info when full info fails."""
        # Mock ticker with failing info but working fast_info
        mock_ticker = Mock()
        mock_ticker.info = Mock(side_effect=Exception("Info not available"))
        
        # Mock fast_info
        mock_fast_info = Mock()
        mock_fast_info.get = Mock(side_effect=lambda key: {
            "lastPrice": 150.0,
            "previousClose": 148.0,
            "marketCap": 2000000000000,
        }.get(key))
        mock_ticker.fast_info = mock_fast_info
        
        mock_ticker_class.return_value = mock_ticker
        
        ingestor = YFinanceIngestor(max_retries=1)
        result = ingestor._fetch_ticker_with_retry("AAPL")
        
        assert result.symbol == "AAPL"
        assert result.success is True
        assert result.fast_info is not None
        assert result.fast_info["last_price"] == 150.0
        assert result.error is None
        
    @patch('stocklighthouse.ingest.yfinance_ingestor.yf.Ticker')
    def test_fetch_ticker_missing_info(self, mock_ticker_class):
        """Test handling when ticker info is completely missing."""
        # Mock ticker with empty info
        mock_ticker = Mock()
        mock_ticker.info = {}
        mock_ticker.fast_info = Mock()
        mock_ticker.fast_info.get = Mock(side_effect=Exception("No data"))
        mock_ticker_class.return_value = mock_ticker
        
        ingestor = YFinanceIngestor(max_retries=1)
        result = ingestor._fetch_ticker_with_retry("INVALID")
        
        assert result.symbol == "INVALID"
        assert result.success is False
        assert result.error is not None
        
    @patch('stocklighthouse.ingest.yfinance_ingestor.yf.Ticker')
    @patch('stocklighthouse.ingest.yfinance_ingestor.time.sleep')
    def test_fetch_ticker_with_retry(self, mock_sleep, mock_ticker_class):
        """Test retry logic with exponential backoff for Ticker creation failures."""
        # Mock Ticker creation that fails twice then succeeds
        call_count = [0]
        
        def create_ticker_with_retries(symbol):
            call_count[0] += 1
            if call_count[0] < 3:
                raise Exception("Network error - temporary failure")
            
            # Third attempt succeeds
            mock_ticker = Mock()
            mock_ticker.info = {
                "regularMarketPrice": 150.0,
                "sector": "Technology"
            }
            return mock_ticker
        
        mock_ticker_class.side_effect = create_ticker_with_retries
        
        ingestor = YFinanceIngestor(
            max_retries=3,
            initial_backoff=0.1,
            backoff_multiplier=2.0
        )
        result = ingestor._fetch_ticker_with_retry("AAPL")
        
        assert result.success is True
        assert mock_sleep.call_count == 2  # Two retries before success
        # Verify exponential backoff: first sleep ~0.1s, second sleep ~0.2s
        sleep_calls = [call.args[0] for call in mock_sleep.call_args_list]
        assert len(sleep_calls) == 2
        assert sleep_calls[0] == pytest.approx(0.1, rel=0.01)
        assert sleep_calls[1] == pytest.approx(0.2, rel=0.01)
        
    @patch('stocklighthouse.ingest.yfinance_ingestor.yf.Ticker')
    def test_fetch_ticker_all_retries_exhausted(self, mock_ticker_class):
        """Test failure when all retries are exhausted."""
        # Mock ticker that always fails
        mock_ticker = Mock()
        mock_ticker.info = Mock(side_effect=Exception("Persistent failure"))
        mock_ticker.fast_info = Mock()
        mock_ticker.fast_info.get = Mock(side_effect=Exception("No fast_info"))
        mock_ticker_class.return_value = mock_ticker
        
        ingestor = YFinanceIngestor(max_retries=2, initial_backoff=0.01)
        result = ingestor._fetch_ticker_with_retry("FAIL")
        
        assert result.success is False
        assert result.error is not None
        assert "fast_info failed" in result.error or "Persistent failure" in result.error
        
    @patch('stocklighthouse.ingest.yfinance_ingestor.yf.Ticker')
    def test_fetch_batch_success(self, mock_ticker_class):
        """Test batch fetching of multiple symbols."""
        # Mock ticker responses
        def create_mock_ticker(symbol):
            mock_ticker = Mock()
            mock_ticker.info = {
                "regularMarketPrice": 100.0 + ord(symbol[0]),
                "sector": "Technology"
            }
            return mock_ticker
        
        mock_ticker_class.side_effect = lambda symbol: create_mock_ticker(symbol)
        
        ingestor = YFinanceIngestor(max_retries=1)
        request = IngestorRequest(symbols=["AAPL", "GOOGL", "MSFT"], use_cache=False)
        response = ingestor.fetch(request)
        
        assert len(response.tickers) == 3
        assert response.fetched_count == 3
        assert response.cached_count == 0
        assert response.failed_count == 0
        assert all(t.success for t in response.tickers)
        
    @patch('stocklighthouse.ingest.yfinance_ingestor.yf.Ticker')
    def test_fetch_with_cache(self, mock_ticker_class):
        """Test that cache is used for subsequent requests."""
        # Mock ticker
        mock_ticker = Mock()
        mock_ticker.info = {
            "regularMarketPrice": 150.0,
            "sector": "Technology"
        }
        mock_ticker_class.return_value = mock_ticker
        
        ingestor = YFinanceIngestor(max_retries=1)
        
        # First request - should fetch
        request1 = IngestorRequest(symbols=["AAPL"], use_cache=True)
        response1 = ingestor.fetch(request1)
        assert response1.fetched_count == 1
        assert response1.cached_count == 0
        
        # Second request - should use cache
        request2 = IngestorRequest(symbols=["AAPL"], use_cache=True)
        response2 = ingestor.fetch(request2)
        assert response2.fetched_count == 0
        assert response2.cached_count == 1
        
        # Only one actual API call should have been made
        assert mock_ticker_class.call_count == 1
        
    @patch('stocklighthouse.ingest.yfinance_ingestor.yf.Ticker')
    def test_fetch_without_cache(self, mock_ticker_class):
        """Test that cache is bypassed when use_cache is False."""
        # Mock ticker
        mock_ticker = Mock()
        mock_ticker.info = {
            "regularMarketPrice": 150.0,
            "sector": "Technology"
        }
        mock_ticker_class.return_value = mock_ticker
        
        ingestor = YFinanceIngestor(max_retries=1)
        
        # First request with cache
        request1 = IngestorRequest(symbols=["AAPL"], use_cache=True)
        ingestor.fetch(request1)
        
        # Second request without cache
        request2 = IngestorRequest(symbols=["AAPL"], use_cache=False)
        response2 = ingestor.fetch(request2)
        
        assert response2.fetched_count == 1
        assert response2.cached_count == 0
        assert mock_ticker_class.call_count == 2  # Two API calls
        
    @patch('stocklighthouse.ingest.yfinance_ingestor.yf.Ticker')
    def test_fetch_partial_data(self, mock_ticker_class):
        """Test handling of partial data where some tickers succeed and some fail."""
        # Mock varying responses
        call_count = [0]
        
        def create_varying_ticker(symbol):
            call_count[0] += 1
            mock_ticker = Mock()
            
            if call_count[0] == 2:  # Second symbol fails
                mock_ticker.info = Mock(side_effect=Exception("Failed"))
                mock_ticker.fast_info = Mock()
                mock_ticker.fast_info.get = Mock(side_effect=Exception("No data"))
            else:
                mock_ticker.info = {
                    "regularMarketPrice": 100.0,
                    "sector": "Technology"
                }
            return mock_ticker
        
        mock_ticker_class.side_effect = create_varying_ticker
        
        ingestor = YFinanceIngestor(max_retries=1)
        request = IngestorRequest(symbols=["AAPL", "INVALID", "MSFT"], use_cache=False)
        response = ingestor.fetch(request)
        
        assert len(response.tickers) == 3
        assert response.fetched_count == 2
        assert response.failed_count == 1
        assert response.tickers[1].success is False
        assert response.tickers[1].error is not None
        
    @patch('stocklighthouse.ingest.yfinance_ingestor.yf.Ticker')
    def test_fetch_single_convenience_method(self, mock_ticker_class):
        """Test the fetch_single convenience method."""
        # Mock ticker
        mock_ticker = Mock()
        mock_ticker.info = {
            "regularMarketPrice": 150.0,
            "sector": "Technology"
        }
        mock_ticker_class.return_value = mock_ticker
        
        ingestor = YFinanceIngestor(max_retries=1)
        result = ingestor.fetch_single("AAPL", use_cache=False)
        
        assert isinstance(result, TickerData)
        assert result.symbol == "AAPL"
        assert result.success is True
        
    @patch('stocklighthouse.ingest.yfinance_ingestor.yf.Ticker')
    def test_fetch_normalizes_symbol_case(self, mock_ticker_class):
        """Test that symbols are normalized to uppercase."""
        mock_ticker = Mock()
        mock_ticker.info = {"regularMarketPrice": 150.0}
        mock_ticker_class.return_value = mock_ticker
        
        ingestor = YFinanceIngestor(max_retries=1)
        request = IngestorRequest(symbols=["aapl", " MSFT ", "googl"], use_cache=False)
        response = ingestor.fetch(request)
        
        symbols = [t.symbol for t in response.tickers]
        assert symbols == ["AAPL", "MSFT", "GOOGL"]
