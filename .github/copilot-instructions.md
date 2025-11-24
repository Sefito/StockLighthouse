# GitHub Copilot Instructions for StockLighthouse

This document provides GitHub Copilot with context about the StockLighthouse project architecture, coding standards, and best practices to help generate consistent, high-quality code suggestions.

## Project Overview

StockLighthouse is a comprehensive stock data ingestion, normalization, and analysis platform with a modern web interface. It follows a three-tier architecture with Python backend (FastAPI) and React TypeScript frontend.

### Core Components

1. **YFinance Ingestor** (`backend/src/stocklighthouse/ingest/`) - Fetches raw stock data with retry logic and caching
2. **Normalizer** (`backend/src/stocklighthouse/normalizer.py`) - Converts raw data to canonical StockKPIs schema
3. **Analyzer** (`backend/src/stocklighthouse/analyzer.py`) - Performs sector aggregation and statistical analysis
4. **Scoring Pipeline** (`backend/scoring/`) - Computes composite buy scores from technical and fundamental indicators
5. **REST API** (`backend/src/stocklighthouse/api/`) - FastAPI-based RESTful endpoints
6. **Frontend** (`frontend/src/`) - React 19 + TypeScript UI with interactive charts

## Technology Stack

### Backend
- **Python 3.10+** with type hints
- **FastAPI** for REST API
- **Pydantic 2.0+** for data validation
- **yfinance** for stock data fetching
- **pytest** for testing (with pytest-mock, pytest-cov)
- **pandas** and **pyarrow** for data processing

### Frontend
- **React 19** with hooks and functional components
- **TypeScript 5.9+** with strict mode
- **Vite 7** for build tooling
- **React Router 7** for navigation
- **Plotly.js** for interactive charts
- **Vitest** for unit testing
- **Playwright** for E2E testing

## Python Coding Standards

### Style and Type Safety

- **Always use type hints** for function signatures, including return types
- Follow **PEP 8** style guidelines
- Use **Pydantic models** for all data structures requiring validation
- Prefer **defensive programming** with explicit None checks and safe conversions

```python
# Good: Type hints, defensive parsing, clear naming
def calculate_weighted_average_pe(
    stocks: list[StockKPIs],
    min_pe: float = 0.0,
    max_pe: float = 100.0
) -> float | None:
    """
    Calculate market-cap weighted average P/E ratio.
    
    Args:
        stocks: List of stock KPI objects
        min_pe: Minimum valid P/E ratio (default: 0.0)
        max_pe: Maximum valid P/E ratio (default: 100.0)
        
    Returns:
        Weighted average P/E or None if insufficient data
    """
    valid_stocks = [
        s for s in stocks 
        if s.pe_ratio is not None 
        and s.market_cap is not None
        and min_pe <= s.pe_ratio <= max_pe
    ]
    
    if not valid_stocks:
        return None
    
    total_market_cap = sum(s.market_cap for s in valid_stocks)
    if total_market_cap == 0:
        return None
    
    weighted_sum = sum(
        s.pe_ratio * s.market_cap 
        for s in valid_stocks
    )
    return weighted_sum / total_market_cap
```

### Defensive Programming Patterns

This project heavily uses defensive programming due to unreliable external data sources:

```python
# Safe float conversion (handles NaN, infinity, None, empty strings)
def _safe_float(value: Any) -> float | None:
    """Convert value to float, returning None for invalid inputs."""
    if value is None or value == "" or value == "N/A":
        return None
    try:
        f = float(value)
        if math.isnan(f) or math.isinf(f):
            return None
        return f
    except (ValueError, TypeError):
        return None

# Safe string conversion
def _safe_string(value: Any) -> str | None:
    """Convert value to string, returning None for empty/None values."""
    if value is None or value == "" or value == "N/A":
        return None
    return str(value).strip()
```

**Always use these patterns when:**
- Parsing data from external APIs (yfinance)
- Handling user inputs
- Performing calculations that could result in division by zero
- Working with financial ratios (P/E, P/B, etc.)

### Error Handling

```python
# Use specific exceptions
try:
    data = fetch_from_api(symbol)
except requests.HTTPError as e:
    logger.error(f"HTTP error fetching {symbol}: {e}")
    raise ValueError(f"Failed to fetch data for {symbol}")
except requests.Timeout as e:
    logger.warning(f"Timeout fetching {symbol}, will retry")
    raise

# Never use bare except clauses
# Avoid silent failures - log and raise or return appropriate error responses
```

### Docstrings

Use **Google-style docstrings** for all public functions, classes, and methods:

