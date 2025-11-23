import pytest
from stocklighthouse.analyzer import (
    sector_aggregate, 
    weighted_average_pe,
    weighted_average_pe_by_sector,
    SectorSummary
)
from stocklighthouse.models import StockKPIs


def test_sector_aggregate_empty_list():
    """Test sector aggregation with empty list returns empty list."""
    result = sector_aggregate([])
    assert result == []


def test_sector_aggregate_single_stock():
    """Test sector aggregation with a single stock."""
    stocks = [
        StockKPIs(
            symbol="AAPL",
            sector="Technology",
            pe_ratio=28.5,
            pb_ratio=40.2,
            market_cap=2.4e12,
            dividend_yield=0.005
        )
    ]
    result = sector_aggregate(stocks)
    
    assert len(result) == 1
    assert result[0].sector == "Technology"
    assert result[0].count == 1
    assert result[0].median_pe == 28.5
    assert result[0].median_pb == 40.2
    assert result[0].median_market_cap == 2.4e12
    assert result[0].avg_dividend_yield == 0.005
    assert result[0].top_tickers == [("AAPL", 2.4e12)]


def test_sector_aggregate_multiple_sectors():
    """Test aggregation across multiple sectors."""
    stocks = [
        StockKPIs(symbol="AAPL", sector="Technology", pe_ratio=28.5, market_cap=2.4e12),
        StockKPIs(symbol="MSFT", sector="Technology", pe_ratio=30.2, market_cap=2.1e12),
        StockKPIs(symbol="JNJ", sector="Healthcare", pe_ratio=15.5, market_cap=0.4e12),
        StockKPIs(symbol="PFE", sector="Healthcare", pe_ratio=12.0, market_cap=0.3e12),
    ]
    result = sector_aggregate(stocks)
    
    assert len(result) == 2
    
    # Should be sorted by count descending, then sector name
    tech = next(s for s in result if s.sector == "Technology")
    health = next(s for s in result if s.sector == "Healthcare")
    
    assert tech.count == 2
    assert health.count == 2
    
    # Check median calculations
    assert tech.median_pe == pytest.approx((28.5 + 30.2) / 2)
    assert health.median_pe == pytest.approx((15.5 + 12.0) / 2)


def test_sector_aggregate_median_calculation():
    """Test median calculation with odd and even number of values."""
    # Odd number of values
    stocks = [
        StockKPIs(symbol="A", sector="Tech", pe_ratio=10.0),
        StockKPIs(symbol="B", sector="Tech", pe_ratio=20.0),
        StockKPIs(symbol="C", sector="Tech", pe_ratio=30.0),
    ]
    result = sector_aggregate(stocks)
    assert result[0].median_pe == 20.0
    
    # Even number of values
    stocks.append(StockKPIs(symbol="D", sector="Tech", pe_ratio=40.0))
    result = sector_aggregate(stocks)
    assert result[0].median_pe == pytest.approx(25.0)  # (20 + 30) / 2


def test_sector_aggregate_with_none_values():
    """Test aggregation handles None values correctly."""
    stocks = [
        StockKPIs(symbol="A", sector="Tech", pe_ratio=20.0, pb_ratio=None, market_cap=1e12),
        StockKPIs(symbol="B", sector="Tech", pe_ratio=None, pb_ratio=5.0, market_cap=2e12),
        StockKPIs(symbol="C", sector="Tech", pe_ratio=30.0, pb_ratio=6.0, market_cap=None),
    ]
    result = sector_aggregate(stocks)
    
    assert len(result) == 1
    assert result[0].count == 3
    # Median PE should only consider non-None values
    assert result[0].median_pe == pytest.approx(25.0)  # median of [20, 30]
    # Median PB should only consider non-None values
    assert result[0].median_pb == pytest.approx(5.5)  # median of [5, 6]
    # Median market cap should only consider non-None values
    assert result[0].median_market_cap == pytest.approx(1.5e12)  # median of [1e12, 2e12]


def test_sector_aggregate_all_none_values():
    """Test aggregation when all metric values are None."""
    stocks = [
        StockKPIs(symbol="A", sector="Tech"),
        StockKPIs(symbol="B", sector="Tech"),
    ]
    result = sector_aggregate(stocks)
    
    assert len(result) == 1
    assert result[0].count == 2
    assert result[0].median_pe is None
    assert result[0].median_pb is None
    assert result[0].median_market_cap is None
    assert result[0].avg_dividend_yield is None


