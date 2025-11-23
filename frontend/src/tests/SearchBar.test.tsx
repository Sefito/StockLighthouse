/**
 * Unit tests for SearchBar component
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { SearchBar } from '../components/SearchBar';
import * as api from '../services/api';

// Mock the API
vi.mock('../services/api');

const mockSearchStocks = vi.mocked(api.searchStocks);

describe('SearchBar', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders search input', () => {
    render(
      <BrowserRouter>
        <SearchBar />
      </BrowserRouter>
    );
    
    const input = screen.getByTestId('search-input');
    expect(input).toBeInTheDocument();
    expect(input).toHaveAttribute('placeholder', expect.stringContaining('Search stocks'));
  });

  it('displays search results when typing', async () => {
    const mockStocks = [
      {
        symbol: 'AAPL',
        price: 150.0,
        sector: 'Technology',
        previous_close: 148.0,
        change_pct: 1.35,
        market_cap: 2400000000000,
        pe_ratio: 28.5,
        pb_ratio: 40.2,
        dividend_yield: 0.005,
        market: 'us_market',
        exchange: 'NMS',
        currency: 'USD',
        industry: 'Consumer Electronics',
      },
    ];

    mockSearchStocks.mockResolvedValue(mockStocks);

    render(
      <BrowserRouter>
        <SearchBar />
      </BrowserRouter>
    );

    const input = screen.getByTestId('search-input');
    fireEvent.change(input, { target: { value: 'AAPL' } });

    await waitFor(() => {
      expect(screen.getByTestId('search-results')).toBeInTheDocument();
    });

    expect(screen.getByText('AAPL')).toBeInTheDocument();
    expect(screen.getByText('Technology')).toBeInTheDocument();
  });

  it('does not display results when input is empty', () => {
    render(
      <BrowserRouter>
        <SearchBar />
      </BrowserRouter>
    );

    const input = screen.getByTestId('search-input');
    fireEvent.change(input, { target: { value: '' } });

    expect(screen.queryByTestId('search-results')).not.toBeInTheDocument();
  });
});
