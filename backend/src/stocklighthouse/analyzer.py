"""
Sector aggregation and derived metrics for StockLighthouse.

Provides functions to aggregate stock data by sector and compute
weighted averages for analysis.
"""
from typing import Optional
from statistics import median
from pydantic import BaseModel
from stocklighthouse.models import StockKPIs


class SectorSummary(BaseModel):
    """
    Summary statistics for a sector.
    
    Attributes:
        sector: Sector name
        count: Number of stocks in the sector
        median_pe: Median price-to-earnings ratio
        median_pb: Median price-to-book ratio
        median_market_cap: Median market capitalization
        avg_dividend_yield: Average dividend yield
        top_tickers: Top 3 tickers by market cap (symbol, market_cap pairs)
    """
    sector: str
    count: int
    median_pe: Optional[float] = None
    median_pb: Optional[float] = None
    median_market_cap: Optional[float] = None
    avg_dividend_yield: Optional[float] = None
    top_tickers: list[tuple[str, Optional[float]]] = []


def sector_aggregate(stocks: list[StockKPIs]) -> list[SectorSummary]:
    """
    Aggregate stock data by sector.
    
    Groups stocks by sector and computes summary statistics including:
    - Count of stocks
    - Median P/E ratio
    - Median P/B ratio
    - Median market cap
    - Average dividend yield
    - Top 3 tickers by market cap
    
    Stocks with None/missing sector are grouped under "Unknown" sector.
    
    Args:
        stocks: List of StockKPIs to aggregate
        
    Returns:
        List of SectorSummary objects, one per sector
        
    Example:
        >>> stocks = [
        ...     StockKPIs(symbol="AAPL", sector="Technology", pe_ratio=28.5, market_cap=2.4e12),
        ...     StockKPIs(symbol="MSFT", sector="Technology", pe_ratio=30.2, market_cap=2.1e12),
        ... ]
        >>> summaries = sector_aggregate(stocks)
        >>> summaries[0].sector
        'Technology'
        >>> summaries[0].count
        2
    """
    if not stocks:
        return []
    
    # Group stocks by sector
    sector_map: dict[str, list[StockKPIs]] = {}
    for stock in stocks:
        sector = stock.sector if stock.sector else "Unknown"
        if sector not in sector_map:
            sector_map[sector] = []
        sector_map[sector].append(stock)
    
    # Build summaries for each sector
    summaries = []
    for sector, sector_stocks in sector_map.items():
        summary = _create_sector_summary(sector, sector_stocks)
        summaries.append(summary)
    
    # Sort by count descending, then by sector name
    summaries.sort(key=lambda s: (-s.count, s.sector))
    
    return summaries


def _create_sector_summary(sector: str, stocks: list[StockKPIs]) -> SectorSummary:
    """
    Create a sector summary from a list of stocks.
    
    Args:
        sector: Sector name
        stocks: List of stocks in the sector
        
    Returns:
        SectorSummary object
    """
    count = len(stocks)
    
    # Collect non-None values for each metric
    pe_values = [s.pe_ratio for s in stocks if s.pe_ratio is not None]
    pb_values = [s.pb_ratio for s in stocks if s.pb_ratio is not None]
    market_cap_values = [s.market_cap for s in stocks if s.market_cap is not None]
    dividend_values = [s.dividend_yield for s in stocks if s.dividend_yield is not None]
    
    # Compute medians
    median_pe = median(pe_values) if pe_values else None
    median_pb = median(pb_values) if pb_values else None
    median_market_cap = median(market_cap_values) if market_cap_values else None
    
    # Compute average dividend yield
    avg_dividend_yield = sum(dividend_values) / len(dividend_values) if dividend_values else None
    
    # Find top 3 tickers by market cap
    stocks_with_cap = [(s.symbol, s.market_cap) for s in stocks if s.market_cap is not None]
    stocks_with_cap.sort(key=lambda x: x[1], reverse=True)
    top_tickers = stocks_with_cap[:3]
    
    # Include stocks without market cap at the end if we have fewer than 3
    if len(top_tickers) < 3:
        stocks_without_cap = [(s.symbol, None) for s in stocks if s.market_cap is None]
        top_tickers.extend(stocks_without_cap[:3 - len(top_tickers)])
    
    return SectorSummary(
        sector=sector,
        count=count,
        median_pe=median_pe,
        median_pb=median_pb,
        median_market_cap=median_market_cap,
        avg_dividend_yield=avg_dividend_yield,
        top_tickers=top_tickers
    )


def weighted_average_pe(stocks: list[StockKPIs]) -> Optional[float]:
    """
    Calculate market-cap weighted average P/E ratio.
    
    Computes the weighted average P/E ratio where each stock's P/E is weighted
    by its market capitalization. Only includes stocks with both P/E ratio and
    market cap defined.
    
    Args:
        stocks: List of StockKPIs
        
    Returns:
        Weighted average P/E ratio, or None if no valid stocks
        
    Example:
        >>> stocks = [
        ...     StockKPIs(symbol="A", pe_ratio=20.0, market_cap=1e12),
        ...     StockKPIs(symbol="B", pe_ratio=30.0, market_cap=2e12),
        ... ]
        >>> weighted_average_pe(stocks)
        26.666666666666668
    """
    # Filter stocks with both PE and market cap
    valid_stocks = [s for s in stocks if s.pe_ratio is not None and s.market_cap is not None]
    
    if not valid_stocks:
        return None
    
    # Calculate weighted sum and total weight
    weighted_sum = sum(s.pe_ratio * s.market_cap for s in valid_stocks)
    total_weight = sum(s.market_cap for s in valid_stocks)
    
    return weighted_sum / total_weight if total_weight > 0 else None


def weighted_average_pe_by_sector(stocks: list[StockKPIs]) -> dict[str, Optional[float]]:
    """
    Calculate market-cap weighted average P/E ratio for each sector.
    
    Args:
        stocks: List of StockKPIs
        
    Returns:
        Dictionary mapping sector name to weighted average P/E ratio
        
    Example:
        >>> stocks = [
        ...     StockKPIs(symbol="A", sector="Tech", pe_ratio=20.0, market_cap=1e12),
        ...     StockKPIs(symbol="B", sector="Tech", pe_ratio=30.0, market_cap=2e12),
        ...     StockKPIs(symbol="C", sector="Health", pe_ratio=15.0, market_cap=0.5e12),
        ... ]
        >>> result = weighted_average_pe_by_sector(stocks)
        >>> result["Tech"]
        26.666666666666668
    """
    # Group stocks by sector
    sector_map: dict[str, list[StockKPIs]] = {}
    for stock in stocks:
        sector = stock.sector if stock.sector else "Unknown"
        if sector not in sector_map:
            sector_map[sector] = []
        sector_map[sector].append(stock)
    
    # Calculate weighted average for each sector
    result = {}
    for sector, sector_stocks in sector_map.items():
        result[sector] = weighted_average_pe(sector_stocks)
    
    return result