def test_sector_aggregate_unknown_sector():
    """Test that stocks with None sector are grouped as Unknown."""
    stocks = [
        StockKPIs(symbol="A", sector=None, pe_ratio=20.0),
        StockKPIs(symbol="B", sector=None, pe_ratio=30.0),
        StockKPIs(symbol="C", sector="Tech", pe_ratio=15.0),
    ]
    result = sector_aggregate(stocks)
    
    assert len(result) == 2
    
    unknown = next(s for s in result if s.sector == "Unknown")
    tech = next(s for s in result if s.sector == "Tech")
    
    assert unknown.count == 2
    assert tech.count == 1
    assert unknown.median_pe == pytest.approx(25.0)


def test_sector_aggregate_mixed_known_and_unknown():
    """Test aggregation with mix of known and unknown sectors."""
    stocks = [
        StockKPIs(symbol="A", sector="Technology", pe_ratio=28.5, market_cap=2.4e12),
        StockKPIs(symbol="B", sector=None, pe_ratio=15.0, market_cap=0.5e12),
        StockKPIs(symbol="C", sector="Healthcare", pe_ratio=12.0, market_cap=0.3e12),
        StockKPIs(symbol="D", sector=None, pe_ratio=18.0, market_cap=0.6e12),
    ]
    result = sector_aggregate(stocks)
    
    assert len(result) == 3
    sectors = {s.sector for s in result}
    assert "Technology" in sectors
    assert "Healthcare" in sectors
    assert "Unknown" in sectors
    
    unknown = next(s for s in result if s.sector == "Unknown")
    assert unknown.count == 2


def test_sector_aggregate_top_tickers():
    """Test that top 3 tickers by market cap are correctly identified."""
    stocks = [
        StockKPIs(symbol="A", sector="Tech", market_cap=3.0e12),
        StockKPIs(symbol="B", sector="Tech", market_cap=1.0e12),
        StockKPIs(symbol="C", sector="Tech", market_cap=2.0e12),
        StockKPIs(symbol="D", sector="Tech", market_cap=0.5e12),
    ]
    result = sector_aggregate(stocks)
    
    assert len(result[0].top_tickers) == 3
    # Should be sorted by market cap descending
    assert result[0].top_tickers[0] == ("A", 3.0e12)
    assert result[0].top_tickers[1] == ("C", 2.0e12)
    assert result[0].top_tickers[2] == ("B", 1.0e12)


def test_sector_aggregate_top_tickers_with_none():
    """Test top tickers when some stocks have None market cap."""
    stocks = [
        StockKPIs(symbol="A", sector="Tech", market_cap=2.0e12),
        StockKPIs(symbol="B", sector="Tech", market_cap=None),
        StockKPIs(symbol="C", sector="Tech", market_cap=1.0e12),
        StockKPIs(symbol="D", sector="Tech", market_cap=None),
    ]
    result = sector_aggregate(stocks)
    
    # Should have 3 tickers: 2 with market cap + 1 without
    assert len(result[0].top_tickers) == 3
    assert result[0].top_tickers[0] == ("A", 2.0e12)
    assert result[0].top_tickers[1] == ("C", 1.0e12)
    assert result[0].top_tickers[2][1] is None  # Third is without market cap


def test_sector_aggregate_top_tickers_fewer_than_three():
    """Test top tickers when sector has fewer than 3 stocks."""
    stocks = [
        StockKPIs(symbol="A", sector="Tech", market_cap=2.0e12),
        StockKPIs(symbol="B", sector="Tech", market_cap=1.0e12),
    ]
    result = sector_aggregate(stocks)
    
    assert len(result[0].top_tickers) == 2
    assert result[0].top_tickers[0] == ("A", 2.0e12)
    assert result[0].top_tickers[1] == ("B", 1.0e12)


def test_sector_aggregate_avg_dividend_yield():
    """Test average dividend yield calculation."""
    stocks = [
        StockKPIs(symbol="A", sector="Tech", dividend_yield=0.02),
        StockKPIs(symbol="B", sector="Tech", dividend_yield=0.03),
        StockKPIs(symbol="C", sector="Tech", dividend_yield=0.01),
    ]
    result = sector_aggregate(stocks)
    
    assert result[0].avg_dividend_yield == pytest.approx(0.02)


def test_sector_aggregate_dividend_yield_with_none():
    """Test dividend yield calculation when some values are None."""
    stocks = [
        StockKPIs(symbol="A", sector="Tech", dividend_yield=0.02),
        StockKPIs(symbol="B", sector="Tech", dividend_yield=None),
        StockKPIs(symbol="C", sector="Tech", dividend_yield=0.04),
    ]
    result = sector_aggregate(stocks)
    
    # Should average only non-None values
    assert result[0].avg_dividend_yield == pytest.approx(0.03)


