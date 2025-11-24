"""
Scoring service for StockLighthouse.

This service orchestrates the complete scoring pipeline:
1. Load feature data and configuration
2. Apply rule-based filters
3. Normalize features
4. Compute technical and fundamental scores
5. Combine into composite score
6. Generate explanations for top candidates
7. Save results to parquet and Redis
"""

import json
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

import numpy as np
import pandas as pd
import yaml

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from scoring.sample_scoring import (
    normalize_minmax,
    normalize_zscore,
    compute_weighted_score,
    apply_filters,
    get_top_k_with_explanations,
    create_explanation_text,
)


class ScoringService:
    """
    Main scoring service that orchestrates the scoring pipeline.
    """
    
    def __init__(self, config_path: str = "config/scoring.yaml"):
        """
        Initialize the scoring service.
        
        Args:
            config_path: Path to scoring configuration YAML file
        """
        self.config = self._load_config(config_path)
        self.redis_client = None  # Will be initialized when needed
        
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        return config
    
    def _get_redis_client(self):
        """
        Lazy initialization of Redis client.
        
        Returns None if Redis is not available (graceful degradation).
        """
        if self.redis_client is None:
            try:
                import redis
                self.redis_client = redis.Redis(
                    host='redis',
                    port=6379,
                    decode_responses=True
                )
                # Test connection
                self.redis_client.ping()
                print("✓ Connected to Redis")
            except Exception as e:
                print(f"⚠ Redis not available: {e}. Continuing without caching.")
                self.redis_client = False  # Mark as unavailable
        
        return self.redis_client if self.redis_client else None
    
    def load_features(self, features_path: str) -> pd.DataFrame:
        """
        Load feature data from parquet file.
        
        Args:
            features_path: Path to daily_features.parquet
            
        Returns:
            DataFrame with feature data
        """
        print(f"Loading features from {features_path}...")
        df = pd.read_parquet(features_path)
        print(f"✓ Loaded {len(df)} tickers with {len(df.columns)} columns")
        return df
    
    def load_fundamentals(self, fundamentals_path: Optional[str] = None) -> Optional[pd.DataFrame]:
        """
        Load latest fundamentals snapshot.
        
        Args:
            fundamentals_path: Path to fundamentals parquet file
            
        Returns:
            DataFrame with fundamentals or None if not available
        """
        if fundamentals_path is None:
            return None
            
        try:
            print(f"Loading fundamentals from {fundamentals_path}...")
            df = pd.read_parquet(fundamentals_path)
            print(f"✓ Loaded fundamentals for {len(df)} tickers")
            return df
        except Exception as e:
            print(f"⚠ Could not load fundamentals: {e}")
            return None
    
    def apply_rule_filters(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Apply rule-based filters from config.
        
        Args:
            df: DataFrame with stock data
            
        Returns:
            Filtered DataFrame
        """
        filters = self.config.get('filters', {})
        
        print("\nApplying filters...")
        filtered = apply_filters(
            df,
            min_market_cap=filters.get('min_market_cap'),
            min_avg_volume=filters.get('min_avg_volume'),
            min_price=filters.get('min_price'),
            max_pe_ratio=filters.get('max_pe_ratio'),
            tradable_exchanges=filters.get('tradable_exchanges')
        )
        
        return filtered
    
    def normalize_features(self, df: pd.DataFrame, feature_list: List[str]) -> pd.DataFrame:
        """
        Normalize specified features in DataFrame.
        
        Args:
            df: DataFrame with raw features
            feature_list: List of feature column names to normalize
            
        Returns:
            DataFrame with normalized features (original features prefixed with 'norm_')
        """
        result = df.copy()
        
        scoring_config = self.config.get('scoring', {})
        method = scoring_config.get('normalization_method', 'zscore')
        outlier_threshold = scoring_config.get('outlier_threshold', 3.0)
        
        print(f"\nNormalizing features using {method} method...")
        
        for feature in feature_list:
            if feature not in df.columns:
                print(f"⚠ Feature '{feature}' not found, skipping")
                continue
            
            values = df[feature].values
            
            # Normalize based on method
            if method == 'minmax':
                normalized = normalize_minmax(values)
            else:  # zscore
                normalized = normalize_zscore(values, clip_threshold=outlier_threshold)
                # Convert z-scores to [0, 1] range for consistency
                # Map [-3, 3] -> [0, 1]
                normalized = (normalized + outlier_threshold) / (2 * outlier_threshold)
                normalized = np.clip(normalized, 0, 1)
            
            result[f'norm_{feature}'] = normalized
        
        print(f"✓ Normalized {len(feature_list)} features")
        return result
    
    def compute_technical_score(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Compute technical score from normalized technical features.
        
        Args:
            df: DataFrame with normalized technical features
            
        Returns:
            DataFrame with 'tech_score' column added
        """
        tech_config = self.config.get('technical_features', {})
        
        # Extract weights and feature names
        weights = {}
        invert_features = []
        
        for feature_name, feature_config in tech_config.items():
            weight = feature_config.get('weight', 0)
            weights[f'norm_{feature_name}'] = weight
            
            # Check if feature should be inverted (direction: negative)
            direction = feature_config.get('direction', 'positive')
            if direction == 'negative':
                invert_features.append(f'norm_{feature_name}')
        
        # Prepare features dictionary
        features = {}
        for feature_name in weights.keys():
            if feature_name in df.columns:
                features[feature_name] = df[feature_name].values
        
        if not features:
            print("⚠ No technical features found, setting tech_score to 0")
            df['tech_score'] = 0.0
            return df
        
        # Compute weighted score
        print(f"\nComputing technical score from {len(features)} features...")
        tech_score = compute_weighted_score(features, weights, invert_features)
        df['tech_score'] = tech_score
        
        print(f"✓ Technical score range: [{tech_score.min():.3f}, {tech_score.max():.3f}], "
              f"mean: {tech_score.mean():.3f}")
        
        return df
    
    def compute_fundamental_score(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Compute fundamental score from normalized fundamental features.
        
        Args:
            df: DataFrame with normalized fundamental features
            
        Returns:
            DataFrame with 'fund_score' column added
        """
        fund_config = self.config.get('fundamental_features', {})
        
        # Extract weights and feature names
        weights = {}
        invert_features = []
        
        for feature_name, feature_config in fund_config.items():
            weight = feature_config.get('weight', 0)
            weights[f'norm_{feature_name}'] = weight
            
            # Check if feature should be inverted (direction: negative)
            direction = feature_config.get('direction', 'positive')
            if direction == 'negative':
                invert_features.append(f'norm_{feature_name}')
        
        # Prepare features dictionary
        features = {}
        for feature_name in weights.keys():
            if feature_name in df.columns:
                features[feature_name] = df[feature_name].values
        
        if not features:
            print("⚠ No fundamental features found, setting fund_score to 0")
            df['fund_score'] = 0.0
            return df
        
        # Compute weighted score
        print(f"\nComputing fundamental score from {len(features)} features...")
        fund_score = compute_weighted_score(features, weights, invert_features)
        df['fund_score'] = fund_score
        
        print(f"✓ Fundamental score range: [{fund_score.min():.3f}, {fund_score.max():.3f}], "
              f"mean: {fund_score.mean():.3f}")
        
        return df
    
    def compute_composite_score(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Compute composite score from technical and fundamental scores.
        
        Args:
            df: DataFrame with tech_score and fund_score columns
            
        Returns:
            DataFrame with 'composite_score' column added
        """
        weights = self.config.get('composite_weights', {})
        w_tech = weights.get('technical', 0.6)
        w_fund = weights.get('fundamental', 0.4)
        
        print(f"\nComputing composite score (tech: {w_tech}, fund: {w_fund})...")
        
        df['composite_score'] = (
            w_tech * df['tech_score'] + 
            w_fund * df['fund_score']
        )
        
        composite = df['composite_score']
        print(f"✓ Composite score range: [{composite.min():.3f}, {composite.max():.3f}], "
              f"mean: {composite.mean():.3f}")
        
        return df
    
    def generate_explanations(
        self,
        df: pd.DataFrame,
        top_k: int = 100
    ) -> Dict[str, Any]:
        """
        Generate explanations for top K candidates.
        
        Args:
            df: DataFrame with scores and features
            top_k: Number of top candidates to explain
            
        Returns:
            Dictionary with explanations for each ticker
        """
        print(f"\nGenerating explanations for top {top_k} candidates...")
        
        # Get top K by composite score
        top_df = df.nlargest(top_k, 'composite_score')
        
        # Collect all feature columns
        tech_features = [f'norm_{k}' for k in self.config.get('technical_features', {}).keys()]
        fund_features = [f'norm_{k}' for k in self.config.get('fundamental_features', {}).keys()]
        all_features = tech_features + fund_features
        
        # Available features in df
        available_features = [f for f in all_features if f in df.columns]
        
        explanations = {}
        for _, row in top_df.iterrows():
            symbol = row.get('symbol', 'Unknown')
            
            # Compute per-feature contributions
            contributions = {}
            for feature in available_features:
                if pd.notna(row.get(feature)):
                    contributions[feature] = float(row[feature])
            
            # Create explanation text
            explanation_text = create_explanation_text(row, available_features, top_n_features=5)
            
            explanations[symbol] = {
                'composite_score': float(row.get('composite_score', 0)),
                'tech_score': float(row.get('tech_score', 0)),
                'fund_score': float(row.get('fund_score', 0)),
                'contributions': contributions,
                'explanation': explanation_text
            }
        
        print(f"✓ Generated explanations for {len(explanations)} tickers")
        return explanations
    
    def save_results(
        self,
        df: pd.DataFrame,
        explanations: Dict[str, Any],
        date_str: Optional[str] = None
    ) -> None:
        """
        Save scoring results to parquet and JSON files.
        
        Args:
            df: DataFrame with all scores
            explanations: Dictionary of explanations
            date_str: Date string (default: today's date)
        """
        if date_str is None:
            date_str = datetime.now().strftime('%Y-%m-%d')
        
        # Create output directories
        ranks_dir = Path('data/ranks')
        ranks_dir.mkdir(parents=True, exist_ok=True)
        
        # Save ranks parquet
        ranks_path = ranks_dir / f'{date_str}_ranks.parquet'
        print(f"\nSaving ranks to {ranks_path}...")
        df.to_parquet(ranks_path, index=False)
        print(f"✓ Saved {len(df)} ranked stocks")
        
        # Save explanations JSON
        explanations_path = ranks_dir / f'{date_str}_explanations.json'
        print(f"Saving explanations to {explanations_path}...")
        with open(explanations_path, 'w') as f:
            json.dump(explanations, f, indent=2)
        print(f"✓ Saved explanations for {len(explanations)} stocks")
    
    def save_to_redis(self, df: pd.DataFrame, top_n: int = 50) -> None:
        """
        Save top N candidates to Redis.
        
        Args:
            df: DataFrame with scores
            top_n: Number of top candidates to cache
        """
        redis_client = self._get_redis_client()
        if redis_client is None:
            print("⚠ Redis not available, skipping cache")
            return
        
        # Get top N
        top_df = df.nlargest(top_n, 'composite_score')
        
        # Prepare data for Redis
        top_candidates = []
        for _, row in top_df.iterrows():
            candidate = {
                'symbol': row.get('symbol', 'Unknown'),
                'composite_score': float(row.get('composite_score', 0)),
                'tech_score': float(row.get('tech_score', 0)),
                'fund_score': float(row.get('fund_score', 0)),
            }
            top_candidates.append(candidate)
        
        # Save to Redis
        redis_config = self.config.get('top_candidates', {})
        redis_key = redis_config.get('redis_key', 'top_candidates/daily')
        redis_ttl = redis_config.get('redis_ttl', 86400)
        
        print(f"\nSaving top {top_n} to Redis key '{redis_key}'...")
        try:
            redis_client.setex(
                redis_key,
                redis_ttl,
                json.dumps(top_candidates)
            )
            print(f"✓ Cached top {top_n} candidates (TTL: {redis_ttl}s)")
        except Exception as e:
            print(f"⚠ Failed to save to Redis: {e}")
    
    def run_scoring_pipeline(
        self,
        features_path: str,
        fundamentals_path: Optional[str] = None,
        date_str: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Run the complete scoring pipeline.
        
        Args:
            features_path: Path to daily_features.parquet
            fundamentals_path: Optional path to fundamentals parquet
            date_str: Date string for output files (default: today)
            
        Returns:
            DataFrame with all scores and rankings
        """
        start_time = time.time()
        
        print("=" * 70)
        print("StockLighthouse Scoring Pipeline")
        print("=" * 70)
        
        # Load data
        df = self.load_features(features_path)
        initial_count = len(df)
        
        # Optionally merge fundamentals
        if fundamentals_path:
            fund_df = self.load_fundamentals(fundamentals_path)
            if fund_df is not None:
                df = df.merge(fund_df, on='symbol', how='left')
        
        # Apply filters
        df = self.apply_rule_filters(df)
        print(f"✓ {len(df)}/{initial_count} tickers passed filters")
        
        # Get feature lists
        tech_features = list(self.config.get('technical_features', {}).keys())
        fund_features = list(self.config.get('fundamental_features', {}).keys())
        all_features = tech_features + fund_features
        
        # Normalize features
        df = self.normalize_features(df, all_features)
        
        # Compute scores
        df = self.compute_technical_score(df)
        df = self.compute_fundamental_score(df)
        df = self.compute_composite_score(df)
        
        # Generate explanations for top candidates
        top_k = self.config.get('top_candidates', {}).get('top_k', 100)
        explanations = self.generate_explanations(df, top_k=top_k)
        
        # Save results
        self.save_results(df, explanations, date_str)
        
        # Save to Redis
        save_top_n = self.config.get('top_candidates', {}).get('save_top_n', 50)
        self.save_to_redis(df, top_n=save_top_n)
        
        # Report timing
        elapsed = time.time() - start_time
        sla_target = self.config.get('sla', {}).get('max_runtime_seconds', 120)
        
        print("\n" + "=" * 70)
        print(f"✓ Pipeline completed in {elapsed:.2f} seconds")
        
        if elapsed <= sla_target:
            print(f"✓ Met SLA target ({sla_target}s)")
        else:
            print(f"⚠ Exceeded SLA target ({elapsed:.2f}s > {sla_target}s)")
        
        print("=" * 70)
        
        return df


def main():
    """
    Main entry point for running the scoring pipeline.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='Run StockLighthouse scoring pipeline')
    parser.add_argument(
        '--features',
        default='data/features/daily_features.parquet',
        help='Path to daily features parquet file'
    )
    parser.add_argument(
        '--fundamentals',
        default=None,
        help='Path to fundamentals parquet file (optional)'
    )
    parser.add_argument(
        '--date',
        default=None,
        help='Date string for output files (default: today)'
    )
    parser.add_argument(
        '--config',
        default='config/scoring.yaml',
        help='Path to scoring config file'
    )
    
    args = parser.parse_args()
    
    # Run pipeline
    service = ScoringService(config_path=args.config)
    result_df = service.run_scoring_pipeline(
        features_path=args.features,
        fundamentals_path=args.fundamentals,
        date_str=args.date
    )
    
    print(f"\n✓ Scored {len(result_df)} tickers")
    print(f"Top 10 candidates:")
    print(result_df.nlargest(10, 'composite_score')[
        ['symbol', 'composite_score', 'tech_score', 'fund_score']
    ].to_string(index=False))


if __name__ == '__main__':
    main()
