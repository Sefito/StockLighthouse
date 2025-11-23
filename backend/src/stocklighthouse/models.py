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
    """Request model for ingestor."""
    symbols: list[str] = Field(..., min_length=1, description="List of stock symbols to fetch")
    use_cache: bool = Field(default=True, description="Whether to use cached data if available")


class TickerData(BaseModel):
    """Individual ticker data response."""
    symbol: str
    success: bool
    raw_data: Optional[Dict[str, Any]] = None
    fast_info: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class IngestorResponse(BaseModel):
    """Response model from ingestor."""
    tickers: list[TickerData]
    fetched_count: int
    cached_count: int
    failed_count: int