def test_sector_aggregate_sorting():
    """Test that results are sorted by count descending, then sector name."""
    stocks = [
        StockKPIs(symbol="A", sector="Tech"),
        StockKPIs(symbol="B", sector="Health"),
        StockKPIs(symbol="C", sector="Health"),
        StockKPIs(symbol="D", sector="Finance"),
        StockKPIs(symbol="E", sector="Finance"),
        StockKPIs(symbol="F", sector="Energy"),
    ]
    result = sector_aggregate(stocks)
    
    # Same count (2), should be alphabetically sorted
    assert result[0].sector in ["Finance", "Health"]
    assert result[1].sector in ["Finance", "Health"]
    assert result[0].count == 2
    assert result[1].count == 2
    
    # Count 1 sectors should come after
    assert result[2].count == 1
    assert result[3].count == 1


def test_weighted_average_pe_empty_list():
    """Test weighted average PE with empty list returns None."""
    result = weighted_average_pe([])
    assert result is None


def test_weighted_average_pe_single_stock():
    """Test weighted average PE with single stock."""
    stocks = [StockKPIs(symbol="A", pe_ratio=20.0, market_cap=1e12)]
    result = weighted_average_pe(stocks)
    assert result == pytest.approx(20.0)


def test_weighted_average_pe_multiple_stocks():
    """Test weighted average PE calculation with multiple stocks."""
    stocks = [
        StockKPIs(symbol="A", pe_ratio=20.0, market_cap=1e12),
        StockKPIs(symbol="B", pe_ratio=30.0, market_cap=2e12),
    ]
    result = weighted_average_pe(stocks)
    
    # Weighted average: (20*1 + 30*2) / (1+2) = 80/3 ≈ 26.67
    expected = (20.0 * 1e12 + 30.0 * 2e12) / (1e12 + 2e12)
    assert result == pytest.approx(expected)


def test_weighted_average_pe_with_none_pe():
    """Test weighted average PE ignores stocks with None PE ratio."""
    stocks = [
        StockKPIs(symbol="A", pe_ratio=20.0, market_cap=1e12),
        StockKPIs(symbol="B", pe_ratio=None, market_cap=2e12),
        StockKPIs(symbol="C", pe_ratio=30.0, market_cap=1e12),
    ]
    result = weighted_average_pe(stocks)
    
    # Should only include A and C
    expected = (20.0 * 1e12 + 30.0 * 1e12) / (1e12 + 1e12)
    assert result == pytest.approx(expected)


def test_weighted_average_pe_with_none_market_cap():
    """Test weighted average PE ignores stocks with None market cap."""
    stocks = [
        StockKPIs(symbol="A", pe_ratio=20.0, market_cap=1e12),
        StockKPIs(symbol="B", pe_ratio=30.0, market_cap=None),
        StockKPIs(symbol="C", pe_ratio=25.0, market_cap=2e12),
    ]
    result = weighted_average_pe(stocks)
    
    # Should only include A and C
    expected = (20.0 * 1e12 + 25.0 * 2e12) / (1e12 + 2e12)
    assert result == pytest.approx(expected)


def test_weighted_average_pe_all_none():
    """Test weighted average PE when all values are None."""
    stocks = [
        StockKPIs(symbol="A", pe_ratio=None, market_cap=1e12),
        StockKPIs(symbol="B", pe_ratio=20.0, market_cap=None),
        StockKPIs(symbol="C", pe_ratio=None, market_cap=None),
    ]
    result = weighted_average_pe(stocks)
    assert result is None


def test_weighted_average_pe_zero_market_cap():
    """Test weighted average PE handles zero market cap gracefully."""
    stocks = [
        StockKPIs(symbol="A", pe_ratio=20.0, market_cap=0.0),
    ]
    result = weighted_average_pe(stocks)
    # Should return None when total weight is 0
    assert result is None


def test_weighted_average_pe_by_sector_empty():
    """Test weighted average PE by sector with empty list."""
    result = weighted_average_pe_by_sector([])
    assert result == {}


def test_weighted_average_pe_by_sector_single_sector():
    """Test weighted average PE by sector with single sector."""
    stocks = [
        StockKPIs(symbol="A", sector="Tech", pe_ratio=20.0, market_cap=1e12),
        StockKPIs(symbol="B", sector="Tech", pe_ratio=30.0, market_cap=2e12),
    ]
    result = weighted_average_pe_by_sector(stocks)
    
    assert "Tech" in result
    expected = (20.0 * 1e12 + 30.0 * 2e12) / (1e12 + 2e12)
    assert result["Tech"] == pytest.approx(expected)


