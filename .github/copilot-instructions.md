# GitHub Copilot Instructions for StockLighthouse

## Project Overview
StockLighthouse is a stock data analysis platform with:
- **Backend**: Python 3.10, FastAPI, yfinance for data ingestion
- **Frontend**: React + TypeScript, Vite build system, Plotly for charts
- **Testing**: pytest for backend, Playwright for frontend E2E
- **Deployment**: Docker + docker-compose
- **Custom Agents**: Specialized agents for domain-specific tasks

## Repository Structure
```
StockLighthouse/
├── backend/
│   ├── src/stocklighthouse/    # Backend source code
│   ├── tests/                  # pytest tests
│   └── requirements.txt        # Python dependencies
├── frontend/
│   ├── src/                    # React components and pages
│   ├── e2e/                    # Playwright E2E tests
│   └── package.json            # Node dependencies
├── .github/
│   ├── agents/                 # Custom agent instructions
│   ├── workflows/              # CI/CD workflows
│   └── ISSUE_TEMPLATE/         # Issue templates
└── docker-compose.yml          # Docker orchestration
```

## Development Environment Setup

### Backend Setup
```bash
cd backend
python -m pip install -r requirements.txt
export PYTHONPATH=/path/to/backend/src
uvicorn stocklighthouse.api.main:app --host 0.0.0.0 --port 8000
```

### Frontend Setup
```bash
cd frontend
npm ci
npm run dev  # Development server on port 5173
npm run build  # Production build
npm run preview  # Preview production build
```

### Docker Setup
```bash
docker-compose up --build
# Backend: http://localhost:8000
# Frontend: http://localhost:5173
```

## Building and Testing

### Backend Testing
```bash
cd backend
pytest -q  # Run all backend tests
pytest tests/test_normalizer.py -v  # Run specific test
```

### Frontend Testing
```bash
cd frontend
npm run build  # Must build before E2E tests
npx playwright test --config=playwright.config.ts
```

### CI/CD
- Workflow: `.github/workflows/agents_ci.yml`
- Backend tests run first, then frontend E2E tests
- Screenshots uploaded to `.test-results/screenshots/`

## Coding Standards

### Python (Backend)
- Python 3.10 syntax
- Use FastAPI for API endpoints
- Follow PEP 8 style guidelines
- Add type hints to functions
- Use pytest for testing
- Keep test files in `backend/tests/` with `test_` prefix
- Set `PYTHONPATH` to include `backend/src`

### TypeScript/React (Frontend)
- TypeScript strict mode
- React functional components with hooks
- Use Vite for building
- Plotly.js for data visualization
- Playwright for E2E testing with screenshots
- Save screenshots to `.test-results/screenshots/<issue-number>/`

### Testing Requirements
- **Backend**: pytest tests for all new functionality
- **Frontend**: Playwright E2E tests for UI features
- **UI Changes**: Must include screenshots in PR
- **Test Coverage**: Unit tests for critical components

## Pull Request Guidelines
- Follow template in `.github/PULL_REQUEST_TEMPLATE.md`
- Include "How to run locally" section
- Add tests (pytest for backend, Playwright for UI)
- Include screenshots for UI changes
- Link related agent task issues
- Use labels: `agent-task`, `qa-needed`, `review-request`

## Branch Naming
- Format: `agent/<agent-name>/<short-description>`
- Examples: `agent/frontend/add-search-bar`, `agent/backend/fix-api-route`

## Custom Agents
Custom agents are available for specialized tasks:
- `frontend_agent` - React + TypeScript frontend development
- `ingestor_agent` - yfinance-based data ingestion
- `normalizer_agent` - KPI mapping and data parsing
- `analyzer` - Sector aggregation and metrics
- `devops_agent` - CI/CD, Docker, dev environment
- `qa_agent` - Testing and QA
- `docs_agent` - Documentation

Delegate tasks to relevant agents when available - they have domain-specific expertise.

## Dependencies

### Adding Python Dependencies
```bash
cd backend
# Add to requirements.txt
pip install -r requirements.txt
```

### Adding Node Dependencies
```bash
cd frontend
npm install <package-name>
# Updates package.json and package-lock.json
```

## Security
- Never commit secrets or API keys
- Use environment variables for sensitive data
- Run security scans before finalizing PRs
- Validate user input in API endpoints
- Use proper authentication for API routes

## API Conventions
- Backend API runs on port 8000
- Frontend proxies `/api` requests to backend
- FastAPI auto-generates OpenAPI docs at `/docs`
- Follow REST conventions for endpoints

## File Locations
- Backend source: `backend/src/stocklighthouse/`
- Backend tests: `backend/tests/`
- Frontend components: `frontend/src/components/`
- Frontend pages: `frontend/src/pages/`
- E2E tests: `frontend/e2e/`
- Screenshots: `.test-results/screenshots/`
- Docker configs: Root level `Dockerfile.*` and `docker-compose.yml`

## Documentation
- Update README.md for major changes
- Include inline comments for complex logic
- Document API endpoints in FastAPI route handlers
- Add JSDoc comments for complex React components

## Common Tasks

### Running Locally
1. Start backend: `cd backend && uvicorn stocklighthouse.api.main:app --port 8000`
2. Start frontend: `cd frontend && npm run dev`
3. Access: Frontend at http://localhost:5173, Backend at http://localhost:8000

### Adding a New Feature
1. Create issue using "Agent Task" template
2. Create branch: `agent/<agent-name>/<feature-name>`
3. Implement feature with tests
4. Run tests: backend `pytest`, frontend `npm run build && npx playwright test`
5. Create PR with screenshots (if UI changes)
6. Ensure CI passes

### Debugging Failed CI
1. Check `.github/workflows/agents_ci.yml`
2. Backend tests fail: `cd backend && pytest -v`
3. Frontend tests fail: Check Playwright logs and screenshots
4. Build fails: Check `npm run build` or Docker build logs
