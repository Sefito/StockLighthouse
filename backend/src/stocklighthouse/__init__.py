"""
StockLighthouse - Stock data ingestion, normalization, and analysis platform.

StockLighthouse provides a comprehensive suite of tools for fetching, normalizing,
and analyzing stock market data from various providers. The platform includes:

- **Ingestor**: Robust data fetching with retry logic and caching
- **Normalizer**: Defensive parsing and canonical schema mapping
- **Analyzer**: Sector aggregation and statistical computations
- **API**: RESTful API for data access and integration

Modules:
    models: Pydantic data models for type-safe data handling
    ingest: Data fetching modules (YFinance and others)
    normalizer: Raw data normalization to canonical schema
    analyzer: Sector analysis and aggregation functions
    api: FastAPI-based REST API endpoints

Example:
    >>> from stocklighthouse.ingest.yfinance_ingestor import YFinanceIngestor
    >>> from stocklighthouse.normalizer import normalize
    >>> 
    >>> # Fetch and normalize stock data
    >>> ingestor = YFinanceIngestor()
    >>> ticker_data = ingestor.fetch_single("AAPL")
    >>> if ticker_data.success:
    ...     kpis = normalize("AAPL", ticker_data.raw_data["info"])
    ...     print(f"{kpis.symbol}: ${kpis.price}")

For detailed documentation, see README.md in the repository root.
"""
__version__ = "0.1.0"
