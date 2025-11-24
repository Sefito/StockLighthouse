# StockLighthouse

A comprehensive stock data ingestion, normalization, and analysis platform with a modern web interface. StockLighthouse provides robust data fetching from financial APIs, standardized data normalization, sector analysis, and interactive visualizations.

## 🚀 Features

### Backend
- **YFinance Ingestor**: Fetch stock data with exponential backoff retry logic, in-memory TTL caching, and fast_info fallback support
- **Data Normalization**: Convert raw provider data to standardized KPIs with defensive parsing and edge case handling
- **Sector Analysis**: Aggregate stocks by sector with weighted averages and comprehensive statistics
- **Scoring Pipeline**: Compute composite buy scores combining technical and fundamental indicators with configurable weights
- **REST API**: FastAPI-based RESTful API with CORS support for frontend integration
- **Type Safety**: Full Pydantic models for data validation and JSON schema generation
- **Comprehensive Testing**: 150+ unit tests with mocked HTTP requests and 99% code coverage

### Frontend
- **React + TypeScript**: Modern, type-safe UI with React 19 and TypeScript
- **Interactive Charts**: Plotly.js-powered price history and P/E distribution charts
- **Smart Search**: Auto-suggest search across symbols, sectors, and industries
- **Sector Dashboard**: Color-coded heatmap showing sector performance and top stocks
- **Responsive Design**: Mobile-friendly interface with CSS modules

### DevOps
- **Containerization**: Docker and docker-compose support for easy deployment
- **Redis Integration**: Optional Redis caching for top candidate rankings
- **CI/CD Ready**: GitHub Actions workflows for testing and deployment
- **Development Tools**: Hot reload, linting, and automated testing

## 📋 Table of Contents