```python
def normalize(symbol: str, raw_data: dict[str, Any]) -> StockKPIs:
    """
    Normalize raw provider data into standardized StockKPIs format.
    
    Performs defensive parsing with multiple field name fallbacks and
    handles missing data, NaN values, and unit conversions.
    
    Args:
        symbol: Stock ticker symbol (e.g., 'AAPL', 'MSFT')
        raw_data: Raw data dictionary from yfinance info payload
        
    Returns:
        Normalized StockKPIs object with canonical field names
        
    Raises:
        ValueError: If symbol is empty or invalid
        
    Example:
        >>> raw = ticker.info
        >>> kpis = normalize('AAPL', raw)
        >>> print(f"Price: ${kpis.price:.2f}")
    """
```

### Module Organization

**Import Order:**
```python
# 1. Standard library
import json
import math
from typing import Any, Dict, List, Optional

# 2. Third-party packages
import pandas as pd
import yfinance as yf
from pydantic import BaseModel, Field

# 3. Local imports
from stocklighthouse.models import StockKPIs, IngestorRequest
from stocklighthouse.ingest.yfinance_ingestor import YFinanceIngestor
```

### Testing Patterns

- Test files mirror source structure: `test_<module>.py` in `backend/tests/`
- Use **pytest** with fixtures for common setup
- Mock external API calls with **pytest-mock**
- Aim for **90%+ code coverage**

```python
# backend/tests/test_normalizer.py
import pytest
from stocklighthouse.normalizer import normalize, _safe_float

class TestSafeFloat:
    """Test suite for _safe_float defensive parsing."""
    
    def test_valid_float(self):
        """Should parse valid float strings."""
        assert _safe_float("42.5") == 42.5
        assert _safe_float(42.5) == 42.5
    
    def test_invalid_inputs(self):
        """Should return None for invalid inputs."""
        assert _safe_float(None) is None
        assert _safe_float("") is None
        assert _safe_float("N/A") is None
        assert _safe_float(float('nan')) is None
        assert _safe_float(float('inf')) is None
    
    def test_type_errors(self):
        """Should handle type conversion errors."""
        assert _safe_float([1, 2, 3]) is None
        assert _safe_float({"value": 42}) is None

class TestNormalize:
    """Test suite for normalize function."""
    
    def test_full_data(self):
        """Should normalize complete data successfully."""
        raw_data = {
            "symbol": "AAPL",
            "regularMarketPrice": 150.0,
            "regularMarketPreviousClose": 148.0,
            "marketCap": 2400000000000,
            "trailingPE": 28.5,
            # ... more fields
        }
        result = normalize("AAPL", raw_data)
        
        assert result.symbol == "AAPL"
        assert result.price == 150.0
        assert result.change_pct == pytest.approx(1.35, rel=0.01)
    
    def test_missing_fields(self):
        """Should handle missing fields gracefully."""
        raw_data = {"symbol": "TEST"}
        result = normalize("TEST", raw_data)
        
        assert result.symbol == "TEST"
        assert result.price is None
        assert result.pe_ratio is None
```

## TypeScript/React Coding Standards

### Type Safety

- Use **strict TypeScript mode** (enabled in tsconfig.json)
- Define **interfaces** for all data structures
- Avoid `any` type; use `unknown` if type is truly unknown
- Type all component props and state

```typescript
// Good: Strongly typed component
interface StockKPIs {
  symbol: string;
  price: number | null;
  change_pct: number | null;
  market_cap: number | null;
  pe_ratio: number | null;
  sector: string | null;
  industry: string | null;
}

interface KPITableProps {
  stock: StockKPIs;
  className?: string;
}

const KPITable: React.FC<KPITableProps> = ({ stock, className }) => {
  const formatPrice = (price: number | null): string => {
    if (price === null) return 'N/A';
    return `$${price.toFixed(2)}`;
  };

  const formatPercent = (value: number | null): string => {
    if (value === null) return 'N/A';
    const sign = value >= 0 ? '+' : '';
    return `${sign}${value.toFixed(2)}%`;
  };

  return (
    <div className={className}>
      <table>
        <tbody>
          <tr>
            <td>Price</td>
            <td>{formatPrice(stock.price)}</td>
          </tr>
          <tr>
            <td>Change</td>
            <td className={stock.change_pct && stock.change_pct >= 0 ? 'positive' : 'negative'}>
              {formatPercent(stock.change_pct)}
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  );
};

export default KPITable;
```

### Component Patterns

- Use **functional components** with hooks (no class components)
- Use **React Router** for navigation (React Router 7)
- Use **CSS modules** for styling (`.module.css` files)
- Keep components focused and single-purpose

