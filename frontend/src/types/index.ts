/**
 * Type definitions for StockLighthouse API
 */

export interface Stock {
  symbol: string;
  price: number | null;
  previous_close: number | null;
  change_pct: number | null;
  market_cap: number | null;
  pe_ratio: number | null;
  pb_ratio: number | null;
  dividend_yield: number | null;
  sector: string | null;
  market: string | null;
  exchange: string | null;
  currency: string | null;
  industry: string | null;
}

export interface SectorSummary {
  sector: string;
  count: number;
  median_pe: number | null;
  median_pb: number | null;
  median_market_cap: number | null;
  avg_dividend_yield: number | null;
  weighted_avg_pe: number | null;
  top_tickers: Array<{
    symbol: string;
    market_cap: number | null;
  }>;
}

export interface HistoryData {
  symbol: string;
  dates: string[];
  prices: number[];
}

export interface PEDistribution {
  symbol: string;
  sector: string | null;
  pe_ratios: number[];
  symbols: string[];
  current_pe: number | null;
}
