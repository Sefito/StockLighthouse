#!/usr/bin/env python3
"""
Sample script demonstrating normalization of raw yfinance data.

This script:
1. Reads raw data from data/samples/ directory
2. Normalizes each ticker's data using the normalize() function
3. Exports normalized JSON
4. Exports JSON schema for StockKPIs
5. Displays summary statistics

Usage:
    python sample_normalize.py
"""
import json
import sys
from pathlib import Path
from typing import List, Dict, Any

# Add backend/src to path for imports
backend_src = Path(__file__).parent / "backend" / "src"
sys.path.insert(0, str(backend_src))

from stocklighthouse.normalizer import normalize
from stocklighthouse.models import StockKPIs


def load_raw_data(samples_dir: Path) -> List[Dict[str, Any]]:
    """
    Load raw data from sample JSON files.
    
    Args:
        samples_dir: Directory containing sample JSON files
        
    Returns:
        List of raw data dictionaries
    """
    raw_data = []
    
    # Find all JSON files except the summary
    json_files = [f for f in samples_dir.glob("*.json") if f.name != "fetch_summary.json"]
    
    for json_file in sorted(json_files):
        try:
            with open(json_file, "r") as f:
                data = json.load(f)
                if data.get("success") and data.get("raw_data"):
                    raw_data.append({
                        "symbol": data["symbol"],
                        "info": data["raw_data"].get("info", {}),
                        "source_file": json_file.name
                    })
        except Exception as e:
            print(f"Warning: Failed to load {json_file.name}: {e}")
    
    return raw_data


def normalize_samples(raw_data: List[Dict[str, Any]]) -> List[StockKPIs]:
    """
    Normalize all raw data samples.
    
    Args:
        raw_data: List of raw data dictionaries
        
    Returns:
        List of normalized StockKPIs
    """
    normalized = []
    
    for item in raw_data:
        symbol = item["symbol"]
        info = item["info"]
        
        try:
            kpis = normalize(symbol, info)
            normalized.append(kpis)
            print(f"✓ Normalized {symbol}")
        except Exception as e:
            print(f"✗ Failed to normalize {symbol}: {e}")
    
    return normalized


def export_normalized_json(normalized: List[StockKPIs], output_file: Path):
    """
    Export normalized data to JSON file.
    
    Args:
        normalized: List of normalized StockKPIs
        output_file: Output file path
    """
    # Convert to list of dicts
    normalized_dicts = [kpis.model_dump() for kpis in normalized]
    
    with open(output_file, "w") as f:
        json.dump(normalized_dicts, f, indent=2)
    
    print(f"\n✓ Exported normalized data to {output_file}")


def export_json_schema(output_file: Path):
    """
    Export JSON schema for StockKPIs.
    
    Args:
        output_file: Output file path
    """
    schema = StockKPIs.model_json_schema()
    
    with open(output_file, "w") as f:
        json.dump(schema, f, indent=2)
    
    print(f"✓ Exported JSON schema to {output_file}")


def print_statistics(normalized: List[StockKPIs]):
    """
    Print summary statistics about normalized data.
    
    Args:
        normalized: List of normalized StockKPIs
    """
    print("\n" + "=" * 70)
    print("NORMALIZATION STATISTICS")
    print("=" * 70)
    
    total = len(normalized)
    print(f"\nTotal symbols normalized: {total}")
    
    # Count fields populated
    field_counts = {
        "price": sum(1 for kpi in normalized if kpi.price is not None),
        "previous_close": sum(1 for kpi in normalized if kpi.previous_close is not None),
        "change_pct": sum(1 for kpi in normalized if kpi.change_pct is not None),
        "market_cap": sum(1 for kpi in normalized if kpi.market_cap is not None),
        "pe_ratio": sum(1 for kpi in normalized if kpi.pe_ratio is not None),
        "pb_ratio": sum(1 for kpi in normalized if kpi.pb_ratio is not None),
        "dividend_yield": sum(1 for kpi in normalized if kpi.dividend_yield is not None),
        "sector": sum(1 for kpi in normalized if kpi.sector is not None),
        "industry": sum(1 for kpi in normalized if kpi.industry is not None),
        "market": sum(1 for kpi in normalized if kpi.market is not None),
        "exchange": sum(1 for kpi in normalized if kpi.exchange is not None),
        "currency": sum(1 for kpi in normalized if kpi.currency is not None),
    }
    
    print("\nField coverage:")
    print("-" * 70)
    for field, count in field_counts.items():
        percentage = (count / total) * 100 if total > 0 else 0
        print(f"  {field:18s}: {count:3d}/{total:3d} ({percentage:5.1f}%)")
    
    # Market distribution
    market_dist = {}
    for kpi in normalized:
        market = kpi.market or "unknown"
        market_dist[market] = market_dist.get(market, 0) + 1
    
    print("\nMarket distribution:")
    print("-" * 70)
    for market, count in sorted(market_dist.items()):
        percentage = (count / total) * 100 if total > 0 else 0
        print(f"  {market:18s}: {count:3d} ({percentage:5.1f}%)")
    
    # Sector distribution
    sector_dist = {}
    for kpi in normalized:
        sector = kpi.sector or "unknown"
        sector_dist[sector] = sector_dist.get(sector, 0) + 1
    
    print("\nSector distribution:")
    print("-" * 70)
    for sector, count in sorted(sector_dist.items()):
        percentage = (count / total) * 100 if total > 0 else 0
        print(f"  {sector:25s}: {count:3d} ({percentage:5.1f}%)")