```typescript
// Good: Functional component with hooks
import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { searchStocks } from '../services/api';
import styles from './SearchBar.module.css';

interface SearchBarProps {
  placeholder?: string;
}

const SearchBar: React.FC<SearchBarProps> = ({ 
  placeholder = 'Search stocks, sectors, industries...' 
}) => {
  const [query, setQuery] = useState('');
  const [suggestions, setSuggestions] = useState<StockKPIs[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    // Debounce search
    const timeoutId = setTimeout(async () => {
      if (query.trim().length < 2) {
        setSuggestions([]);
        return;
      }

      setIsLoading(true);
      try {
        const results = await searchStocks(query);
        setSuggestions(results);
      } catch (error) {
        console.error('Search failed:', error);
        setSuggestions([]);
      } finally {
        setIsLoading(false);
      }
    }, 300);

    return () => clearTimeout(timeoutId);
  }, [query]);

  const handleSelect = (symbol: string) => {
    navigate(`/stock/${symbol}`);
    setQuery('');
    setSuggestions([]);
  };

  return (
    <div className={styles.searchBar}>
      <input
        type="text"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder={placeholder}
        className={styles.searchInput}
      />
      {isLoading && <div className={styles.spinner}>Loading...</div>}
      {suggestions.length > 0 && (
        <ul className={styles.suggestions}>
          {suggestions.map((stock) => (
            <li
              key={stock.symbol}
              onClick={() => handleSelect(stock.symbol)}
              className={styles.suggestion}
            >
              <strong>{stock.symbol}</strong> - {stock.sector || 'N/A'}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
};

export default SearchBar;
```

### API Client Patterns

Centralize API calls in `frontend/src/services/api.ts`:

```typescript
// services/api.ts
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

interface ApiError {
  message: string;
  status: number;
}

async function fetchApi<T>(endpoint: string): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${endpoint}`);
  
  if (!response.ok) {
    throw {
      message: `API error: ${response.statusText}`,
      status: response.status
    } as ApiError;
  }
  
  return response.json();
}

export const searchStocks = (query: string): Promise<StockKPIs[]> => {
  return fetchApi(`/api/stocks/search?q=${encodeURIComponent(query)}`);
};

export const getStockDetails = (symbol: string): Promise<StockKPIs> => {
  return fetchApi(`/api/stocks/${symbol}`);
};

export const getPriceHistory = (symbol: string): Promise<PriceHistory> => {
  return fetchApi(`/api/stocks/${symbol}/history`);
};
```

### Testing Patterns (Frontend)

- Unit tests with **Vitest** and **Testing Library**
- E2E tests with **Playwright**
- Test files colocated: `ComponentName.test.tsx`

```typescript
// src/components/SearchBar.test.tsx
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { vi } from 'vitest';
import SearchBar from './SearchBar';
import * as api from '../services/api';

// Mock the API module
vi.mock('../services/api');

describe('SearchBar', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders with placeholder text', () => {
    render(
      <BrowserRouter>
        <SearchBar />
      </BrowserRouter>
    );
    
    expect(screen.getByPlaceholderText(/search stocks/i)).toBeInTheDocument();
  });

  it('calls search API when user types', async () => {
    const mockResults = [
      { symbol: 'AAPL', sector: 'Technology', price: 150.0 },
      { symbol: 'MSFT', sector: 'Technology', price: 350.0 }
    ];
    
    vi.mocked(api.searchStocks).mockResolvedValue(mockResults);

    render(
      <BrowserRouter>
        <SearchBar />
      </BrowserRouter>
    );

    const input = screen.getByRole('textbox');
    fireEvent.change(input, { target: { value: 'AAPL' } });

    await waitFor(() => {
      expect(api.searchStocks).toHaveBeenCalledWith('AAPL');
    });

    expect(screen.getByText('AAPL')).toBeInTheDocument();
    expect(screen.getByText(/Technology/)).toBeInTheDocument();
  });

  it('handles API errors gracefully', async () => {
    vi.mocked(api.searchStocks).mockRejectedValue(new Error('Network error'));

    render(
      <BrowserRouter>
        <SearchBar />
      </BrowserRouter>
    );

    const input = screen.getByRole('textbox');
    fireEvent.change(input, { target: { value: 'FAIL' } });

    await waitFor(() => {
      expect(api.searchStocks).toHaveBeenCalled();
    });

    // Should not display suggestions on error
    expect(screen.queryByRole('list')).not.toBeInTheDocument();
  });
});
```

## Project Architecture Patterns

### Data Flow

```
External API (yfinance) 
    ↓
Ingestor (fetch with retry + cache)
    ↓