- [Quick Start](#quick-start)
- [Installation](#installation)
- [Usage Examples](#usage-examples)
- [Project Structure](#project-structure)
- [Architecture](#architecture)
- [API Documentation](#api-documentation)
- [Development](#development)
- [Testing](#testing)
- [Deployment](#deployment)
- [Contributing](#contributing)
- [Documentation](#documentation)
- [Troubleshooting](#troubleshooting)
- [License](#license)

## 🎯 Quick Start

### Prerequisites

- **Python 3.10+** with pip
- **Node.js 18+** with npm
- **Git** for version control

### 1. Clone the Repository

```bash
git clone https://github.com/Sefito/StockLighthouse.git
cd StockLighthouse
```

### 2. Backend Setup

```bash
cd backend
pip install -r requirements.txt
```

### 3. Fetch Sample Data

```bash
# From repository root
python scripts/demo_fetch.py
python sample_normalize.py
```

### 4. Start Backend API

```bash
cd backend
PYTHONPATH=src uvicorn stocklighthouse.api.main:app --reload --host 0.0.0.0 --port 8000
```

API will be available at `http://localhost:8000`

### 5. Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

Frontend will be available at `http://localhost:5173`

## 📦 Installation

### Backend Dependencies

```bash
cd backend
pip install -r requirements.txt
```

**Core Dependencies:**
- `yfinance>=0.2.32` - Financial data API wrapper
- `pydantic>=2.0.0` - Data validation and models
- `fastapi>=0.104.0` - Modern web framework
- `uvicorn[standard]>=0.24.0` - ASGI server

**Testing:**
- `pytest>=7.4.0` - Testing framework
- `pytest-mock>=3.12.0` - Mocking support
- `pytest-cov>=4.1.0` - Coverage reporting

### Frontend Dependencies

```bash
cd frontend
npm install
```

**Core:**
- React 19 + TypeScript - UI framework
- Vite 7 - Build tool
- React Router 7 - Routing

**Visualization:**
- Plotly.js - Interactive charts

**Testing:**
- Vitest - Unit testing
- Playwright - E2E testing
- Testing Library - React component testing

### Docker Installation

Run the entire stack with Docker Compose:

```bash
docker-compose up --build
```

Services:
- Backend: `http://localhost:8000`
- Frontend: `http://localhost:5173`

## 💡 Usage Examples

### Python API - Fetch Stock Data

```python
from stocklighthouse.ingest.yfinance_ingestor import YFinanceIngestor
from stocklighthouse.models import IngestorRequest

# Initialize ingestor with caching
ingestor = YFinanceIngestor(
    cache_ttl_seconds=300,  # 5 minute cache
    max_retries=3
)

# Fetch multiple stocks
request = IngestorRequest(
    symbols=["AAPL", "MSFT", "GOOGL"],
    use_cache=True
)
response = ingestor.fetch(request)

# Process results
print(f"Fetched: {response.fetched_count}, Failed: {response.failed_count}")
for ticker in response.tickers:
    if ticker.success:
        price = ticker.raw_data['info'].get('regularMarketPrice')
        print(f"{ticker.symbol}: ${price}")
    else:
        print(f"{ticker.symbol}: {ticker.error}")
```

### Python API - Normalize Data

```python
from stocklighthouse.normalizer import normalize
from stocklighthouse.ingest.yfinance_ingestor import YFinanceIngestor

# Fetch raw data
ingestor = YFinanceIngestor()
ticker_data = ingestor.fetch_single("AAPL")

# Normalize to canonical schema
if ticker_data.success and ticker_data.raw_data:
    kpis = normalize("AAPL", ticker_data.raw_data["info"])
    
    print(f"Symbol: {kpis.symbol}")
    print(f"Price: ${kpis.price:.2f}")
    print(f"Change: {kpis.change_pct:+.2f}%")
    print(f"Market Cap: ${kpis.market_cap:,.0f}")
    print(f"P/E Ratio: {kpis.pe_ratio:.2f}")
    print(f"Sector: {kpis.sector}")
```

### Python API - Sector Analysis

```python
from stocklighthouse.analyzer import sector_aggregate, weighted_average_pe
from stocklighthouse.models import StockKPIs

# Create stock data (or load from normalized JSON)
stocks = [
    StockKPIs(symbol="AAPL", sector="Technology", pe_ratio=28.5, market_cap=2.4e12),
    StockKPIs(symbol="MSFT", sector="Technology", pe_ratio=30.2, market_cap=2.1e12),
    StockKPIs(symbol="JNJ", sector="Healthcare", pe_ratio=15.5, market_cap=0.4e12),
]

# Aggregate by sector
summaries = sector_aggregate(stocks)
for summary in summaries:
    print(f"\n{summary.sector}:")
    print(f"  Count: {summary.count} stocks")
    print(f"  Median P/E: {summary.median_pe:.2f}")
    print(f"  Top stocks: {[t[0] for t in summary.top_tickers]}")

# Calculate weighted average
weighted_pe = weighted_average_pe(stocks)
print(f"\nMarket-cap weighted P/E: {weighted_pe:.2f}")
```

### Python API - Scoring Pipeline

```python
from backend.scoring.scoring_service import ScoringService

# Initialize scoring service
service = ScoringService(config_path='config/scoring.yaml')

# Run scoring pipeline
result_df = service.run_scoring_pipeline(
    features_path='data/features/daily_features.parquet',
    fundamentals_path='data/fundamentals/latest.parquet',
    date_str='2025-11-24'
)

# View top candidates
print("\nTop 10 Buy Candidates:")
top_10 = result_df.nlargest(10, 'composite_score')
for _, row in top_10.iterrows():
    print(f"{row['symbol']}: {row['composite_score']:.3f} "
          f"(tech: {row['tech_score']:.3f}, fund: {row['fund_score']:.3f})")

# Load explanations
import json
with open('data/ranks/2025-11-24_explanations.json') as f:
    explanations = json.load(f)
    print(f"\nExplanation for AAPL:")
    print(explanations['AAPL']['explanation'])
```

### REST API Examples

```bash
# Search stocks
curl "http://localhost:8000/api/stocks/search?q=tech"

# Get stock details
curl "http://localhost:8000/api/stocks/AAPL"

# Get price history
curl "http://localhost:8000/api/stocks/AAPL/history"

# Get sectors
curl "http://localhost:8000/api/sectors"

# Get sector details
curl "http://localhost:8000/api/sectors/Technology"
```

## 📁 Project Structure

```
StockLighthouse/
├── backend/                        # Python backend
│   ├── src/
│   │   └── stocklighthouse/
│   │       ├── api/
│   │       │   └── main.py        # FastAPI application
│   │       ├── ingest/
│   │       │   ├── __init__.py
│   │       │   └── yfinance_ingestor.py  # Data fetching
│   │       ├── models.py          # Pydantic models
│   │       ├── normalizer.py      # Data normalization
│   │       ├── analyzer.py        # Sector analysis
│   │       └── __init__.py
│   ├── scoring/                   # Scoring pipeline
│   │   ├── __init__.py
│   │   ├── sample_scoring.py      # Scoring functions
│   │   ├── scoring_service.py     # Main scoring service
│   │   └── README.md              # Scoring documentation
│   ├── tests/
│   │   ├── test_ingestor.py      # Ingestor tests
│   │   ├── test_normalizer.py    # Normalizer tests
│   │   ├── test_analyzer.py      # Analyzer tests
│   │   ├── test_scoring.py       # Scoring tests
│   │   └── README.md
│   ├── requirements.txt           # Python dependencies
│   ├── pytest.ini                 # Pytest configuration
│   ├── INGESTOR_README.md        # Ingestor documentation
│   └── ANALYZER_README.md        # Analyzer documentation
├── frontend/                      # React frontend
│   ├── src/
│   │   ├── components/           # React components
│   │   │   ├── SearchBar.tsx
│   │   │   ├── KPITable.tsx
│   │   │   ├── PriceChart.tsx
│   │   │   ├── PEChart.tsx
│   │   │   └── SectorHeatmap.tsx
│   │   ├── pages/                # Page components
│   │   │   ├── HomePage.tsx
│   │   │   ├── StockDetailPage.tsx
│   │   │   └── SectorDashboard.tsx
│   │   ├── services/
│   │   │   └── api.ts            # API client
│   │   ├── types/
│   │   │   └── index.ts          # TypeScript types
│   │   ├── App.tsx               # Main app component
│   │   └── main.tsx              # Entry point
│   ├── e2e/                      # E2E tests
│   ├── package.json
│   ├── vite.config.ts
│   └── README.md
├── scripts/
│   ├── demo_fetch.py             # Fetch demo data
│   ├── demo_analyzer.py          # Analyzer demo
│   └── generate_sample_features.py  # Generate scoring features
├── data/
│   ├── samples/                  # Raw sample data
│   ├── normalized/               # Normalized KPIs
│   ├── aggregates/               # Sector aggregates
│   ├── features/                 # Feature data for scoring
│   └── ranks/                    # Scoring results (parquet + JSON)
├── config/
│   └── scoring.yaml              # Scoring configuration
├── tests/                        # Root-level test utilities
│   └── utils/
│       └── visual-diff.js        # Visual diff tool
├── .github/
│   ├── workflows/                # CI/CD workflows
│   └── agents/                   # Agent configurations
├── docker-compose.yml            # Docker orchestration
├── Dockerfile.backend            # Backend container
├── Dockerfile.frontend           # Frontend container
├── sample_normalize.py           # Normalization demo
├── NORMALIZER_README.md          # Normalizer documentation
├── CONTRIBUTING.md               # Contribution guidelines
└── README.md                     # This file
```

## 🏗️ Architecture

### System Overview

StockLighthouse follows a three-tier architecture:

```
┌─────────────────────────────────────────────────────────────┐
│                       Frontend (React)                       │
│  Search │ Stock Details │ Charts │ Sector Dashboard         │
└────────────────────────┬────────────────────────────────────┘
                         │ REST API
                         │
┌────────────────────────▼────────────────────────────────────┐
│                    Backend API (FastAPI)                     │
│  /api/stocks │ /api/sectors │ /api/search                   │
└────────────────────────┬────────────────────────────────────┘
                         │
         ┌───────────────┼───────────────┐
         │               │               │
┌────────▼─────┐ ┌──────▼──────┐ ┌─────▼──────┐
│  Ingestor    │ │ Normalizer  │ │  Analyzer  │
│  (YFinance)  │ │  (KPI Map)  │ │  (Sector)  │
└──────────────┘ └─────────────┘ └────────────┘
         │
┌────────▼──────────────────────────────────────────────────┐
│              External Data Provider (Yahoo Finance)        │
└───────────────────────────────────────────────────────────┘
```

### Data Flow

1. **Ingestion**: YFinance ingestor fetches raw stock data with retry logic and caching
2. **Normalization**: Raw provider data is converted to canonical StockKPIs schema
3. **Analysis**: Normalized data is aggregated by sector with statistical computations
4. **API Layer**: FastAPI exposes RESTful endpoints for frontend consumption
5. **Visualization**: React frontend displays data with interactive charts

### Key Components

#### YFinance Ingestor
- Fetches data from Yahoo Finance API
- Implements exponential backoff for resilience
- In-memory TTL-based caching (300s default)
- Fallback to fast_info when full data unavailable
- Returns raw provider payload

#### Normalizer
- Defensive parsing of raw data
- Multiple field name fallbacks
- Handles NaN, infinity, missing values
- Unit conversions (e.g., dividend yield %)
- Market inference from exchange codes

#### Analyzer
- Sector aggregation with statistics
- Median and average calculations
- Market-cap weighted P/E ratios
- Top ticker identification

#### API
- RESTful endpoints with FastAPI
- CORS enabled for frontend
- JSON-based request/response
- Error handling with HTTP status codes

#### Frontend
- Component-based React architecture
- TypeScript for type safety
- React Router for navigation
- Plotly.js for charts
- Responsive CSS design

## 📚 API Documentation

### Base URL
`http://localhost:8000`

### Endpoints

#### Health Check
```
GET /
Response: {"status": "ok", "message": "StockLighthouse API"}
```

#### Search Stocks
```
GET /api/stocks/search?q={query}
Parameters:
  - q: Search query (symbol, sector, or industry)
Response: Array of StockKPIs objects (max 50 results)
```

#### Get Stock Details
```
GET /api/stocks/{symbol}
Parameters:
  - symbol: Stock ticker symbol
Response: StockKPIs object
```

#### Get Price History
```
GET /api/stocks/{symbol}/history
Parameters:
  - symbol: Stock ticker symbol
Response: {symbol, dates[], prices[]}
```

#### Get P/E Distribution
```
GET /api/stocks/{symbol}/pe-distribution
Parameters:
  - symbol: Stock ticker symbol
Response: {symbol, sector, pe_ratios[], symbols[], current_pe}
```

#### Get All Sectors
```
GET /api/sectors
Response: Array of sector summaries with statistics
```

#### Get Sector Details
```
GET /api/sectors/{sector_name}
Parameters:
  - sector_name: Name of the sector
Response: {sector, summary, stocks[]}
```

For detailed API documentation, see [backend/src/stocklighthouse/api/main.py](backend/src/stocklighthouse/api/main.py)

## 🛠️ Development

### Backend Development

```bash
cd backend

# Install dependencies
pip install -r requirements.txt

# Run API with hot reload
PYTHONPATH=src uvicorn stocklighthouse.api.main:app --reload

# Run tests
PYTHONPATH=src pytest tests/ -v

# Run tests with coverage
PYTHONPATH=src pytest tests/ -v --cov=stocklighthouse --cov-report=html
```

### Frontend Development

```bash
cd frontend

# Install dependencies
npm install

# Start dev server with hot reload
npm run dev

# Run unit tests
npm test

# Run tests in UI mode
npm run test:ui

# Lint code
npm run lint

# Build for production
npm run build
```

### Demo Scripts

```bash
# Fetch sample stock data (from repo root)
python scripts/demo_fetch.py

# Normalize raw data
python sample_normalize.py

# Run analyzer demo
python scripts/demo_analyzer.py

# Generate sample features for scoring
python scripts/generate_sample_features.py

# Run scoring pipeline
python backend/scoring/scoring_service.py \
  --features data/features/daily_features.parquet \
  --date $(date +%Y-%m-%d)
```

## 🧪 Testing

### Backend Tests

```bash
cd backend

# Run all tests
PYTHONPATH=src pytest tests/ -v

# Run specific test file
PYTHONPATH=src pytest tests/test_ingestor.py -v

# Run with coverage
PYTHONPATH=src pytest tests/ -v --cov=stocklighthouse --cov-report=term-missing

# Run tests with markers
PYTHONPATH=src pytest tests/ -v -m "not slow"
```

**Test Coverage:**
- 19 ingestor tests (HTTP mocking, retry logic, caching)
- 32 normalizer tests (edge cases, type safety, conversions)
- 27 analyzer tests (aggregation, weighted averages, edge cases)

### Frontend Tests

```bash
cd frontend

# Run unit tests
npm test

# Run E2E tests (requires backend and frontend running)
npm run e2e

# Generate coverage report
npm test -- --coverage
```

**Test Coverage:**
- Unit tests for components (SearchBar, KPITable, Charts)
- E2E tests for user flows (search, stock detail, sector dashboard)
- Visual regression tests with screenshots

### Visual Regression Testing

Screenshots are automatically captured during E2E tests and saved to `.test-results/screenshots/<issue-number>/`

## 🚀 Deployment

### Docker Deployment

```bash
# Build and run with docker-compose
docker-compose up --build

# Run in detached mode
docker-compose up -d

# Stop services
docker-compose down
```

### Production Build

**Backend:**
```bash
cd backend
pip install -r requirements.txt
PYTHONPATH=src uvicorn stocklighthouse.api.main:app --host 0.0.0.0 --port 8000
```

**Frontend:**
```bash
cd frontend
npm install
npm run build
npm run preview  # Serve production build
```

### Environment Variables

Backend:
- `PORT` - API server port (default: 8000)
- `PYTHONPATH` - Python module search path

Frontend:
- `VITE_API_URL` - Backend API URL (default: http://localhost:8000)

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.

### Quick Contribution Guide

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Make your changes with tests
4. Run linters and tests
5. Commit with clear messages
6. Push and create a Pull Request

### Code Standards

- **Python**: Follow PEP 8, use type hints, add docstrings
- **TypeScript**: Follow ESLint rules, use strict types
- **Tests**: Maintain 90%+ coverage
- **Documentation**: Update docs with code changes

## 📖 Documentation

### Component Documentation

- [Architecture Overview](ARCHITECTURE.md) - System design and data flow
- [YFinance Ingestor](backend/INGESTOR_README.md) - Data fetching API
- [Normalizer](NORMALIZER_README.md) - Data normalization
- [Analyzer](backend/ANALYZER_README.md) - Sector analysis
- [Scoring Pipeline](backend/scoring/README.md) - Stock scoring and ranking
- [Frontend](frontend/README.md) - UI components and setup
- [Contributing](CONTRIBUTING.md) - Contribution guidelines
- [Tests](backend/tests/README.md) - Testing documentation

### Additional Resources

- [Pydantic Documentation](https://docs.pydantic.dev/) - Data validation
- [FastAPI Documentation](https://fastapi.tiangolo.com/) - Web framework
- [React Documentation](https://react.dev/) - UI framework
- [Plotly.js Documentation](https://plotly.com/javascript/) - Charts

## 🔧 Troubleshooting

### Common Issues

#### Backend Issues

**Problem**: `ModuleNotFoundError: No module named 'stocklighthouse'`
```bash
# Solution: Set PYTHONPATH
export PYTHONPATH=/path/to/StockLighthouse/backend/src
# Or use relative path
PYTHONPATH=src python your_script.py
```

**Problem**: Tests fail with import errors
```bash
# Solution: Run tests with PYTHONPATH
cd backend
PYTHONPATH=src pytest tests/ -v
```

**Problem**: API returns 404 for all endpoints
```bash
# Solution: Ensure normalized data exists
python scripts/demo_fetch.py
python sample_normalize.py
```

#### Frontend Issues

**Problem**: API connection refused
```bash
# Solution: Start backend first
cd backend
PYTHONPATH=src uvicorn stocklighthouse.api.main:app --host 0.0.0.0 --port 8000
```

**Problem**: Port 5173 already in use
```bash
# Solution: Vite will auto-increment port, check terminal output
# Or kill the process using the port:
lsof -ti:5173 | xargs kill
```

**Problem**: Charts not rendering
```bash
# Solution: Clear node_modules and reinstall
rm -rf node_modules package-lock.json
npm install
```

#### Docker Issues

**Problem**: `Cannot connect to Docker daemon`
```bash
# Solution: Start Docker service
sudo systemctl start docker  # Linux
# Or start Docker Desktop on macOS/Windows
```

**Problem**: Port conflicts with docker-compose
```bash
# Solution: Stop services using ports 8000 or 5173
docker-compose down
# Or modify ports in docker-compose.yml
```

### Data Issues

**Problem**: No sample data available
```bash
# Solution: Run demo scripts
python scripts/demo_fetch.py
python sample_normalize.py
```

**Problem**: Stale cached data
```python
# Solution: Clear cache programmatically
from stocklighthouse.ingest.yfinance_ingestor import YFinanceIngestor
ingestor = YFinanceIngestor()
ingestor.clear_cache()
```

### Getting Help

- **Issues**: Report bugs on [GitHub Issues](https://github.com/Sefito/StockLighthouse/issues)
- **Discussions**: Ask questions in [GitHub Discussions](https://github.com/Sefito/StockLighthouse/discussions)
- **Documentation**: Check component-specific READMEs

## 📄 License

This project is licensed under the MIT License. See LICENSE file for details.

## 🙏 Acknowledgments

- **yfinance** - Yahoo Finance API wrapper
- **FastAPI** - Modern Python web framework
- **React** - UI library
- **Plotly.js** - Interactive charting library
- **Pydantic** - Data validation framework

---

**Made with ❤️ by the StockLighthouse team**