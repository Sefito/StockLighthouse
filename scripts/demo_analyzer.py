#!/usr/bin/env python3
"""
Demo script showing how to use the sector analyzer.

This script demonstrates:
1. Loading stock data
2. Aggregating by sector
3. Calculating weighted averages
4. Displaying results
"""
import sys
import json
from pathlib import Path

# Add the backend source to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend" / "src"))

from stocklighthouse.models import StockKPIs
from stocklighthouse.analyzer import (
    sector_aggregate,
    weighted_average_pe,
    weighted_average_pe_by_sector
)


def main():
    """Run the analyzer demo."""
    print("=" * 60)
    print("StockLighthouse Sector Analyzer Demo")
    print("=" * 60)
    print()
    
    # Sample stock data
    stocks = [
        StockKPIs(
            symbol="AAPL",
            sector="Technology",
            pe_ratio=28.5,
            pb_ratio=40.2,
            market_cap=2.75e12,
            dividend_yield=0.0052
        ),
        StockKPIs(
            symbol="MSFT",
            sector="Technology",
            pe_ratio=35.2,
            pb_ratio=13.1,
            market_cap=2.82e12,
            dividend_yield=0.0078
        ),
        StockKPIs(
            symbol="JNJ",
            sector="Healthcare",
            pe_ratio=15.5,
            pb_ratio=5.2,
            market_cap=0.38e12,
            dividend_yield=0.0295
        ),
        StockKPIs(
            symbol="PFE",
            sector="Healthcare",
            pe_ratio=10.2,
            pb_ratio=1.8,
            market_cap=0.16e12,
            dividend_yield=0.0612
        ),
        StockKPIs(
            symbol="UNKNOWN",
            sector=None,
            pe_ratio=12.0,
            market_cap=0.05e12
        ),
    ]
    
    print(f"Analyzing {len(stocks)} stocks...\n")
    
    # 1. Sector aggregation
    print("📊 Sector Aggregation")
    print("-" * 60)
    summaries = sector_aggregate(stocks)
    
    for summary in summaries:
        print(f"\n{summary.sector} Sector:")
        print(f"  Count: {summary.count} stocks")
        print(f"  Median P/E: {summary.median_pe:.2f}" if summary.median_pe else "  Median P/E: N/A")
        print(f"  Median P/B: {summary.median_pb:.2f}" if summary.median_pb else "  Median P/B: N/A")
        print(f"  Median Market Cap: ${summary.median_market_cap/1e12:.2f}T" if summary.median_market_cap else "  Median Market Cap: N/A")
        print(f"  Avg Dividend Yield: {summary.avg_dividend_yield*100:.2f}%" if summary.avg_dividend_yield else "  Avg Dividend Yield: N/A")
        print(f"  Top Tickers: {', '.join(t[0] for t in summary.top_tickers)}")
    
    # 2. Weighted average P/E
    print("\n\n💰 Market-Cap Weighted Averages")
    print("-" * 60)
    
    overall_weighted = weighted_average_pe(stocks)
    if overall_weighted:
        print(f"\nOverall Weighted P/E: {overall_weighted:.2f}")
    
    sector_weighted = weighted_average_pe_by_sector(stocks)
    print("\nWeighted P/E by Sector:")
    for sector, weighted_pe in sorted(sector_weighted.items()):
        if weighted_pe:
            print(f"  {sector}: {weighted_pe:.2f}")
        else:
            print(f"  {sector}: N/A")
    
    # 3. Load and display the sample sectors file
    print("\n\n📄 Sample Sectors JSON")
    print("-" * 60)
    sample_path = Path(__file__).parent.parent / "data" / "aggregates" / "sample_sectors.json"
    
    if sample_path.exists():
        with open(sample_path, 'r') as f:
            sample_data = json.load(f)
        print(f"\nLoaded sample data from: {sample_path}")
        print(f"Total stocks: {sample_data['total_stocks']}")
        print(f"Sectors analyzed: {sample_data['sector_count']}")
        print("\nTop 3 sectors by stock count:")
        for i, sector_data in enumerate(sample_data['sectors'][:3], 1):
            print(f"  {i}. {sector_data['sector']}: {sector_data['count']} stocks")
    else:
        print(f"\nSample file not found at: {sample_path}")
    
    print("\n" + "=" * 60)
    print("Demo complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
