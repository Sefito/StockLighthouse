"""
Normalizer module for converting raw provider data to standardized KPIs.
"""
from typing import Dict, Any, Optional

from stocklighthouse.models import StockKPIs


def normalize(symbol: str, raw_data: Dict[str, Any]) -> StockKPIs:
    """
    Normalize raw provider data into standardized StockKPIs.
    
    Args:
        symbol: Stock symbol
        raw_data: Raw data from provider (e.g., yfinance info dict)
        
    Returns:
        StockKPIs with normalized data
    """
    # Extract price
    price = raw_data.get("regularMarketPrice") or raw_data.get("currentPrice")
    
    # Calculate change percentage
    change_pct: Optional[float] = None
    previous_close = raw_data.get("previousClose")
    if price is not None and previous_close is not None and previous_close > 0:
        change_pct = ((price - previous_close) / previous_close) * 100
    
    # Extract other KPIs
    market_cap = raw_data.get("marketCap")
    pe_ratio = raw_data.get("trailingPE")
    price_to_book = raw_data.get("priceToBook")
    dividend_yield = raw_data.get("dividendYield")
    sector = raw_data.get("sector")
    industry = raw_data.get("industry")
    
    return StockKPIs(
        symbol=symbol,
        price=price,
        change_pct=change_pct,
        market_cap=market_cap,
        pe_ratio=pe_ratio,
        price_to_book=price_to_book,
        dividend_yield=dividend_yield,
        sector=sector,
        industry=industry
    )
