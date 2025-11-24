/**
 * API service for StockLighthouse
 */
import type { Stock, SectorSummary, HistoryData, PEDistribution } from '../types';

// Use environment variable for API base URL, fallback to /api for local dev with Vite proxy
const API_BASE = import.meta.env.VITE_API_BASE_URL || '/api';

/**
 * Search for stocks by query
 */
export async function searchStocks(query: string = ''): Promise<Stock[]> {
  const response = await fetch(`${API_BASE}/stocks/search?q=${encodeURIComponent(query)}`);
  if (!response.ok) {
    throw new Error(`Failed to search stocks: ${response.statusText}`);
  }
  return response.json();
}

/**
 * Get details for a specific stock
 */
export async function getStockDetails(symbol: string): Promise<Stock> {
  const response = await fetch(`${API_BASE}/stocks/${encodeURIComponent(symbol)}`);
  if (!response.ok) {
    throw new Error(`Failed to get stock details: ${response.statusText}`);
  }
  return response.json();
}

/**
 * Get historical price data for a stock
 */
export async function getStockHistory(symbol: string): Promise<HistoryData> {
  const response = await fetch(`${API_BASE}/stocks/${encodeURIComponent(symbol)}/history`);
  if (!response.ok) {
    throw new Error(`Failed to get stock history: ${response.statusText}`);
  }
  return response.json();
}

/**
 * Get P/E distribution for a stock's sector
 */
export async function getPEDistribution(symbol: string): Promise<PEDistribution> {
  const response = await fetch(`${API_BASE}/stocks/${encodeURIComponent(symbol)}/pe-distribution`);
  if (!response.ok) {
    throw new Error(`Failed to get P/E distribution: ${response.statusText}`);
  }
  return response.json();
}

/**
 * Get all sector summaries
 */
export async function getSectors(): Promise<SectorSummary[]> {
  const response = await fetch(`${API_BASE}/sectors`);
  if (!response.ok) {
    throw new Error(`Failed to get sectors: ${response.statusText}`);
  }
  return response.json();
}

/**
 * Get details for a specific sector
 */
export async function getSectorDetails(sectorName: string): Promise<{
  sector: string;
  summary: SectorSummary;
  stocks: Stock[];
}> {
  const response = await fetch(`${API_BASE}/sectors/${encodeURIComponent(sectorName)}`);
  if (!response.ok) {
    throw new Error(`Failed to get sector details: ${response.statusText}`);
  }
  return response.json();
}
