/**
 * Unit tests for SearchBar component
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
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
    // For MUI Autocomplete, the placeholder is on the input element inside
    const inputElement = input.querySelector('input');
    expect(inputElement).toHaveAttribute('placeholder', expect.stringContaining('Search stocks'));
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

    const user = userEvent.setup();
    
    render(
      <BrowserRouter>
        <SearchBar />
      </BrowserRouter>
    );

    const input = screen.getByTestId('search-input').querySelector('input')!;
    await user.type(input, 'AAPL');

    await waitFor(() => {
      expect(screen.getByText('AAPL')).toBeInTheDocument();
    });

    expect(screen.getByText('Technology')).toBeInTheDocument();
  });

  it('does not display results when input is empty', () => {
    render(
      <BrowserRouter>
        <SearchBar />
      </BrowserRouter>
    );

    // Initially, no results should be displayed
    expect(screen.queryByText('AAPL')).not.toBeInTheDocument();
  });
});
