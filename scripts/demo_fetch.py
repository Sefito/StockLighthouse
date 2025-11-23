#!/usr/bin/env python3
"""
Demo script to fetch sample stock data using the YFinance ingestor.

Fetches 10 popular stock symbols and writes the raw JSON data to data/samples/.
"""
import json
import sys
from pathlib import Path

# Add backend/src to path for imports
backend_src = Path(__file__).parent.parent / "backend" / "src"
sys.path.insert(0, str(backend_src))

from stocklighthouse.ingest.yfinance_ingestor import YFinanceIngestor
from stocklighthouse.models import IngestorRequest


def main():
    """Fetch sample stock data and write to data/samples/."""
    # Sample tickers - popular stocks across different sectors
    sample_symbols = [
        "AAPL",   # Technology
        "MSFT",   # Technology
        "GOOGL",  # Technology
        "AMZN",   # Consumer Cyclical
        "TSLA",   # Automotive
        "JPM",    # Financial
        "JNJ",    # Healthcare
        "V",      # Financial Services
        "WMT",    # Consumer Defensive
        "PG",     # Consumer Defensive
    ]
    
    print("=" * 60)
    print("StockLighthouse YFinance Ingestor Demo")
    print("=" * 60)
    print(f"\nFetching data for {len(sample_symbols)} symbols:")
    print(", ".join(sample_symbols))
    print("\n" + "-" * 60)
    
    # Initialize ingestor with reasonable settings
    ingestor = YFinanceIngestor(
        cache_ttl_seconds=300,  # 5 minute cache
        max_retries=3,
        initial_backoff=1.0,
        backoff_multiplier=2.0
    )
    
    # Create request
    request = IngestorRequest(
        symbols=sample_symbols,
        use_cache=True
    )
    
    # Fetch data
    print("\nFetching data from yfinance...")
    response = ingestor.fetch(request)
    
    # Print summary
    print("\n" + "=" * 60)
    print("Fetch Summary:")
    print("=" * 60)
    print(f"Total symbols:   {len(sample_symbols)}")
    print(f"Fetched:         {response.fetched_count}")
    print(f"Cached:          {response.cached_count}")
    print(f"Failed:          {response.failed_count}")
    print()
    
    # Create output directory
    output_dir = Path(__file__).parent.parent / "data" / "samples"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Write individual ticker files and collect summary
    summary_data = {
        "fetch_time": None,
        "symbols": [],
        "statistics": {
            "total": len(sample_symbols),
            "successful": response.fetched_count + response.cached_count,
            "failed": response.failed_count
        }
    }
    
    print("Writing results to data/samples/:")
    print("-" * 60)
    
    for ticker_data in response.tickers:
        symbol = ticker_data.symbol
        
        if ticker_data.success:
            # Write raw data to individual file
            output_file = output_dir / f"{symbol.lower()}.json"
            
            output_data = {
                "symbol": symbol,
                "success": True,
                "raw_data": ticker_data.raw_data,
                "fast_info": ticker_data.fast_info
            }
            
            with open(output_file, "w") as f:
                json.dump(output_data, f, indent=2, default=str)
            
            print(f"  ✓ {symbol:6s} -> {output_file.name}")
            
            # Add to summary
            summary_data["symbols"].append({
                "symbol": symbol,
                "success": True,
                "file": output_file.name
            })
            
            # Capture first fetch time for summary
            if summary_data["fetch_time"] is None and ticker_data.raw_data:
                summary_data["fetch_time"] = ticker_data.raw_data.get("fetch_time")
        else:
            print(f"  ✗ {symbol:6s} -> FAILED: {ticker_data.error}")
            summary_data["symbols"].append({
                "symbol": symbol,
                "success": False,
                "error": ticker_data.error
            })
    
    # Write summary file
    summary_file = output_dir / "fetch_summary.json"
    with open(summary_file, "w") as f:
        json.dump(summary_data, f, indent=2, default=str)
    
    print(f"\n  Summary written to: {summary_file.name}")
    print("\n" + "=" * 60)
    print("Demo completed successfully!")
    print("=" * 60)
    
    # Print example data snippet
    if response.tickers and response.tickers[0].success:
        first_ticker = response.tickers[0]
        print(f"\nExample data structure for {first_ticker.symbol}:")
        print("-" * 60)
        
        if first_ticker.raw_data:
            # Print first few keys from raw_data
            print("Raw data keys:", ", ".join(list(first_ticker.raw_data.keys())[:5]), "...")
            
            if "info" in first_ticker.raw_data:
                info_keys = list(first_ticker.raw_data["info"].keys())[:10]
                print("Info keys sample:", ", ".join(info_keys), "...")
        
        if first_ticker.fast_info:
            print("Fast info:", json.dumps(first_ticker.fast_info, indent=2, default=str))
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
