# StockLighthouse Frontend

A React + TypeScript frontend application for visualizing stock data and sector analysis.

## Features

- **Search Bar**: Auto-suggest search for stocks by symbol, sector, or industry
- **Stock Detail Page**: 
  - Comprehensive KPI table with key metrics
  - Interactive price history chart (30-day)
  - P/E ratio distribution chart comparing stocks within the same sector
- **Sector Dashboard**:
  - Color-coded heatmap tiles showing sector aggregates
  - Summary statistics (count, median P/E, market cap, etc.)
  - Interactive navigation to drill down into sectors

## Technology Stack

- **Framework**: React 19 with TypeScript
- **Build Tool**: Vite
- **Routing**: React Router v7
- **Charts**: Plotly.js (basic-dist)
- **Testing**: 
  - Unit tests: Vitest + Testing Library
  - E2E tests: Playwright
- **Styling**: CSS Modules + vanilla CSS

## Prerequisites

- Node.js 18+ and npm
- Backend API running on `http://localhost:8000`

## Installation

```bash
cd frontend
npm install
```

## Development

Start the development server with API proxy:

```bash
npm run dev
```

The app will be available at `http://localhost:5173`. The Vite dev server automatically proxies `/api` requests to the backend at `http://localhost:8000`.

## Building

Build the production bundle:

```bash
npm run build
```

The optimized build will be in the `dist/` directory.

Preview the production build:

```bash
npm run preview
```

## Testing

### Unit Tests

Run unit tests with Vitest:

```bash
npm test
```

Run tests in UI mode:

```bash
npm run test:ui
```

### E2E Tests

Make sure both backend and frontend are running, then run Playwright tests:

```bash
# Terminal 1: Start backend
cd backend
PYTHONPATH=src python -m uvicorn stocklighthouse.api.main:app --host 0.0.0.0 --port 8000

# Terminal 2: Start frontend
cd frontend
npm run dev

# Terminal 3: Run e2e tests
npm run e2e
```

Screenshots will be saved to `.test-results/screenshots/`.

## Project Structure

```
frontend/
├── src/
│   ├── components/          # Reusable components
│   │   ├── SearchBar.tsx    # Search with auto-suggest
│   │   ├── KPITable.tsx     # Stock KPI display
│   │   ├── PriceChart.tsx   # Price history chart
│   │   ├── PEChart.tsx      # P/E distribution chart
│   │   └── SectorHeatmap.tsx # Sector tiles heatmap
│   ├── pages/               # Page components
│   │   ├── HomePage.tsx     # Landing page with search
│   │   ├── StockDetailPage.tsx # Stock detail view
│   │   └── SectorDashboard.tsx # Sector overview
│   ├── services/            # API services
│   │   └── api.ts           # Backend API client
│   ├── types/               # TypeScript types
│   │   └── index.ts         # Shared type definitions
│   ├── tests/               # Unit tests
│   │   ├── SearchBar.test.tsx
│   │   └── KPITable.test.tsx
│   ├── App.tsx              # Main app with routing
│   └── main.tsx             # Entry point
├── e2e/                     # Playwright E2E tests
│   ├── home.spec.ts
│   ├── stock-detail.spec.ts
│   └── sector-dashboard.spec.ts
├── playwright.config.ts     # Playwright configuration
├── vite.config.ts           # Vite configuration
└── package.json
```

## API Integration

The frontend communicates with the backend via the following endpoints:

- `GET /api/stocks/search?q={query}` - Search stocks
- `GET /api/stocks/{symbol}` - Get stock details
- `GET /api/stocks/{symbol}/history` - Get price history
- `GET /api/stocks/{symbol}/pe-distribution` - Get P/E distribution
- `GET /api/sectors` - Get all sectors
- `GET /api/sectors/{sectorName}` - Get sector details

All API calls are defined in `src/services/api.ts`.

## Key Components

### SearchBar

Auto-suggest search component that:
- Debounces input (300ms)
- Searches across symbol, sector, and industry
- Displays results with price and sector info
- Navigates to stock detail on selection

### KPITable

Displays comprehensive stock metrics:
- Price, change %, market cap
- P/E ratio, P/B ratio, dividend yield
- Sector, industry, exchange info
- Formatted with color coding for positive/negative changes

### Charts (PriceChart & PEChart)

Interactive Plotly.js charts:
- Price history with 30-day data
- P/E distribution comparing sector peers
- Responsive and mobile-friendly
- Hover tooltips for detailed info

### SectorHeatmap

Visual sector overview:
- Color-coded tiles based on median P/E ratio
  - Green (<15): Undervalued
  - Yellow (15-25): Fair value
  - Orange (25-35): Moderate
  - Red (>35): Overvalued
- Shows count, median metrics, weighted P/E
- Displays top 3 stocks by market cap
- Clickable tiles for drill-down

## Linting

Run ESLint:

```bash
npm run lint
```

## Notes

- The backend must be running for the frontend to function
- Mock historical data is generated for demonstration
- All components are typed with TypeScript
- CSS is modular and scoped to components
- E2E tests require both services to be running
- Screenshots are automatically captured during E2E tests

## Troubleshooting

### Port already in use

If port 5173 is in use, Vite will automatically try the next available port. Check the terminal output for the actual port.

### API connection errors

Ensure the backend is running on port 8000. The Vite proxy is configured in `vite.config.ts`.

### Chart rendering issues

Plotly charts require the page to be fully loaded. E2E tests wait for the `.js-plotly-plot` selector to ensure charts are rendered.

## Future Enhancements

- Real-time data updates via WebSocket
- Historical data from real sources (not mock)
- More chart types (candlestick, volume)
- User portfolios and watchlists
- Advanced filtering and sorting
- Dark mode support
