"""
Normalizer module for converting raw provider data to standardized KPIs.

This module provides defensive parsing and unit conversions for yfinance data,
handling edge cases like missing fields, zero values, and null data gracefully.
"""
from typing import Dict, Any, Optional
import math
import logging

from stocklighthouse.models import StockKPIs

logger = logging.getLogger(__name__)

# Constants for data normalization
DIVIDEND_YIELD_PERCENTAGE_THRESHOLD = 0.01  # Values above this are assumed to be percentages


def _safe_float(value: Any) -> Optional[float]:
    """
    Safely convert a value to float, returning None on failure.
    
    Args:
        value: Value to convert (can be None, string, int, float, etc.)
        
    Returns:
        Float value or None if conversion fails or value is None
    """
    if value is None:
        return None
    
    try:
        result = float(value)
        # Check for NaN and infinity
        if math.isnan(result):
            return None
        if math.isinf(result):
            return None
        return result
    except (ValueError, TypeError):
        return None


def _safe_string(value: Any) -> Optional[str]:
    """
    Safely convert a value to string, returning None on failure.
    
    Args:
        value: Value to convert
        
    Returns:
        String value or None if conversion fails or value is None/empty
    """
    if value is None:
        return None
    
    try:
        result = str(value).strip()
        return result if result else None
    except (ValueError, TypeError):
        return None


def _infer_market(exchange: Optional[str]) -> Optional[str]:
    """
    Infer market region from exchange code.
    
    Args:
        exchange: Exchange code (e.g., "NMS", "NYSE", "LSE")
        
    Returns:
        Market region identifier (e.g., "us_market", "uk_market")
    """
    if not exchange:
        return None
    
    exchange_upper = exchange.upper()
    
    # US exchanges
    us_exchanges = {"NMS", "NYSE", "NYQ", "NASDAQ", "AMEX", "BATS"}
    if exchange_upper in us_exchanges:
        return "us_market"
    
    # UK exchanges
    if exchange_upper in {"LSE", "LON"}:
        return "uk_market"
    
    # European exchanges
    eu_exchanges = {"FRA", "PAR", "AMS", "SWX", "ETR"}
    if exchange_upper in eu_exchanges:
        return "eu_market"
    
    # Asian exchanges
    asian_exchanges = {"TYO", "HKG", "SHH", "SHZ", "KRX"}
    if exchange_upper in asian_exchanges:
        return "asian_market"
    
    # Default: return None for unknown exchanges
    return None


def normalize(symbol: str, raw_data: Dict[str, Any]) -> StockKPIs:
    """
    Normalize raw provider data into standardized StockKPIs.
    
    This function implements defensive parsing with multiple fallbacks:
    - Tries multiple field names for each KPI (e.g., regularMarketPrice, currentPrice)
    - Validates numeric values (no NaN, infinity, or negative values where inappropriate)
    - Handles missing data gracefully by returning None for optional fields
    - Calculates derived fields (e.g., change_pct from price and previous_close)
    - Performs unit conversions where needed
    
    Args:
        symbol: Stock symbol (required, will be uppercased and stripped)
        raw_data: Raw data from provider (e.g., yfinance info dict)
        
    Returns:
        StockKPIs with normalized data, all optional fields may be None
        
    Examples:
        >>> raw = {"regularMarketPrice": 100.0, "previousClose": 95.0, "sector": "Technology"}
        >>> kpis = normalize("AAPL", raw)
        >>> kpis.price
        100.0
        >>> kpis.change_pct
        5.263...
    """
    # Normalize symbol
    normalized_symbol = symbol.upper().strip()
    
    # Extract price - try multiple field names with defensive parsing
    price = _safe_float(raw_data.get("regularMarketPrice"))
    if price is None:
        price = _safe_float(raw_data.get("currentPrice"))
    if price is None:
        price = _safe_float(raw_data.get("price"))
    
    # Extract previous close
    previous_close = _safe_float(raw_data.get("previousClose"))
    
    # Calculate change percentage (only if we have both values and previous_close > 0)
    change_pct: Optional[float] = None
    if price is not None and previous_close is not None and previous_close > 0:
        try:
            change_pct = ((price - previous_close) / previous_close) * 100
        except (ZeroDivisionError, ArithmeticError):
            logger.warning(f"Failed to calculate change_pct for {normalized_symbol}")
            change_pct = None
    
    # Extract market cap - defensive float conversion
    market_cap = _safe_float(raw_data.get("marketCap"))
    
    # Extract PE ratio - try multiple field names
    pe_ratio = _safe_float(raw_data.get("trailingPE"))
    if pe_ratio is None:
        pe_ratio = _safe_float(raw_data.get("forwardPE"))
    
    # Extract PB ratio - renamed from price_to_book to pb_ratio in model
    pb_ratio = _safe_float(raw_data.get("priceToBook"))
    if pb_ratio is None:
        pb_ratio = _safe_float(raw_data.get("priceBookRatio"))
    
    # Extract dividend yield - ensure it's a decimal fraction
    # yfinance returns dividend yield as a percentage value (e.g., 0.38 means 0.38%)
    # We need to convert it to decimal (0.0038)
    dividend_yield = _safe_float(raw_data.get("dividendYield"))
    if dividend_yield is not None:
        # yfinance typically returns values like 0.38 for 0.38%, so divide by 100
        # However, some values might already be in decimal form (< 0.01)
        # Use a heuristic: if > DIVIDEND_YIELD_PERCENTAGE_THRESHOLD, assume it's a percentage
        if dividend_yield > DIVIDEND_YIELD_PERCENTAGE_THRESHOLD:
            dividend_yield = dividend_yield / 100.0
    
    # Extract string fields with defensive parsing
    sector = _safe_string(raw_data.get("sector"))
    industry = _safe_string(raw_data.get("industry"))
    exchange = _safe_string(raw_data.get("exchange"))
    currency = _safe_string(raw_data.get("currency"))
    
    # Infer market from exchange
    market = _infer_market(exchange)
    
    return StockKPIs(
        symbol=normalized_symbol,
        price=price,
        previous_close=previous_close,
        change_pct=change_pct,
        market_cap=market_cap,
        pe_ratio=pe_ratio,
        pb_ratio=pb_ratio,
        dividend_yield=dividend_yield,
        sector=sector,
        market=market,
        exchange=exchange,
        currency=currency,
        industry=industry
    )
