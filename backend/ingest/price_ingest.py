#!/usr/bin/env python3
"""
Production-ready price ingestion module for StockLighthouse.

This module fetches daily OHLCV (Open, High, Low, Close, Volume) data for stocks
in the universe and saves them to both raw CSV and normalized Parquet formats.

Features:
- Fetch historical OHLCV data from Yahoo Finance via yfinance
- Exponential backoff with configurable retries
- Data validation (continuous dates, gap detection)
- Rate limiting to respect provider limits
- Comprehensive logging and monitoring
- Progress reporting during batch ingestion
- CLI interface for easy execution

Usage:
    python backend/ingest/price_ingest.py [--universe PATH] [--lookback-days N]

Example:
    python backend/ingest/price_ingest.py --universe data/universe.csv --lookback-days 365
"""

import argparse
import csv
import logging
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field

import pandas as pd
import yfinance as yf

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class IngestionMetrics:
    """Metrics for ingestion run."""
    total_tickers: int = 0
    successful_tickers: int = 0
    failed_tickers: int = 0
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    
    @property
    def duration_seconds(self) -> float:
        """Calculate duration in seconds."""
        end = self.end_time or datetime.now()
        return (end - self.start_time).total_seconds()
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate as percentage."""
        if self.total_tickers == 0:
            return 0.0
        return (self.successful_tickers / self.total_tickers) * 100


@dataclass
class ValidationResult:
    """Result of data validation."""
    ticker: str
    total_days: int
    missing_days: int
    completeness_pct: float
    has_gaps: bool
    gap_details: List[str] = field(default_factory=list)
    
    @property
    def is_valid(self) -> bool:
        """Check if validation passed minimum threshold (98%)."""
        return self.completeness_pct >= 98.0


class PriceIngestor:
    """
    Production-ready price data ingestor with comprehensive features.
    
    Fetches daily OHLCV data from Yahoo Finance, validates it, and stores
    in both raw CSV and normalized Parquet formats.
    
    Attributes:
        universe_path: Path to universe CSV file
        lookback_days: Number of days to fetch historical data
        raw_dir: Directory for raw CSV files
        normalized_dir: Directory for normalized Parquet files
        max_retries: Maximum retry attempts
        initial_backoff: Initial backoff time in seconds
        backoff_multiplier: Multiplier for exponential backoff
        request_delay: Delay between requests in seconds
    """
    
    def __init__(
        self,
        universe_path: str = "data/universe.csv",
        lookback_days: int = 365,
        raw_dir: str = "data/raw/prices",
        normalized_dir: str = "data/normalized",
        max_retries: int = 3,
        initial_backoff: float = 1.0,
        backoff_multiplier: float = 2.0,
        request_delay: float = 0.1,
    ):
        """
        Initialize the price ingestor.
        
        Args:
            universe_path: Path to universe CSV file with ticker,sector,industry columns
            lookback_days: Number of days of historical data to fetch
            raw_dir: Directory to store raw CSV files per ticker
            normalized_dir: Directory to store normalized parquet file
            max_retries: Maximum number of retry attempts on failure
            initial_backoff: Initial backoff time in seconds for retries
            backoff_multiplier: Multiplier for exponential backoff
            request_delay: Delay between requests to respect rate limits
        """
        self.universe_path = Path(universe_path)
        self.lookback_days = lookback_days
        self.raw_dir = Path(raw_dir)
        self.normalized_dir = Path(normalized_dir)
        self.max_retries = max_retries
        self.initial_backoff = initial_backoff
        self.backoff_multiplier = backoff_multiplier
        self.request_delay = request_delay
        
        # Create directories if they don't exist
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        self.normalized_dir.mkdir(parents=True, exist_ok=True)
        
        # Setup logging files
        self.validation_log_path = self.raw_dir / "validation.log"
        self.failures_log_path = self.raw_dir / "failures.log"
        
        # Setup file handlers for logs
        self._setup_file_logging()
    
    def _setup_file_logging(self) -> None:
        """Setup file handlers for validation and failure logs."""
        # Remove existing FileHandler instances to avoid duplicates
        logger.handlers = [h for h in logger.handlers 
                          if not isinstance(h, logging.FileHandler)]
        
        # Validation log handler
        validation_handler = logging.FileHandler(self.validation_log_path, mode='a')
        validation_handler.setLevel(logging.INFO)
        validation_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(message)s'
        ))
        
        # Failures log handler
        failure_handler = logging.FileHandler(self.failures_log_path, mode='a')
        failure_handler.setLevel(logging.ERROR)
        failure_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(message)s'
        ))
        
        logger.addHandler(validation_handler)
        logger.addHandler(failure_handler)
    
    def load_universe(self) -> List[Dict[str, str]]:
        """
        Load universe of tickers from CSV file.
        
        Returns:
            List of dicts with ticker, sector, and industry information
            
        Raises:
            FileNotFoundError: If universe file doesn't exist
            ValueError: If universe file is malformed
        """
        if not self.universe_path.exists():
            raise FileNotFoundError(f"Universe file not found: {self.universe_path}")
        
        universe = []
        with open(self.universe_path, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if 'ticker' not in row:
                    raise ValueError("Universe CSV must have 'ticker' column")
                universe.append(row)
        
        logger.info(f"Loaded {len(universe)} tickers from {self.universe_path}")
        return universe
    
    def _fetch_ohlcv_with_retry(
        self,
        ticker: str,
        start_date: datetime,
        end_date: datetime
    ) -> Optional[pd.DataFrame]:
        """
        Fetch OHLCV data with exponential backoff retry logic.
        
        Args:
            ticker: Stock ticker symbol
            start_date: Start date for historical data
            end_date: End date for historical data
            
        Returns:
            DataFrame with OHLCV data or None on failure
        """
        backoff = self.initial_backoff
        last_error = None
        
        for attempt in range(self.max_retries):
            try:
                logger.debug(f"Fetching {ticker} (attempt {attempt + 1}/{self.max_retries})")
                
                # Fetch data from yfinance
                ticker_obj = yf.Ticker(ticker)
                df = ticker_obj.history(
                    start=start_date,
                    end=end_date,
                    auto_adjust=True,
                    actions=False
                )
                
                if df is not None and not df.empty:
                    # Validate that we have the required columns
                    required_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
                    if all(col in df.columns for col in required_cols):
                        logger.info(f"Successfully fetched {len(df)} rows for {ticker}")
                        return df
                    else:
                        last_error = f"Missing required columns: {required_cols}"
                        logger.warning(f"{ticker}: {last_error}")
                else:
                    last_error = "Empty or None DataFrame returned"
                    logger.warning(f"{ticker}: {last_error}")
                    
            except Exception as e:
                last_error = str(e)
                logger.warning(f"{ticker} attempt {attempt + 1} failed: {e}")
            
            # Retry with exponential backoff
            if attempt < self.max_retries - 1:
                sleep_time = backoff
                logger.debug(f"Retrying {ticker} after {sleep_time:.2f}s")
                time.sleep(sleep_time)
                backoff *= self.backoff_multiplier
        
        # All retries exhausted
        error_msg = f"Failed to fetch {ticker} after {self.max_retries} attempts: {last_error}"
        logger.error(error_msg)
        with open(self.failures_log_path, 'a') as f:
            f.write(f"{datetime.now().isoformat()} - {ticker} - {last_error}\n")
        return None
    
    def _validate_timeseries(
        self,
        ticker: str,
        df: pd.DataFrame,
        expected_days: int
    ) -> ValidationResult:
        """
        Validate timeseries data for continuity and completeness.
        
        Args:
            ticker: Stock ticker symbol
            df: DataFrame with OHLCV data
            expected_days: Expected number of trading days
            
        Returns:
            ValidationResult with validation metrics and details
        """
        total_days = len(df)
        
        # Calculate expected trading days using pandas bdate_range for accuracy
        # Note: Using datetime.now() as the reference end date for lookback validation
        # This is appropriate for ingestion validation but may vary slightly in tests
        end_date = datetime.now()
        start_date = end_date - timedelta(days=expected_days)
        expected_trading_days = len(pd.bdate_range(start=start_date, end=end_date))
        
        # Calculate completeness
        completeness_pct = (total_days / expected_trading_days) * 100 if expected_trading_days > 0 else 0
        
        # Check for gaps (more than 5 days between consecutive dates)
        gaps = []
        if len(df) > 1:
            df_sorted = df.sort_index()
            dates = df_sorted.index
            
            for i in range(1, len(dates)):
                days_diff = (dates[i] - dates[i-1]).days
                # Flag gaps larger than 5 days (longer than typical weekend)
                if days_diff > 5:
                    gaps.append(f"Gap of {days_diff} days between {dates[i-1].date()} and {dates[i].date()}")
        
        missing_days = expected_trading_days - total_days
        has_gaps = len(gaps) > 0
        
        result = ValidationResult(
            ticker=ticker,
            total_days=total_days,
            missing_days=missing_days,
            completeness_pct=completeness_pct,
            has_gaps=has_gaps,
            gap_details=gaps
        )
        
        # Log validation results
        validation_msg = (
            f"{ticker} - Total: {total_days}, Missing: {missing_days}, "
            f"Completeness: {completeness_pct:.2f}%, Gaps: {len(gaps)}"
        )
        
        if result.is_valid:
            logger.info(f"VALID - {validation_msg}")
        else:
            logger.warning(f"INVALID - {validation_msg}")
            
        if gaps:
            for gap in gaps:
                logger.warning(f"{ticker} - {gap}")
        
        return result
    
    def _save_raw_csv(self, ticker: str, df: pd.DataFrame) -> None:
        """
        Save raw OHLCV data to CSV file.
        
        Args:
            ticker: Stock ticker symbol
            df: DataFrame with OHLCV data
        """
        output_path = self.raw_dir / f"{ticker}.csv"
        
        # Prepare DataFrame for CSV output
        df_out = df.copy()
        df_out.index.name = 'Date'
        df_out = df_out[['Open', 'High', 'Low', 'Close', 'Volume']]
        
        # Save to CSV
        df_out.to_csv(output_path)
        logger.debug(f"Saved raw CSV for {ticker} to {output_path}")
    
    def _save_normalized_parquet(
        self,
        all_data: List[Tuple[str, pd.DataFrame, Dict[str, str]]]
    ) -> None:
        """
        Save normalized parquet file combining all tickers.
        
        Args:
            all_data: List of tuples (ticker, dataframe, metadata_dict)
        """
        if not all_data:
            logger.warning("No data to save to normalized parquet")
            return
        
        combined_data = []
        
        for ticker, df, metadata in all_data:
            # Add ticker and metadata columns
            df_copy = df.copy()
            df_copy['ticker'] = ticker
            df_copy['fetch_timestamp'] = metadata['fetch_timestamp']
            df_copy['data_source'] = metadata['data_source']
            df_copy['validation_status'] = metadata['validation_status']
            
            # Reset index to make Date a column
            df_copy = df_copy.reset_index()
            # Handle index naming - ensure the date column is named 'Date'
            if 'index' in df_copy.columns:
                df_copy = df_copy.rename(columns={'index': 'Date'})
            
            combined_data.append(df_copy)
        
        # Combine all DataFrames
        combined_df = pd.concat(combined_data, ignore_index=True)
        
        # Reorder columns for better readability
        col_order = [
            'ticker', 'Date', 'Open', 'High', 'Low', 'Close', 'Volume',
            'fetch_timestamp', 'data_source', 'validation_status'
        ]
        combined_df = combined_df[col_order]
        
        # Save to parquet
        output_path = self.normalized_dir / "prices.parquet"
        combined_df.to_parquet(output_path, index=False, engine='pyarrow')
        logger.info(f"Saved normalized parquet with {len(combined_df)} rows to {output_path}")
    
    def ingest(self) -> IngestionMetrics:
        """
        Run the full ingestion process for all tickers in universe.
        
        Returns:
            IngestionMetrics with statistics about the ingestion run
        """
        metrics = IngestionMetrics()
        
        # Load universe
        try:
            universe = self.load_universe()
            metrics.total_tickers = len(universe)
        except Exception as e:
            logger.error(f"Failed to load universe: {e}")
            metrics.end_time = datetime.now()
            return metrics
        
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=self.lookback_days)
        
        logger.info(f"Starting ingestion for {metrics.total_tickers} tickers")
        logger.info(f"Date range: {start_date.date()} to {end_date.date()}")
        
        all_data = []
        
        for idx, ticker_info in enumerate(universe, 1):
            ticker = ticker_info['ticker'].upper().strip()
            sector = ticker_info.get('sector', 'Unknown')
            industry = ticker_info.get('industry', 'Unknown')
            
            logger.info(f"[{idx}/{metrics.total_tickers}] Processing {ticker} ({sector}/{industry})")
            
            # Fetch OHLCV data
            df = self._fetch_ohlcv_with_retry(ticker, start_date, end_date)
            
            if df is not None and not df.empty:
                # Validate data
                validation_result = self._validate_timeseries(
                    ticker, df, self.lookback_days
                )
                
                # Save raw CSV
                self._save_raw_csv(ticker, df)
                
                # Prepare metadata
                metadata = {
                    'fetch_timestamp': datetime.now().isoformat(),
                    'data_source': 'yfinance',
                    'validation_status': 'valid' if validation_result.is_valid else 'invalid'
                }
                
                # Add to combined data
                all_data.append((ticker, df, metadata))
                
                metrics.successful_tickers += 1
            else:
                metrics.failed_tickers += 1
            
            # Rate limiting
            if idx < metrics.total_tickers:  # Don't sleep after last ticker
                time.sleep(self.request_delay)
        
        # Save normalized parquet
        if all_data:
            self._save_normalized_parquet(all_data)
        
        metrics.end_time = datetime.now()
        
        return metrics
    
    def print_summary(self, metrics: IngestionMetrics) -> None:
        """
        Print a summary report of the ingestion run.
        
        Args:
            metrics: IngestionMetrics from ingestion run
        """
        print("\n" + "="*70)
        print("PRICE INGESTION SUMMARY")
        print("="*70)
        print(f"Total Tickers:      {metrics.total_tickers}")
        print(f"Successful:         {metrics.successful_tickers}")
        print(f"Failed:             {metrics.failed_tickers}")
        print(f"Success Rate:       {metrics.success_rate:.2f}%")
        print(f"Duration:           {metrics.duration_seconds:.2f} seconds")
        print(f"Raw CSVs:           {self.raw_dir}")
        print(f"Normalized Parquet: {self.normalized_dir / 'prices.parquet'}")
        print(f"Validation Log:     {self.validation_log_path}")
        print(f"Failures Log:       {self.failures_log_path}")
        print("="*70)


def main():
    """Main entry point for CLI execution."""
    parser = argparse.ArgumentParser(
        description="Ingest daily OHLCV price data for StockLighthouse universe"
    )
    parser.add_argument(
        '--universe',
        type=str,
        default='data/universe.csv',
        help='Path to universe CSV file (default: data/universe.csv)'
    )
    parser.add_argument(
        '--lookback-days',
        type=int,
        default=365,
        help='Number of days of historical data to fetch (default: 365)'
    )
    
    args = parser.parse_args()
    
    # Create ingestor and run
    ingestor = PriceIngestor(
        universe_path=args.universe,
        lookback_days=args.lookback_days
    )
    
    metrics = ingestor.ingest()
    ingestor.print_summary(metrics)


if __name__ == '__main__':
    main()
