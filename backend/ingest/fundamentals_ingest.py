#!/usr/bin/env python3
"""
Production-ready fundamentals ingestion module for StockLighthouse.

This module fetches quarterly fundamental financial data for stocks in the
universe and saves them to normalized Parquet format.

Features:
- Fetch quarterly fundamentals from Yahoo Finance via yfinance
- Key metrics: revenue, net_income, eps, total_assets, total_debt, free_cash_flow, operating_margin
- Exponential backoff with configurable retries
- Comprehensive error handling and logging
- CLI interface for easy execution

Usage:
    python backend/ingest/fundamentals_ingest.py [--universe PATH]

Example:
    python backend/ingest/fundamentals_ingest.py --universe data/universe.csv
"""

import argparse
import csv
import json
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
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
class FundamentalsMetrics:
    """Metrics for fundamentals ingestion run."""
    total_tickers: int = 0
    successful_tickers: int = 0
    failed_tickers: int = 0
    total_quarters: int = 0
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


class FundamentalsIngestor:
    """
    Production-ready fundamentals data ingestor.
    
    Fetches quarterly fundamental financial data from Yahoo Finance and stores
    in normalized Parquet format.
    
    Attributes:
        universe_path: Path to universe CSV file
        raw_dir: Directory for raw fundamentals data
        normalized_dir: Directory for normalized Parquet files
        max_retries: Maximum retry attempts
        initial_backoff: Initial backoff time in seconds
        backoff_multiplier: Multiplier for exponential backoff
        request_delay: Delay between requests in seconds
    """
    
    def __init__(
        self,
        universe_path: str = "data/universe.csv",
        raw_dir: str = "data/raw/fundamentals",
        normalized_dir: str = "data/normalized",
        max_retries: int = 3,
        initial_backoff: float = 1.0,
        backoff_multiplier: float = 2.0,
        request_delay: float = 0.1,
    ):
        """
        Initialize the fundamentals ingestor.
        
        Args:
            universe_path: Path to universe CSV file with ticker,sector,industry columns
            raw_dir: Directory for raw fundamentals data and logs
            normalized_dir: Directory to store normalized parquet file
            max_retries: Maximum number of retry attempts on failure
            initial_backoff: Initial backoff time in seconds for retries
            backoff_multiplier: Multiplier for exponential backoff
            request_delay: Delay between requests to respect rate limits
        """
        self.universe_path = Path(universe_path)
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
        self.failures_log_path = self.raw_dir / "failures.log"
        
        # Setup file handler for failures log
        self._setup_file_logging()
    
    def _setup_file_logging(self) -> None:
        """Setup file handler for failure logs."""
        # Remove existing FileHandler instances to avoid duplicates
        logger.handlers = [h for h in logger.handlers 
                          if not isinstance(h, logging.FileHandler)]
        
        failure_handler = logging.FileHandler(self.failures_log_path, mode='a')
        failure_handler.setLevel(logging.ERROR)
        failure_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(message)s'
        ))
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
    
    def _extract_metrics(
        self,
        ticker: str,
        quarterly_financials: pd.DataFrame,
        quarterly_balance_sheet: pd.DataFrame,
        quarterly_cashflow: pd.DataFrame
    ) -> List[Dict[str, Any]]:
        """
        Extract key metrics from quarterly financial statements.
        
        Args:
            ticker: Stock ticker symbol
            quarterly_financials: Quarterly income statement
            quarterly_balance_sheet: Quarterly balance sheet
            quarterly_cashflow: Quarterly cash flow statement
            
        Returns:
            List of dicts with quarterly metrics
        """
        quarters_data = []
        
        # Get all available dates (union of dates from all statements)
        all_dates = set()
        if not quarterly_financials.empty:
            all_dates.update(quarterly_financials.columns)
        if not quarterly_balance_sheet.empty:
            all_dates.update(quarterly_balance_sheet.columns)
        if not quarterly_cashflow.empty:
            all_dates.update(quarterly_cashflow.columns)
        
        # Sort dates in descending order (most recent first)
        sorted_dates = sorted(all_dates, reverse=True)
        
        for date in sorted_dates:
            try:
                # Convert timestamp to datetime
                if isinstance(date, pd.Timestamp):
                    report_date = date.to_pydatetime()
                else:
                    report_date = pd.to_datetime(date)
                
                # Determine quarter and fiscal year
                quarter = f"Q{(report_date.month - 1) // 3 + 1}"
                fiscal_year = report_date.year
                
                # Extract metrics with safe access
                metrics = {}
                
                # Income statement metrics
                if date in quarterly_financials.columns:
                    try:
                        metrics['revenue'] = self._safe_get_value(
                            quarterly_financials, 'Total Revenue', date
                        )
                        metrics['net_income'] = self._safe_get_value(
                            quarterly_financials, 'Net Income', date
                        )
                        # EPS extraction - try direct field first, then calculate
                        eps = self._safe_get_value(quarterly_financials, 'Basic EPS', date)
                        if eps is None:
                            eps = self._safe_get_value(quarterly_financials, 'Diluted EPS', date)
                        metrics['eps'] = eps
                        
                        # Operating margin calculation
                        revenue = self._safe_get_value(quarterly_financials, 'Total Revenue', date)
                        operating_income = self._safe_get_value(quarterly_financials, 'Operating Income', date)
                        if revenue and operating_income and revenue != 0:
                            metrics['operating_margin'] = operating_income / revenue
                    except Exception as e:
                        logger.debug(f"{ticker} - Error extracting income statement metrics: {e}")
                
                # Balance sheet metrics
                if date in quarterly_balance_sheet.columns:
                    try:
                        metrics['total_assets'] = self._safe_get_value(
                            quarterly_balance_sheet, 'Total Assets', date
                        )
                        metrics['total_debt'] = self._safe_get_value(
                            quarterly_balance_sheet, 'Total Debt', date
                        )
                    except Exception as e:
                        logger.debug(f"{ticker} - Error extracting balance sheet metrics: {e}")
                
                # Cash flow metrics
                if date in quarterly_cashflow.columns:
                    try:
                        metrics['free_cash_flow'] = self._safe_get_value(
                            quarterly_cashflow, 'Free Cash Flow', date
                        )
                    except Exception as e:
                        logger.debug(f"{ticker} - Error extracting cash flow metrics: {e}")
                
                # Only add if we have at least some metrics
                if metrics:
                    quarters_data.append({
                        'ticker': ticker,
                        'report_date': report_date.strftime('%Y-%m-%d'),
                        'period': quarter,
                        'fiscal_year': fiscal_year,
                        'metrics': metrics
                    })
            
            except Exception as e:
                logger.exception(f"{ticker} - Error processing date {date}: {e}")
                continue
        
        return quarters_data
    
    def _safe_get_value(
        self,
        df: pd.DataFrame,
        row_name: str,
        column: Any
    ) -> Optional[float]:
        """
        Safely get a value from DataFrame.
        
        Args:
            df: DataFrame to get value from
            row_name: Row name/index
            column: Column name
            
        Returns:
            Float value or None if not available
        """
        try:
            if row_name in df.index and column in df.columns:
                value = df.loc[row_name, column]
                if pd.notna(value):
                    return float(value)
        except Exception as e:
            logging.debug(f"Exception in _safe_get_value for row '{row_name}', column '{column}': {e}")
        return None
    
    def _fetch_fundamentals_with_retry(
        self,
        ticker: str
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Fetch fundamental data with exponential backoff retry logic.
        
        Args:
            ticker: Stock ticker symbol
            
        Returns:
            List of quarterly fundamentals dicts or None on failure
        """
        backoff = self.initial_backoff
        last_error = None
        
        for attempt in range(self.max_retries):
            try:
                logger.debug(f"Fetching fundamentals for {ticker} (attempt {attempt + 1}/{self.max_retries})")
                
                # Fetch data from yfinance
                ticker_obj = yf.Ticker(ticker)
                
                # Get quarterly financial statements
                quarterly_financials = ticker_obj.quarterly_financials
                quarterly_balance_sheet = ticker_obj.quarterly_balance_sheet
                quarterly_cashflow = ticker_obj.quarterly_cashflow
                
                # Check if we have any data
                has_data = (
                    (quarterly_financials is not None and not quarterly_financials.empty) or
                    (quarterly_balance_sheet is not None and not quarterly_balance_sheet.empty) or
                    (quarterly_cashflow is not None and not quarterly_cashflow.empty)
                )
                
                if has_data:
                    # Extract metrics
                    quarters_data = self._extract_metrics(
                        ticker,
                        quarterly_financials if quarterly_financials is not None else pd.DataFrame(),
                        quarterly_balance_sheet if quarterly_balance_sheet is not None else pd.DataFrame(),
                        quarterly_cashflow if quarterly_cashflow is not None else pd.DataFrame()
                    )
                    
                    if quarters_data:
                        logger.info(f"Successfully fetched {len(quarters_data)} quarters for {ticker}")
                        return quarters_data
                    else:
                        last_error = "No metrics could be extracted"
                        logger.warning(f"{ticker}: {last_error}")
                else:
                    last_error = "No quarterly data available"
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
    
    def _save_normalized_parquet(
        self,
        all_data: List[Dict[str, Any]]
    ) -> None:
        """
        Save normalized parquet file combining all fundamentals data.
        
        Args:
            all_data: List of fundamentals records
        """
        if not all_data:
            logger.warning("No data to save to normalized parquet")
            return
        
        # Convert to DataFrame
        # Need to handle the nested metrics dict
        records = []
        for record in all_data:
            flat_record = {
                'ticker': record['ticker'],
                'report_date': record['report_date'],
                'period': record['period'],
                'fiscal_year': record['fiscal_year'],
                'fetch_timestamp': record['fetch_timestamp'],
                'data_source': record['data_source'],
            }
            
            # Flatten metrics
            metrics = record['metrics']
            flat_record['revenue'] = metrics.get('revenue')
            flat_record['net_income'] = metrics.get('net_income')
            flat_record['eps'] = metrics.get('eps')
            flat_record['total_assets'] = metrics.get('total_assets')
            flat_record['total_debt'] = metrics.get('total_debt')
            flat_record['free_cash_flow'] = metrics.get('free_cash_flow')
            flat_record['operating_margin'] = metrics.get('operating_margin')
            
            # Store original metrics as JSON string for reference
            flat_record['metrics_json'] = json.dumps(metrics)
            
            records.append(flat_record)
        
        df = pd.DataFrame(records)
        
        # Save to parquet
        output_path = self.normalized_dir / "fundamentals.parquet"
        df.to_parquet(output_path, index=False, engine='pyarrow')
        logger.info(f"Saved normalized parquet with {len(df)} quarters to {output_path}")
    
    def ingest(self) -> FundamentalsMetrics:
        """
        Run the full fundamentals ingestion process.
        
        Returns:
            FundamentalsMetrics with statistics about the ingestion run
        """
        metrics = FundamentalsMetrics()
        
        # Load universe
        try:
            universe = self.load_universe()
            metrics.total_tickers = len(universe)
        except Exception as e:
            logger.error(f"Failed to load universe: {e}")
            metrics.end_time = datetime.now()
            return metrics
        
        logger.info(f"Starting fundamentals ingestion for {metrics.total_tickers} tickers")
        
        all_data = []
        
        for idx, ticker_info in enumerate(universe, 1):
            ticker = ticker_info['ticker'].upper().strip()
            sector = ticker_info.get('sector', 'Unknown')
            industry = ticker_info.get('industry', 'Unknown')
            
            logger.info(f"[{idx}/{metrics.total_tickers}] Processing {ticker} ({sector}/{industry})")
            
            # Fetch fundamentals
            quarters_data = self._fetch_fundamentals_with_retry(ticker)
            
            if quarters_data:
                # Add metadata to each quarter record
                fetch_timestamp = datetime.now().isoformat()
                for quarter_record in quarters_data:
                    quarter_record['fetch_timestamp'] = fetch_timestamp
                    quarter_record['data_source'] = 'yfinance'
                    all_data.append(quarter_record)
                
                metrics.successful_tickers += 1
                metrics.total_quarters += len(quarters_data)
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
    
    def print_summary(self, metrics: FundamentalsMetrics) -> None:
        """
        Print a summary report of the ingestion run.
        
        Args:
            metrics: FundamentalsMetrics from ingestion run
        """
        print("\n" + "="*70)
        print("FUNDAMENTALS INGESTION SUMMARY")
        print("="*70)
        print(f"Total Tickers:      {metrics.total_tickers}")
        print(f"Successful:         {metrics.successful_tickers}")
        print(f"Failed:             {metrics.failed_tickers}")
        print(f"Total Quarters:     {metrics.total_quarters}")
        print(f"Success Rate:       {metrics.success_rate:.2f}%")
        print(f"Duration:           {metrics.duration_seconds:.2f} seconds")
        print(f"Normalized Parquet: {self.normalized_dir / 'fundamentals.parquet'}")
        print(f"Failures Log:       {self.failures_log_path}")
        print("="*70)


def main():
    """Main entry point for CLI execution."""
    parser = argparse.ArgumentParser(
        description="Ingest quarterly fundamentals data for StockLighthouse universe"
    )
    parser.add_argument(
        '--universe',
        type=str,
        default='data/universe.csv',
        help='Path to universe CSV file (default: data/universe.csv)'
    )
    
    args = parser.parse_args()
    
    # Create ingestor and run
    ingestor = FundamentalsIngestor(
        universe_path=args.universe
    )
    
    metrics = ingestor.ingest()
    ingestor.print_summary(metrics)


if __name__ == '__main__':
    main()