Normalizer (convert to StockKPIs)
    ↓
Analyzer (aggregate by sector)
    ↓
Scoring (compute buy scores)
    ↓
API (FastAPI REST endpoints)
    ↓
Frontend (React UI)
```

### Pydantic Models

All data structures use Pydantic models for validation:

```python
# models.py
from pydantic import BaseModel, Field
from typing import Optional

class StockKPIs(BaseModel):
    """Canonical stock data model."""
    
    symbol: str = Field(..., description="Stock ticker symbol")
    name: Optional[str] = Field(None, description="Company name")
    price: Optional[float] = Field(None, description="Current price in USD")
    change_pct: Optional[float] = Field(None, description="Daily change percentage")
    market_cap: Optional[float] = Field(None, description="Market capitalization")
    pe_ratio: Optional[float] = Field(None, description="Price-to-earnings ratio")
    pb_ratio: Optional[float] = Field(None, description="Price-to-book ratio")
    dividend_yield: Optional[float] = Field(None, description="Dividend yield (decimal)")
    sector: Optional[str] = Field(None, description="Business sector")
    industry: Optional[str] = Field(None, description="Business industry")
    market: Optional[str] = Field(None, description="Primary market (US, UK, etc.)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "symbol": "AAPL",
                "name": "Apple Inc.",
                "price": 150.25,
                "change_pct": 1.35,
                "market_cap": 2400000000000,
                "pe_ratio": 28.5,
                "sector": "Technology"
            }
        }
```

### File Organization

```
backend/src/stocklighthouse/
├── __init__.py
├── models.py              # Pydantic models
├── normalizer.py          # Data normalization
├── analyzer.py            # Sector analysis
├── ingest/
│   ├── __init__.py
│   └── yfinance_ingestor.py
└── api/
    ├── __init__.py
    └── main.py            # FastAPI app

backend/scoring/
├── __init__.py
├── sample_scoring.py      # Scoring functions
└── scoring_service.py     # Scoring pipeline

frontend/src/
├── components/            # Reusable components
├── pages/                 # Route pages
├── services/              # API clients
├── types/                 # TypeScript types
└── tests/                 # Component tests
```

## Common Patterns and Conventions

### Field Name Fallbacks (Normalizer)

When parsing data from yfinance, always check multiple field names:

```python
# Price fallbacks
price = _safe_float(raw_data.get("regularMarketPrice"))
if price is None:
    price = _safe_float(raw_data.get("currentPrice"))

# Market cap fallbacks
market_cap = _safe_float(raw_data.get("marketCap"))
if market_cap is None:
    market_cap = _safe_float(raw_data.get("marketCapitalization"))
```

### Percentage vs. Decimal

- **Display percentages** as user-facing strings: "1.35%"
- **Store internally** as decimals: 0.0135 for dividend yield
- **Store change_pct** as percentage value: 1.35 (not 0.0135)

```python
# Dividend yield: convert percentage to decimal
dividend_yield = _safe_float(raw_data.get("dividendYield"))
if dividend_yield is not None and dividend_yield > 1.0:
    # Value is in percentage form, convert to decimal
    dividend_yield = dividend_yield / 100.0
```

### Caching Patterns

The ingestor uses in-memory TTL caching:

```python
from dataclasses import dataclass
from datetime import datetime, timedelta

@dataclass
class CacheEntry:
    data: Any
    timestamp: datetime

class YFinanceIngestor:
    def __init__(self, cache_ttl_seconds: int = 300):
        self._cache: dict[str, CacheEntry] = {}
        self._cache_ttl = timedelta(seconds=cache_ttl_seconds)
    
    def _get_from_cache(self, symbol: str) -> Optional[Any]:
        if symbol not in self._cache:
            return None
        
        entry = self._cache[symbol]
        if datetime.now() - entry.timestamp > self._cache_ttl:
            del self._cache[symbol]
            return None
        
        return entry.data
    
    def _store_in_cache(self, symbol: str, data: Any) -> None:
        self._cache[symbol] = CacheEntry(data=data, timestamp=datetime.now())
```

### Retry Logic (Exponential Backoff)

```python
import time

def fetch_with_retry(symbol: str, max_retries: int = 3) -> Any:
    """Fetch data with exponential backoff retry."""
    backoff = 1.0
    
    for attempt in range(max_retries):
        try:
            return fetch_data(symbol)
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            
            wait_time = backoff * (2 ** attempt)
            logger.warning(f"Attempt {attempt + 1} failed for {symbol}, retrying in {wait_time}s")
            time.sleep(wait_time)
