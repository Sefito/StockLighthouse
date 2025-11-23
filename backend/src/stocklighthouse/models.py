"""
Data models for StockLighthouse.
Uses Pydantic for typed data validation.
"""
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class StockKPIs(BaseModel):
    """
    Normalized stock KPIs output model.
    
    This is the canonical schema for stock data across all providers.
    All fields except symbol are optional to handle incomplete data gracefully.
    
    Attributes:
        symbol: Stock ticker symbol (required)
        price: Current market price
        previous_close: Previous trading day's closing price
        change_pct: Percentage change from previous close
        market_cap: Total market capitalization
        pe_ratio: Price-to-earnings ratio (trailing)
        pb_ratio: Price-to-book ratio
        dividend_yield: Annual dividend yield as decimal (e.g., 0.02 for 2%)
        sector: Business sector (e.g., "Technology", "Healthcare")
        market: Market/region (e.g., "us_market", "uk_market")
        exchange: Stock exchange code (e.g., "NMS", "NYSE", "LSE")
        currency: Currency code (e.g., "USD", "EUR", "GBP")
        industry: Industry classification (e.g., "Consumer Electronics")
    """
    symbol: str
    price: Optional[float] = None
    previous_close: Optional[float] = None
    change_pct: Optional[float] = None
    market_cap: Optional[float] = None
    pe_ratio: Optional[float] = None
    pb_ratio: Optional[float] = None
    dividend_yield: Optional[float] = None
    sector: Optional[str] = None
    market: Optional[str] = None
    exchange: Optional[str] = None
    currency: Optional[str] = None
    industry: Optional[str] = None
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "symbol": "AAPL",
                    "price": 150.25,
                    "previous_close": 148.50,
                    "change_pct": 1.18,
                    "market_cap": 2400000000000,
                    "pe_ratio": 28.5,
                    "pb_ratio": 40.2,
                    "dividend_yield": 0.005,
                    "sector": "Technology",
                    "market": "us_market",
                    "exchange": "NMS",
                    "currency": "USD",
                    "industry": "Consumer Electronics"
                }
            ]
        }
    }


class IngestorRequest(BaseModel):
    """
    Request model for stock data ingestor.
    
    Specifies which symbols to fetch and whether to use cached data if available.
    Used with YFinanceIngestor and other ingestor implementations.
    
    Attributes:
        symbols: List of stock ticker symbols to fetch (e.g., ["AAPL", "MSFT"])
        use_cache: Whether to use cached data if available (default: True)
        
    Example:
        >>> request = IngestorRequest(symbols=["AAPL", "GOOGL"], use_cache=True)
        >>> request.symbols
        ['AAPL', 'GOOGL']
        
    Raises:
        ValidationError: If symbols list is empty or invalid
    """
    symbols: list[str] = Field(..., min_length=1, description="List of stock symbols to fetch")
    use_cache: bool = Field(default=True, description="Whether to use cached data if available")


class TickerData(BaseModel):
    """
    Individual ticker data response from ingestor.
    
    Contains the fetched data for a single stock symbol, including success status,
    raw data, fast_info fallback, and error information if applicable.
    
    Attributes:
        symbol: Stock ticker symbol (e.g., "AAPL")
        success: True if data was successfully fetched
        raw_data: Full raw data from provider (includes 'info' dict with all fields)
        fast_info: Minimal fallback data if full info unavailable
        error: Error message if fetch failed, None on success
        
    Example:
        >>> ticker = TickerData(
        ...     symbol="AAPL",
        ...     success=True,
        ...     raw_data={"info": {"regularMarketPrice": 150.0}},
        ...     error=None
        ... )
        >>> ticker.success
        True
    """
    symbol: str
    success: bool
    raw_data: Optional[Dict[str, Any]] = None
    fast_info: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class IngestorResponse(BaseModel):
    """
    Response model from ingestor containing all fetched ticker data.
    
    Aggregates results from fetching multiple symbols, providing both
    individual ticker data and summary statistics.
    
    Attributes:
        tickers: List of TickerData objects, one per requested symbol
        fetched_count: Number of symbols newly fetched from API
        cached_count: Number of symbols served from cache
        failed_count: Number of symbols that failed to fetch
        
    Example:
        >>> response = IngestorResponse(
        ...     tickers=[...],
        ...     fetched_count=2,
        ...     cached_count=1,
        ...     failed_count=0
        ... )
        >>> response.fetched_count + response.cached_count
        3
        
    Note:
        Total symbols = fetched_count + cached_count + failed_count
    """
    tickers: list[TickerData]
    fetched_count: int
    cached_count: int
    failed_count: int
