"""
FastAPI application for StockLighthouse.

Provides REST API endpoints for stock data, search, and sector analysis.
"""
from typing import Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import json
import os
from pathlib import Path

from stocklighthouse.models import StockKPIs
from stocklighthouse.analyzer import sector_aggregate, weighted_average_pe_by_sector

app = FastAPI(
    title="StockLighthouse API",
    description="Stock data and analysis API",
    version="1.0.0"
)

# Configure CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load stock data from JSON
def load_stock_data() -> list[StockKPIs]:
    """Load normalized stock KPIs from JSON file."""
    data_path = Path(__file__).parent.parent.parent.parent.parent / "data" / "normalized" / "normalized_kpis.json"
    if not data_path.exists():
        return []
    
    with open(data_path, 'r') as f:
        data = json.load(f)
        return [StockKPIs(**item) for item in data]

# Cache stock data
_stock_cache: Optional[list[StockKPIs]] = None

def get_stocks() -> list[StockKPIs]:
    """Get cached stock data or load from file."""
    global _stock_cache
    if _stock_cache is None:
        _stock_cache = load_stock_data()
    return _stock_cache


@app.get("/")
def read_root():
    """Health check endpoint."""
    return {"status": "ok", "message": "StockLighthouse API"}


@app.get("/api/stocks/search")
def search_stocks(q: str = ""):
    """
    Search for stocks by symbol or name.
    
    Args:
        q: Search query (symbol or partial match)
        
    Returns:
        List of matching stocks
    """
    stocks = get_stocks()
    
    if not q:
        # Return first 20 stocks if no query
        return stocks[:20]
    
    query = q.upper()
    results = [
        stock for stock in stocks
        if query in stock.symbol.upper() or 
           (stock.sector and query in stock.sector.upper()) or
           (stock.industry and query in stock.industry.upper())
    ]
    
    return results[:50]  # Limit to 50 results


@app.get("/api/stocks/{symbol}")
def get_stock_details(symbol: str):
    """
    Get detailed information for a specific stock.
    
    Args:
        symbol: Stock ticker symbol
        
    Returns:
        Stock details with KPIs
    """
    stocks = get_stocks()
    symbol_upper = symbol.upper()
    
    for stock in stocks:
        if stock.symbol.upper() == symbol_upper:
            return stock
    
    raise HTTPException(status_code=404, detail=f"Stock {symbol} not found")


@app.get("/api/stocks/{symbol}/history")
def get_stock_history(symbol: str):
    """
    Get historical price data for a stock.
    
    Note: This is mock data for demonstration. In production, this would
    fetch real historical data from the ingestor.
    
    Args:
        symbol: Stock ticker symbol
        
    Returns:
        Historical price data
    """
    # Get current stock to ensure it exists
    stock = get_stock_details(symbol)
    
    if not stock.price or not stock.previous_close:
        return {"symbol": symbol, "dates": [], "prices": []}
    
    # Generate mock historical data (30 days)
    import datetime
    dates = []
    prices = []
    
    current_price = stock.price
    base_date = datetime.date.today()
    
    for i in range(30, -1, -1):
        date = base_date - datetime.timedelta(days=i)
        dates.append(date.isoformat())
        
        # Simple random walk for demo
        import random
        variation = random.uniform(-0.02, 0.02)
        prices.append(round(current_price * (1 + variation), 2))
    
    # Ensure last price matches current
    prices[-1] = stock.price
    
    return {
        "symbol": symbol,
        "dates": dates,
        "prices": prices
    }


@app.get("/api/stocks/{symbol}/pe-distribution")
def get_pe_distribution(symbol: str):
    """
    Get P/E ratio distribution for a stock's sector.
    
    Args:
        symbol: Stock ticker symbol
        
    Returns:
        P/E distribution data for the sector
    """
    stock = get_stock_details(symbol)
    stocks = get_stocks()
    
    # Get all stocks in the same sector
    sector_stocks = [
        s for s in stocks
        if s.sector == stock.sector and s.pe_ratio is not None
    ]
    
    if not sector_stocks:
        return {"symbol": symbol, "sector": stock.sector, "pe_ratios": []}
    
    pe_ratios = [s.pe_ratio for s in sector_stocks if s.pe_ratio]
    symbols = [s.symbol for s in sector_stocks if s.pe_ratio]
    
    return {
        "symbol": symbol,
        "sector": stock.sector,
        "pe_ratios": pe_ratios,
        "symbols": symbols,
        "current_pe": stock.pe_ratio
    }


@app.get("/api/sectors")
def get_sectors():
    """
    Get sector aggregation data.
    
    Returns:
        List of sector summaries with statistics
    """
    stocks = get_stocks()
    
    if not stocks:
        return []
    
    # Get sector aggregates
    summaries = sector_aggregate(stocks)
    
    # Add weighted P/E by sector
    weighted_pes = weighted_average_pe_by_sector(stocks)
    
    # Combine data
    result = []
    for summary in summaries:
        result.append({
            "sector": summary.sector,
            "count": summary.count,
            "median_pe": summary.median_pe,
            "median_pb": summary.median_pb,
            "median_market_cap": summary.median_market_cap,
            "avg_dividend_yield": summary.avg_dividend_yield,
            "weighted_avg_pe": weighted_pes.get(summary.sector),
            "top_tickers": [
                {"symbol": symbol, "market_cap": market_cap}
                for symbol, market_cap in summary.top_tickers
            ]
        })
    
    return result


@app.get("/api/sectors/{sector_name}")
def get_sector_details(sector_name: str):
    """
    Get detailed information for a specific sector.
    
    Args:
        sector_name: Name of the sector
        
    Returns:
        Sector details with all stocks
    """
    stocks = get_stocks()
    
    # Get stocks in sector
    sector_stocks = [
        stock for stock in stocks
        if stock.sector and stock.sector.lower() == sector_name.lower()
    ]
    
    if not sector_stocks:
        raise HTTPException(status_code=404, detail=f"Sector {sector_name} not found")
    
    # Get sector summary
    summaries = sector_aggregate(sector_stocks)
    summary = summaries[0] if summaries else None
    
    return {
        "sector": sector_name,
        "summary": summary,
        "stocks": sector_stocks
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