```

## API Conventions

### REST Endpoints

- **GET /api/stocks/search?q={query}** - Search stocks (max 50 results)
- **GET /api/stocks/{symbol}** - Get stock details
- **GET /api/stocks/{symbol}/history** - Get 30-day price history
- **GET /api/stocks/{symbol}/pe-distribution** - Get P/E distribution in sector
- **GET /api/sectors** - List all sectors with statistics
- **GET /api/sectors/{sector_name}** - Get sector details and stocks

### Response Formats

All endpoints return JSON with proper HTTP status codes:

```python
# Success response (200)
{
  "symbol": "AAPL",
  "price": 150.25,
  "sector": "Technology"
}

# Error response (404, 500, etc.)
{
  "detail": "Stock not found: INVALID"
}
```

### CORS Configuration

FastAPI backend has CORS enabled for frontend:

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Frontend dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## Environment and Configuration

### Backend Environment

- **PYTHONPATH=src** required when running from backend directory
- Default API port: **8000**
- Run with: `PYTHONPATH=src uvicorn stocklighthouse.api.main:app --reload`

### Frontend Environment

- **VITE_API_URL** - Backend API URL (default: http://localhost:8000)
- Default dev server port: **5173**
- Run with: `npm run dev`

### Data Directories

```
data/
├── samples/       # Raw yfinance JSON payloads
├── normalized/    # Normalized StockKPIs JSON
├── aggregates/    # Sector aggregation results
├── features/      # Feature parquet files for scoring
├── fundamentals/  # Fundamental data parquet files
└── ranks/         # Scoring results (parquet + JSON explanations)
```

## Testing and Quality Standards

### Coverage Requirements

- Maintain **90%+ code coverage** for new code
- Backend: Use `pytest --cov=stocklighthouse --cov-report=html`
- Frontend: Use `npm test -- --coverage`

### Running Tests

```bash
# Backend tests
cd backend
PYTHONPATH=src pytest tests/ -v

# Frontend unit tests
cd frontend
npm test

# Frontend E2E tests (requires running backend)
npm run e2e
```

### Mocking External APIs

Always mock yfinance API calls in tests:

```python
import pytest
from unittest.mock import Mock

def test_fetch_stock(mocker):
    """Test stock fetching with mocked yfinance."""
    mock_ticker = Mock()
    mock_ticker.info = {
        "regularMarketPrice": 150.0,
        "symbol": "AAPL"
    }
    
    mocker.patch('yfinance.Ticker', return_value=mock_ticker)
    
    ingestor = YFinanceIngestor()
    result = ingestor.fetch_single("AAPL")
    
    assert result.success
    assert result.raw_data["info"]["regularMarketPrice"] == 150.0
```

## Common Pitfalls to Avoid

### Backend

1. **Don't access raw_data without defensive parsing** - always use `_safe_float()`, `_safe_string()`
2. **Don't assume fields exist** - yfinance data is inconsistent
3. **Don't use bare `except` clauses** - catch specific exceptions
4. **Don't forget PYTHONPATH** - always set when running from backend/
5. **Don't commit without type hints** - all functions need type annotations

### Frontend

1. **Don't use `any` type** - be explicit about types
2. **Don't forget null checks** - stock data fields can be null
3. **Don't make API calls in render** - use useEffect with dependencies
4. **Don't forget error handling** - API calls can fail
5. **Don't use inline styles** - use CSS modules instead

## Performance Considerations

1. **Use caching** - ingestor has 5-minute TTL cache enabled by default
2. **Batch API calls** - fetch multiple symbols in single request when possible
3. **Lazy load data** - API lazy-loads normalized data on first request
4. **Debounce search** - 300ms debounce on search input
5. **Limit results** - search returns max 50 results

## Security Best Practices

1. **Validate all inputs** - use Pydantic models for validation
2. **Sanitize user input** - escape special characters in search queries
3. **Use HTTPS in production** - enable SSL for API
4. **Don't expose internal errors** - return generic error messages to frontend
5. **Rate limit API** - prevent abuse (future enhancement)

## Documentation Standards

- Update README.md for user-facing features
- Update ARCHITECTURE.md for design decisions
- Update component-specific READMEs (INGESTOR_README.md, etc.)
- Use Google-style docstrings for Python
- Use JSDoc comments for complex TypeScript functions

## Version Control

- Commit messages follow Conventional Commits: `feat:`, `fix:`, `docs:`, etc.
- Branch naming: `feature/name`, `fix/name`, `docs/name`
- Keep commits atomic and focused
- Reference issues in commit messages: `Fixes #123`

---

This instruction set should help GitHub Copilot understand the StockLighthouse codebase and generate suggestions that follow project conventions and best practices.