def print_sample_records(normalized: List[StockKPIs], num_samples: int = 3):
    """
    Print sample normalized records.
    
    Args:
        normalized: List of normalized StockKPIs
        num_samples: Number of samples to print
    """
    print("\n" + "=" * 70)
    print(f"SAMPLE NORMALIZED RECORDS (first {num_samples})")
    print("=" * 70)
    
    for i, kpis in enumerate(normalized[:num_samples]):
        print(f"\n{i+1}. {kpis.symbol}")
        print("-" * 70)
        print(f"  Price:           ${kpis.price:,.2f}" if kpis.price else "  Price:           N/A")
        print(f"  Previous Close:  ${kpis.previous_close:,.2f}" if kpis.previous_close else "  Previous Close:  N/A")
        print(f"  Change:          {kpis.change_pct:+.2f}%" if kpis.change_pct is not None else "  Change:          N/A")
        print(f"  Market Cap:      ${kpis.market_cap:,.0f}" if kpis.market_cap else "  Market Cap:      N/A")
        print(f"  P/E Ratio:       {kpis.pe_ratio:.2f}" if kpis.pe_ratio else "  P/E Ratio:       N/A")
        print(f"  P/B Ratio:       {kpis.pb_ratio:.2f}" if kpis.pb_ratio else "  P/B Ratio:       N/A")
        print(f"  Dividend Yield:  {kpis.dividend_yield:.2%}" if kpis.dividend_yield is not None else "  Dividend Yield:  N/A")
        print(f"  Sector:          {kpis.sector}" if kpis.sector else "  Sector:          N/A")
        print(f"  Industry:        {kpis.industry}" if kpis.industry else "  Industry:        N/A")
        print(f"  Market:          {kpis.market}" if kpis.market else "  Market:          N/A")
        print(f"  Exchange:        {kpis.exchange}" if kpis.exchange else "  Exchange:        N/A")
        print(f"  Currency:        {kpis.currency}" if kpis.currency else "  Currency:        N/A")


def main():
    """Main execution function."""
    print("=" * 70)
    print("StockLighthouse Normalization Demo")
    print("=" * 70)
    
    # Setup paths
    base_dir = Path(__file__).parent
    samples_dir = base_dir / "data" / "samples"
    output_dir = base_dir / "data" / "normalized"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Check if samples directory exists
    if not samples_dir.exists():
        print(f"\nError: Samples directory not found: {samples_dir}")
        print("Please run 'python scripts/demo_fetch.py' first to generate sample data.")
        return 1
    
    # Load raw data
    print(f"\nLoading raw data from {samples_dir}...")
    print("-" * 70)
    raw_data = load_raw_data(samples_dir)
    
    if not raw_data:
        print("\nError: No raw data found in samples directory.")
        return 1
    
    print(f"\nLoaded {len(raw_data)} raw data files")
    
    # Normalize data
    print("\nNormalizing data...")
    print("-" * 70)
    normalized = normalize_samples(raw_data)
    
    if not normalized:
        print("\nError: No data was normalized successfully.")
        return 1
    
    # Export normalized JSON
    print("\nExporting results...")
    print("-" * 70)
    normalized_file = output_dir / "normalized_kpis.json"
    export_normalized_json(normalized, normalized_file)
    
    # Export JSON schema
    schema_file = output_dir / "kpis_schema.json"
    export_json_schema(schema_file)
    
    # Print statistics
    print_statistics(normalized)
    
    # Print sample records
    print_sample_records(normalized, num_samples=3)
    
    print("\n" + "=" * 70)
    print("Normalization completed successfully!")
    print("=" * 70)
    print(f"\nOutput files:")
    print(f"  - Normalized data: {normalized_file}")
    print(f"  - JSON schema:     {schema_file}")
    print("\n" + "=" * 70)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
