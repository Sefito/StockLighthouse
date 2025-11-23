"""
Data models for StockLighthouse.
Uses Pydantic for typed data validation.
"""
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class StockKPIs(BaseModel):
    """Normalized stock KPIs output model."""
    symbol: str
    price: Optional[float] = None
    change_pct: Optional[float] = None
    market_cap: Optional[float] = None
    pe_ratio: Optional[float] = None
    price_to_book: Optional[float] = None
    dividend_yield: Optional[float] = None
    sector: Optional[str] = None
    industry: Optional[str] = None


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
