# StockLighthouse Architecture

This document provides a comprehensive overview of the StockLighthouse system architecture, design decisions, and data flow.

## Table of Contents

- [System Overview](#system-overview)
- [Architecture Diagram](#architecture-diagram)
- [Component Details](#component-details)
- [Data Flow](#data-flow)
- [Design Decisions](#design-decisions)
- [Technology Stack](#technology-stack)
- [Scalability Considerations](#scalability-considerations)
- [Future Enhancements](#future-enhancements)

## System Overview

StockLighthouse is a three-tier web application for stock data ingestion, normalization, and analysis:

1. **Data Layer**: Fetches raw stock data from external providers (Yahoo Finance)
2. **Business Logic Layer**: Normalizes and analyzes stock data
3. **Presentation Layer**: RESTful API and React-based web interface

### Key Characteristics

- **Defensive Programming**: Graceful handling of missing, invalid, or malformed data
- **Type Safety**: Pydantic models ensure data validation throughout the pipeline
- **Caching**: In-memory TTL-based caching reduces API calls and improves performance
- **Modularity**: Clear separation of concerns with distinct modules for each function
- **Testability**: Comprehensive test coverage with mocked external dependencies

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         Web Browser                              │
│                    (React + TypeScript)                          │
└──────────────────────────┬──────────────────────────────────────┘
                           │ HTTP/REST
                           │
┌──────────────────────────▼──────────────────────────────────────┐
│                      FastAPI Server                              │
│                    (Python Backend)                              │
│  ┌────────────────────────────────────────────────────────┐     │
│  │              REST API Endpoints                        │     │
│  │  /api/stocks/search  │  /api/sectors  │  /api/stocks  │     │
│  └────────────────────────────────────────────────────────┘     │
│                           │                                      │
│  ┌────────────────────────┼──────────────────────────────┐     │
│  │                        │                               │     │
│  │  ┌──────────────┐  ┌──▼──────────┐  ┌─────────────┐  │     │
│  │  │  Ingestor    │  │ Normalizer  │  │  Analyzer   │  │     │
│  │  │              │  │             │  │             │  │     │
│  │  │ - Fetch data │  │ - Parse raw │  │ - Aggregate │  │     │
│  │  │ - Retry      │  │ - Validate  │  │ - Compute   │  │     │
│  │  │ - Cache      │  │ - Convert   │  │ - Analyze   │  │     │
│  │  └──────┬───────┘  └─────────────┘  └─────────────┘  │     │
│  │         │                                             │     │
│  │         │ Raw JSON                                    │     │
│  └─────────┼─────────────────────────────────────────────┘     │
│            │                                                    │
└────────────┼────────────────────────────────────────────────────┘
             │
┌────────────▼────────────────────────────────────────────────────┐
│                  External Data Providers                         │
│                    (Yahoo Finance API)                           │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                      File System                                 │
│   data/samples/      │  data/normalized/  │  data/aggregates/   │
└─────────────────────────────────────────────────────────────────┘
```

## Component Details

### 1. YFinance Ingestor

**Location**: `backend/src/stocklighthouse/ingest/yfinance_ingestor.py`

**Purpose**: Fetch raw stock data from Yahoo Finance API

**Key Features**:
- Exponential backoff retry logic for resilience
- TTL-based in-memory caching to reduce API calls
- Fallback to `fast_info` when full data unavailable
- Batch fetching support for multiple symbols
- Returns raw provider payloads unchanged

**Design Pattern**: Strategy pattern (can swap providers)

```python
class YFinanceIngestor:
    def __init__(self, cache_ttl_seconds, max_retries, ...):
        self._cache: Dict[str, CacheEntry] = {}
    
    def fetch(self, request: IngestorRequest) -> IngestorResponse:
        # Check cache first
        # Fetch from API with retry
        # Store in cache
        # Return aggregated response
```

**Cache Strategy**:
- In-memory dictionary with TTL
- Per-symbol caching
- Automatic expiration on read
- Manual cache clearing available

### 2. Normalizer

**Location**: `backend/src/stocklighthouse/normalizer.py`

**Purpose**: Convert raw provider data to canonical schema

**Key Features**:
- Defensive parsing with `_safe_float()` and `_safe_string()`
- Multiple field name fallbacks (e.g., `regularMarketPrice` → `currentPrice`)
- Unit conversions (dividend yield percentage to decimal)
- Market inference from exchange codes
- NaN and infinity handling

**Design Pattern**: Adapter pattern (provider-agnostic output)

```python
def normalize(symbol: str, raw_data: Dict) -> StockKPIs:
    # Safe extraction with fallbacks
    price = _safe_float(raw_data.get("regularMarketPrice"))
    if price is None:
        price = _safe_float(raw_data.get("currentPrice"))
    
    # Defensive calculations
    if price and previous_close and previous_close > 0:
        change_pct = ((price - previous_close) / previous_close) * 100
    
    return StockKPIs(...)
```

**Edge Cases Handled**:
- Missing fields → None values
- NaN/Infinity → None values
- Empty strings → None values
- Zero/negative previous_close → No change_pct calculated
- Percentage vs decimal dividend yield

### 3. Analyzer

**Location**: `backend/src/stocklighthouse/analyzer.py`

**Purpose**: Aggregate and analyze normalized stock data

**Key Features**:
- Sector-based aggregation
- Statistical computations (median, average)
- Market-cap weighted P/E ratios
- Top ticker identification by market cap
- Unknown sector handling

**Design Pattern**: Aggregator pattern

```python
def sector_aggregate(stocks: list[StockKPIs]) -> list[SectorSummary]:
    # Group by sector
    sector_map = {}
    for stock in stocks:
        sector = stock.sector or "Unknown"
        sector_map.setdefault(sector, []).append(stock)
    
    # Compute statistics per sector
    summaries = [_create_sector_summary(s, stocks) for s, stocks in sector_map.items()]
    
    return sorted(summaries, key=lambda s: (-s.count, s.sector))
```

**Statistics Computed**:
- Median P/E ratio (robust to outliers)
- Median P/B ratio
- Median market cap
- Average dividend yield
- Weighted average P/E (by market cap)

### 4. REST API

**Location**: `backend/src/stocklighthouse/api/main.py`

**Purpose**: Expose data via RESTful HTTP endpoints

**Key Features**:
- FastAPI framework for automatic OpenAPI docs
- CORS support for frontend integration
- In-memory data caching
- JSON request/response
- HTTP status codes for error handling

**Endpoints**:

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/` | GET | Health check |
| `/api/stocks/search` | GET | Search stocks |
| `/api/stocks/{symbol}` | GET | Get stock details |
| `/api/stocks/{symbol}/history` | GET | Get price history |
| `/api/stocks/{symbol}/pe-distribution` | GET | Get P/E distribution |
| `/api/sectors` | GET | List all sectors |
| `/api/sectors/{sector}` | GET | Get sector details |

**Data Loading**:
```python
# Lazy loading with caching
_stock_cache: Optional[list[StockKPIs]] = None

def get_stocks() -> list[StockKPIs]:
    global _stock_cache
    if _stock_cache is None:
        _stock_cache = load_stock_data()  # Load from JSON file
    return _stock_cache
```

### 5. Frontend (React)

**Location**: `frontend/src/`

**Purpose**: User interface for stock data visualization

**Key Components**:

**SearchBar** (`components/SearchBar.tsx`):
- Auto-suggest search with debouncing (300ms)
- Searches across symbol, sector, industry
- Navigates to stock detail on selection

**KPITable** (`components/KPITable.tsx`):
- Displays stock metrics in structured table
- Color coding for positive/negative changes
- Formatted numbers with currency and percentages

**Charts** (`components/PriceChart.tsx`, `PEChart.tsx`):
- Plotly.js interactive charts
- 30-day price history
- P/E distribution across sector peers
- Responsive and mobile-friendly

**SectorHeatmap** (`components/SectorHeatmap.tsx`):
- Color-coded tiles by median P/E ratio
- Shows sector statistics
- Interactive drill-down to sector details

**Architecture Pattern**: Component-based with React Router

```
App
├── HomePage
│   └── SearchBar
├── StockDetailPage
│   ├── KPITable
│   ├── PriceChart
│   └── PEChart
└── SectorDashboard
    └── SectorHeatmap
```

## Data Flow

### 1. Data Ingestion Flow

```
User/Script → IngestorRequest → YFinanceIngestor
                                      ↓
                              Check Cache?
                              ├─ Hit → Return cached
                              └─ Miss → Fetch from API
                                      ↓
                              Retry on failure (exponential backoff)
                                      ↓
                              Store in cache
                                      ↓
                              IngestorResponse → User/Script
```

### 2. Normalization Flow

```
Raw Data (yfinance) → normalize()
                          ↓
                  Extract fields with fallbacks
                          ↓
                  Safe type conversions
                          ↓
                  Calculate derived fields
                          ↓
                  Unit conversions
                          ↓
                  Infer market from exchange
                          ↓
                      StockKPIs (canonical)
```

### 3. Analysis Flow

```
List[StockKPIs] → sector_aggregate()
                          ↓
                  Group by sector
                          ↓
                  Compute statistics
                          ↓
                  Sort by count
                          ↓
                  List[SectorSummary]
```

### 4. API Request Flow

```
Frontend → HTTP Request → FastAPI
                              ↓
                      Route to handler
                              ↓
                      Load cached data
                              ↓
                      Process request
                              ↓
                      JSON Response → Frontend
                              ↓
                      Render in React
```

### 5. End-to-End Flow

```
1. Script: demo_fetch.py
   ↓
   Fetch raw data → data/samples/*.json

2. Script: sample_normalize.py
   ↓
   Normalize data → data/normalized/normalized_kpis.json

3. API Server: uvicorn
   ↓
   Load normalized data → In-memory cache

4. Frontend: npm run dev
   ↓
   Fetch from API → Display in UI
```

## Design Decisions

### 1. Why Pydantic Models?

**Decision**: Use Pydantic for all data structures

**Rationale**:
- Type validation at runtime
- Automatic JSON serialization/deserialization
- JSON schema generation for documentation
- IDE autocomplete support
- Easy migration to other languages (schema-first)

**Alternative Considered**: Python dataclasses (lacks validation)

### 2. Why In-Memory Caching?

**Decision**: Use in-memory TTL cache instead of persistent cache

**Rationale**:
- Simple implementation
- Low latency access
- No external dependencies (Redis, Memcached)
- Suitable for development and small-scale production

**Trade-offs**:
- Cache lost on restart
- Not shared across multiple server instances
- Limited by available memory

**Future**: May migrate to Redis for production scalability

### 3. Why Defensive Parsing?

**Decision**: Extensive use of `_safe_*()` functions

**Rationale**:
- External APIs are unreliable (NaN, missing fields, etc.)
- Graceful degradation better than crashes
- Partial data is useful (show what's available)
- Easier debugging with None vs exceptions

### 4. Why Median Over Mean?

**Decision**: Use median for P/E, P/B, market cap aggregates

**Rationale**:
- Robust to outliers (extreme values don't skew results)
- More representative of "typical" stock in sector
- Financial data often has extreme outliers

**Exception**: Dividend yield uses mean (values are bounded)

### 5. Why Separate Normalizer?

**Decision**: Separate normalization from ingestion

**Rationale**:
- Single Responsibility Principle
- Easy to add new providers (just implement normalizer)
- Can normalize historical data offline
- Testable in isolation

### 6. Why FastAPI?

**Decision**: Use FastAPI instead of Flask/Django

**Rationale**:
- Automatic OpenAPI documentation
- Native async support (future scalability)
- Type hints integration
- High performance (Starlette + Pydantic)
- Modern Python 3.10+ features

### 7. Why React Over Vue/Angular?

**Decision**: Use React with TypeScript

**Rationale**:
- Large ecosystem and community
- TypeScript for type safety
- Component reusability
- Excellent tooling (Vite, Testing Library)
- Performance with virtual DOM

## Technology Stack

### Backend

| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| Language | Python | 3.10+ | Core language |
| Framework | FastAPI | 0.104+ | Web framework |
| Server | Uvicorn | 0.24+ | ASGI server |
| Validation | Pydantic | 2.0+ | Data models |
| Data Source | yfinance | 0.2.32+ | Stock data |
| Testing | pytest | 7.4+ | Unit tests |
| Coverage | pytest-cov | 4.1+ | Coverage reports |

### Frontend

| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| Language | TypeScript | 5.9+ | Core language |
| Framework | React | 19+ | UI library |
| Build | Vite | 7+ | Build tool |
| Routing | React Router | 7+ | Navigation |
| Charts | Plotly.js | 3.3+ | Visualizations |
| Testing | Vitest | 4+ | Unit tests |
| E2E | Playwright | 1.56+ | E2E tests |

### DevOps

| Component | Technology | Purpose |
|-----------|-----------|---------|
| Containers | Docker | Containerization |
| Orchestration | docker-compose | Multi-container setup |
| CI/CD | GitHub Actions | Automated testing |
| Version Control | Git + GitHub | Source control |

## Scalability Considerations

### Current Limitations

1. **Single Server**: API runs on single instance
2. **In-Memory Cache**: Lost on restart, not shared
3. **File-Based Data**: Loaded from JSON files
4. **Synchronous Operations**: No async/await in ingestor

### Scalability Improvements

#### Short-Term (< 1000 requests/sec)

1. **Add Redis Caching**:
   ```python
   import redis
   r = redis.Redis()
   
   def get_from_cache(symbol):
       return r.get(f"stock:{symbol}")
   ```

2. **Database Storage**:
   - PostgreSQL for structured data
   - TimescaleDB for time-series data

3. **API Rate Limiting**:
   ```python
   from slowapi import Limiter
   limiter = Limiter(key_func=get_remote_address)
   
   @app.get("/api/stocks/search")
   @limiter.limit("100/minute")
   def search_stocks(...):
       ...
   ```

#### Medium-Term (< 10000 requests/sec)

1. **Async Ingestion**:
   ```python
   async def fetch_async(symbols):
       async with aiohttp.ClientSession() as session:
           tasks = [fetch_one(session, symbol) for symbol in symbols]
           return await asyncio.gather(*tasks)
   ```

2. **Load Balancing**:
   - Multiple API server instances
   - Nginx/HAProxy load balancer
   - Shared Redis cache

3. **CDN for Frontend**:
   - CloudFlare/AWS CloudFront
   - Static asset caching
   - Geographic distribution

#### Long-Term (> 10000 requests/sec)

1. **Microservices Architecture**:
   - Separate ingestor service
   - Separate analyzer service
   - Message queue (RabbitMQ/Kafka)

2. **Horizontal Scaling**:
   - Kubernetes orchestration
   - Auto-scaling based on load
   - Multi-region deployment

3. **Data Streaming**:
   - WebSocket for real-time updates
   - Server-Sent Events (SSE)
   - GraphQL subscriptions

## Future Enhancements

### Data Sources

- [ ] Add Alpha Vantage provider
- [ ] Add Polygon.io provider
- [ ] Support historical data fetching
- [ ] Real-time streaming quotes

### Features

- [ ] User authentication and portfolios
- [ ] Watchlist functionality
- [ ] Price alerts and notifications
- [ ] Technical indicators (RSI, MACD, Bollinger Bands)
- [ ] Fundamental analysis tools
- [ ] Screener with custom filters
- [ ] Backtesting capabilities

### Infrastructure

- [ ] Persistent cache (Redis)
- [ ] Database storage (PostgreSQL)
- [ ] Message queue (RabbitMQ)
- [ ] Monitoring (Prometheus + Grafana)
- [ ] Logging (ELK stack)
- [ ] CI/CD pipelines
- [ ] Kubernetes deployment

### Performance

- [ ] Async data fetching
- [ ] GraphQL API
- [ ] Server-side rendering (SSR)
- [ ] Progressive Web App (PWA)
- [ ] Code splitting and lazy loading

### Analytics

- [ ] Advanced analytics dashboard
- [ ] Machine learning predictions
- [ ] Sentiment analysis from news
- [ ] Correlation analysis
- [ ] Risk metrics and VaR

## Conclusion

StockLighthouse's architecture prioritizes:

1. **Simplicity**: Easy to understand and maintain
2. **Robustness**: Handles errors gracefully
3. **Modularity**: Clear separation of concerns
4. **Testability**: Comprehensive test coverage
5. **Scalability**: Can grow with user demand

The current design is suitable for development and small-to-medium production deployments. For larger scale, the architecture can evolve incrementally without major rewrites.

---

**Last Updated**: 2025-11-23
**Version**: 0.1.0