def test_weighted_average_pe_by_sector_multiple_sectors():
    """Test weighted average PE by sector with multiple sectors."""
    stocks = [
        StockKPIs(symbol="A", sector="Tech", pe_ratio=20.0, market_cap=1e12),
        StockKPIs(symbol="B", sector="Tech", pe_ratio=30.0, market_cap=2e12),
        StockKPIs(symbol="C", sector="Health", pe_ratio=15.0, market_cap=0.5e12),
        StockKPIs(symbol="D", sector="Health", pe_ratio=25.0, market_cap=1.5e12),
    ]
    result = weighted_average_pe_by_sector(stocks)
    
    assert len(result) == 2
    assert "Tech" in result
    assert "Health" in result
    
    tech_expected = (20.0 * 1e12 + 30.0 * 2e12) / (1e12 + 2e12)
    health_expected = (15.0 * 0.5e12 + 25.0 * 1.5e12) / (0.5e12 + 1.5e12)
    
    assert result["Tech"] == pytest.approx(tech_expected)
    assert result["Health"] == pytest.approx(health_expected)


def test_weighted_average_pe_by_sector_unknown_sector():
    """Test weighted average PE by sector with Unknown sector."""
    stocks = [
        StockKPIs(symbol="A", sector=None, pe_ratio=20.0, market_cap=1e12),
        StockKPIs(symbol="B", sector=None, pe_ratio=30.0, market_cap=2e12),
    ]
    result = weighted_average_pe_by_sector(stocks)
    
    assert "Unknown" in result
    expected = (20.0 * 1e12 + 30.0 * 2e12) / (1e12 + 2e12)
    assert result["Unknown"] == pytest.approx(expected)


def test_weighted_average_pe_by_sector_with_none_values():
    """Test weighted average PE by sector handles None values."""
    stocks = [
        StockKPIs(symbol="A", sector="Tech", pe_ratio=20.0, market_cap=1e12),
        StockKPIs(symbol="B", sector="Tech", pe_ratio=None, market_cap=2e12),
        StockKPIs(symbol="C", sector="Health", pe_ratio=None, market_cap=None),
    ]
    result = weighted_average_pe_by_sector(stocks)
    
    assert result["Tech"] == pytest.approx(20.0)
    assert result["Health"] is None


def test_real_world_scenario():
    """Test with realistic stock data scenario."""
    stocks = [
        # Technology sector
        StockKPIs(
            symbol="AAPL", 
            sector="Technology",
            pe_ratio=28.5, 
            pb_ratio=40.2,
            market_cap=2.4e12,
            dividend_yield=0.005
        ),
        StockKPIs(
            symbol="MSFT",
            sector="Technology", 
            pe_ratio=30.2,
            pb_ratio=12.5,
            market_cap=2.1e12,
            dividend_yield=0.01
        ),
        StockKPIs(
            symbol="GOOGL",
            sector="Technology",
            pe_ratio=25.0,
            pb_ratio=6.0,
            market_cap=1.5e12,
            dividend_yield=0.0
        ),
        # Healthcare sector
        StockKPIs(
            symbol="JNJ",
            sector="Healthcare",
            pe_ratio=15.5,
            pb_ratio=5.2,
            market_cap=0.4e12,
            dividend_yield=0.025
        ),
        StockKPIs(
            symbol="PFE",
            sector="Healthcare",
            pe_ratio=12.0,
            pb_ratio=3.8,
            market_cap=0.3e12,
            dividend_yield=0.035
        ),
        # Unknown sector
        StockKPIs(
            symbol="UNKNOWN",
            sector=None,
            pe_ratio=10.0,
            market_cap=0.1e12
        ),
    ]
    
    summaries = sector_aggregate(stocks)
    
    # Should have 3 sectors
    assert len(summaries) == 3
    
    # Technology should have the most stocks
    tech = next(s for s in summaries if s.sector == "Technology")
    assert tech.count == 3
    assert tech.median_pe == pytest.approx(28.5)
    assert tech.top_tickers[0][0] == "AAPL"
    
    # Test weighted averages
    weighted_avgs = weighted_average_pe_by_sector(stocks)
    assert "Technology" in weighted_avgs
    assert "Healthcare" in weighted_avgs
    assert "Unknown" in weighted_avgs
    
    # Technology weighted PE should be closer to AAPL/MSFT due to higher market caps
    tech_weighted = weighted_avgs["Technology"]
    assert tech_weighted > 25.0  # Should be > minimum
    assert tech_weighted < 30.2  # Should be < maximum
