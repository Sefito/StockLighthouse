"""
YFinance-based ingestor for StockLighthouse.

Features:
- Batch fetching for multiple symbols
- Exponential backoff with retries
- In-memory cache with TTL
- Raw provider payload return
- Minimal fast_info fallback for missing data
"""
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field

import yfinance as yf

from stocklighthouse.models import IngestorRequest, IngestorResponse, TickerData

logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """Cache entry with TTL."""
    data: Dict[str, Any]
    timestamp: datetime
    ttl_seconds: int = 300  # 5 minutes default
    
    def is_expired(self) -> bool:
        """Check if cache entry has expired."""
        return datetime.now() - self.timestamp > timedelta(seconds=self.ttl_seconds)


class YFinanceIngestor:
    """
    YFinance-based stock data ingestor with caching and retry logic.
    
    Features:
    - Batch fetching of multiple symbols
    - Exponential backoff with configurable retries
    - In-memory TTL cache to reduce API calls during development
    - Returns raw provider payloads
    - Provides fast_info fallback when full info is unavailable
    """
    
    def __init__(
        self,
        cache_ttl_seconds: int = 300,
        max_retries: int = 3,
        initial_backoff: float = 1.0,
        backoff_multiplier: float = 2.0,
    ):
        """
        Initialize the YFinance ingestor.
        
        Args:
            cache_ttl_seconds: Time-to-live for cached data in seconds
            max_retries: Maximum number of retry attempts
            initial_backoff: Initial backoff time in seconds
            backoff_multiplier: Multiplier for exponential backoff
        """
        self.cache_ttl_seconds = cache_ttl_seconds
        self.max_retries = max_retries
        self.initial_backoff = initial_backoff
        self.backoff_multiplier = backoff_multiplier
        self._cache: Dict[str, CacheEntry] = {}
        
    def clear_cache(self) -> None:
        """Clear all cached data."""
        self._cache.clear()
        
    def _get_from_cache(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get data from cache if available and not expired.
        
        Args:
            symbol: Stock symbol
            
        Returns:
            Cached data or None if not available or expired
        """
        if symbol in self._cache:
            entry = self._cache[symbol]
            if not entry.is_expired():
                logger.debug(f"Cache hit for {symbol}")
                return entry.data
            else:
                logger.debug(f"Cache expired for {symbol}")
                del self._cache[symbol]
        return None
        
    def _store_in_cache(self, symbol: str, data: Dict[str, Any]) -> None:
        """
        Store data in cache.
        
        Args:
            symbol: Stock symbol
            data: Data to cache
        """
        self._cache[symbol] = CacheEntry(
            data=data,
            timestamp=datetime.now(),
            ttl_seconds=self.cache_ttl_seconds
        )
        logger.debug(f"Cached data for {symbol}")
        
    def _fetch_ticker_with_retry(self, symbol: str) -> TickerData:
        """
        Fetch ticker data with exponential backoff retry logic.
        
        Args:
            symbol: Stock symbol to fetch
            
        Returns:
            TickerData with success status and data or error information
        """
        backoff = self.initial_backoff
        last_error = None
        
        for attempt in range(self.max_retries):
            try:
                ticker = yf.Ticker(symbol)
                
                # Try to get full info first
                try:
                    info = ticker.info
                    if info and len(info) > 0:
                        # Successful fetch with full info
                        raw_data = {
                            "symbol": symbol,
                            "info": info,
                            "source": "yfinance",
                            "fetch_time": datetime.now().isoformat(),
                        }
                        logger.info(f"Successfully fetched full info for {symbol}")
                        return TickerData(
                            symbol=symbol,
                            success=True,
                            raw_data=raw_data,
                            fast_info=None
                        )
                except Exception as info_error:
                    logger.warning(f"Failed to get full info for {symbol}: {info_error}")
                    # Fall back to fast_info
                    
                # Fallback to fast_info if full info fails
                try:
                    fast_info_data = {
                        "symbol": symbol,
                        "last_price": ticker.fast_info.get("lastPrice"),
                        "previous_close": ticker.fast_info.get("previousClose"),
                        "market_cap": ticker.fast_info.get("marketCap"),
                        "shares": ticker.fast_info.get("shares"),
                        "currency": ticker.fast_info.get("currency"),
                    }
                    
                    raw_data = {
                        "symbol": symbol,
                        "source": "yfinance_fast_info",
                        "fetch_time": datetime.now().isoformat(),
                    }
                    
                    logger.info(f"Using fast_info fallback for {symbol}")
                    return TickerData(
                        symbol=symbol,
                        success=True,
                        raw_data=raw_data,
                        fast_info=fast_info_data
                    )
                except Exception as fast_info_error:
                    last_error = f"Both info and fast_info failed: {fast_info_error}"
                    logger.warning(f"{last_error} for {symbol}")
                    
            except Exception as e:
                last_error = str(e)
                logger.warning(f"Attempt {attempt + 1}/{self.max_retries} failed for {symbol}: {e}")
                
                if attempt < self.max_retries - 1:
                    sleep_time = backoff
                    logger.info(f"Retrying {symbol} after {sleep_time:.2f}s backoff")
                    time.sleep(sleep_time)
                    backoff *= self.backoff_multiplier
        
        # All retries exhausted
        logger.error(f"Failed to fetch {symbol} after {self.max_retries} attempts: {last_error}")
        return TickerData(
            symbol=symbol,
            success=False,
            raw_data=None,
            fast_info=None,
            error=last_error or "Unknown error"
        )
        
    def fetch(self, request: IngestorRequest) -> IngestorResponse:
        """
        Fetch stock data for multiple symbols.
        
        Args:
            request: IngestorRequest with symbols and cache preference
            
        Returns:
            IngestorResponse with fetched data and statistics
        """
        tickers: List[TickerData] = []
        fetched_count = 0
        cached_count = 0
        failed_count = 0
        
        for symbol in request.symbols:
            symbol = symbol.upper().strip()
            
            # Check cache if enabled
            if request.use_cache:
                cached_data = self._get_from_cache(symbol)
                if cached_data:
                    tickers.append(TickerData(
                        symbol=symbol,
                        success=True,
                        raw_data=cached_data,
                        fast_info=None
                    ))
                    cached_count += 1
                    continue
            
            # Fetch from API
            ticker_data = self._fetch_ticker_with_retry(symbol)
            tickers.append(ticker_data)
            
            if ticker_data.success:
                fetched_count += 1
                # Cache the successful result
                if request.use_cache and ticker_data.raw_data:
                    self._store_in_cache(symbol, ticker_data.raw_data)
            else:
                failed_count += 1
                
        return IngestorResponse(
            tickers=tickers,
            fetched_count=fetched_count,
            cached_count=cached_count,
            failed_count=failed_count
        )
        
    def fetch_single(
        self,
        symbol: str,
        use_cache: bool = True
    ) -> TickerData:
        """
        Convenience method to fetch a single symbol.
        
        Args:
            symbol: Stock symbol to fetch
            use_cache: Whether to use cache
            
        Returns:
            TickerData for the symbol
        """
        request = IngestorRequest(symbols=[symbol], use_cache=use_cache)
        response = self.fetch(request)
        return response.tickers[0]
