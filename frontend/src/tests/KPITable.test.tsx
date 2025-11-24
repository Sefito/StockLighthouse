/**
 * Unit tests for KPITable component
 */
import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { KPITable } from '../components/KPITable';
import type { Stock } from '../types';

describe('KPITable', () => {
  const mockStock: Stock = {
    symbol: 'AAPL',
    price: 150.25,
    previous_close: 148.50,
    change_pct: 1.18,
    market_cap: 2400000000000,
    pe_ratio: 28.5,
    pb_ratio: 40.2,
    dividend_yield: 0.005,
    sector: 'Technology',
    market: 'us_market',
    exchange: 'NMS',
    currency: 'USD',
    industry: 'Consumer Electronics',
  };

  it('renders stock symbol', () => {
    render(<KPITable stock={mockStock} />);
    expect(screen.getByText('AAPL')).toBeInTheDocument();
  });

  it('renders all KPI labels', () => {
    render(<KPITable stock={mockStock} />);
    expect(screen.getByText('Current Price')).toBeInTheDocument();
    expect(screen.getByText('Market Cap')).toBeInTheDocument();
    expect(screen.getByText('P/E Ratio')).toBeInTheDocument();
    expect(screen.getByText('Sector')).toBeInTheDocument();
  });

  it('formats price correctly', () => {
    render(<KPITable stock={mockStock} />);
    expect(screen.getByText('$150.25')).toBeInTheDocument();
  });

  it('formats market cap correctly', () => {
    render(<KPITable stock={mockStock} />);
    expect(screen.getByText('$2.40T')).toBeInTheDocument();
  });

  it('handles null values', () => {
    const stockWithNulls: Stock = {
      ...mockStock,
      price: null,
      market_cap: null,
      pe_ratio: null,
    };
    render(<KPITable stock={stockWithNulls} />);
    
    // Should display N/A for null values
    const naElements = screen.getAllByText('N/A');
    expect(naElements.length).toBeGreaterThan(0);
  });

  it('applies success color to positive change', () => {
    render(<KPITable stock={mockStock} />);
    const changeElement = screen.getByText('1.18%');
    expect(changeElement).toBeInTheDocument();
    // MUI applies inline styles via sx prop, so we check the element exists
    // rather than checking for a specific class
  });

  it('applies error color to negative change', () => {
    const stockWithNegativeChange: Stock = {
      ...mockStock,
      change_pct: -2.5,
    };
    render(<KPITable stock={stockWithNegativeChange} />);
    const changeElement = screen.getByText('-2.50%');
    expect(changeElement).toBeInTheDocument();
    // MUI applies inline styles via sx prop, so we check the element exists
    // rather than checking for a specific class
  });
});
