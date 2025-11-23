# StockLighthouse QA & Testing Guide

This guide provides comprehensive instructions for running tests, performing QA, and managing visual regression testing for StockLighthouse.

---

## 📋 Table of Contents

1. [Quick Start](#quick-start)
2. [Backend Testing](#backend-testing)
3. [Frontend E2E Testing](#frontend-e2e-testing)
4. [Visual Regression Testing](#visual-regression-testing)
5. [CI/CD Integration](#cicd-integration)
6. [QA Workflow](#qa-workflow)
7. [Troubleshooting](#troubleshooting)

---

## 🚀 Quick Start

### Prerequisites

**Backend:**
- Python 3.10+
- pip

**Frontend:**
- Node.js 18+
- npm

### Installation

```bash
# Backend dependencies
cd backend
pip install -r requirements.txt

# Frontend dependencies
cd frontend
npm ci

# Install Playwright browsers
npx playwright install chromium
```

### Run All Tests

```bash
# Backend tests
cd backend
PYTHONPATH=src pytest tests/ -v

# Frontend E2E tests (requires backend and frontend running)
cd frontend
npm run e2e
```

---

## 🔬 Backend Testing

### Test Structure

```
backend/tests/
├── test_analyzer.py      # Tests for sector aggregation and analytics
├── test_ingestor.py      # Tests for data ingestion and caching
└── test_normalizer.py    # Tests for data normalization
```

### Running Backend Tests

#### Run all tests with verbose output:
```bash
cd backend
PYTHONPATH=src pytest tests/ -v
```

#### Run specific test file:
```bash
cd backend
PYTHONPATH=src pytest tests/test_normalizer.py -v
```

#### Run specific test:
```bash
cd backend
PYTHONPATH=src pytest tests/test_normalizer.py::test_normalize_minimal -v
```

#### Run with coverage report:
```bash
cd backend
PYTHONPATH=src pytest tests/ -v --cov=stocklighthouse --cov-report=html
# View coverage: open htmlcov/index.html
```

#### Run tests in parallel:
```bash
cd backend
PYTHONPATH=src pytest tests/ -v -n auto
```

### Test Coverage

Current backend test coverage:
- **Normalizer:** 32 tests covering edge cases, type safety, and real-world scenarios
- **Analyzer:** 27 tests covering sector aggregation and weighted averages
- **Ingestor:** 19 tests covering caching, retry logic, and error handling

**Total: 78 tests**

### Adding New Backend Tests

1. Create a new test file in `backend/tests/` with prefix `test_`
2. Import the module you're testing
3. Use descriptive test names: `test_<function>_<scenario>`
4. Use pytest fixtures for reusable test data
5. Mock external dependencies (e.g., yfinance API calls)

Example:
```python
import pytest
from stocklighthouse.normalizer import normalize

def test_normalize_handles_missing_data():
    """Test that normalizer handles missing data gracefully."""
    raw = {}
    result = normalize("TEST", raw)
    assert result.symbol == "TEST"
    assert result.price is None
```

---

## 🎭 Frontend E2E Testing

### Test Structure

```
frontend/e2e/
├── home.spec.ts              # Home page tests
├── sector-dashboard.spec.ts  # Sector dashboard tests
└── stock-detail.spec.ts      # Stock detail page tests
```

### Running E2E Tests

#### Prerequisites:
Make sure backend and frontend are running:

```bash
# Terminal 1: Start backend
cd backend
PYTHONPATH=src uvicorn stocklighthouse.api.main:app --reload --port 8000

# Terminal 2: Start frontend
cd frontend
npm run dev
```

#### Run all E2E tests:
```bash
cd frontend
npm run e2e
```

#### Run tests in headed mode (see browser):
```bash
cd frontend
npx playwright test --headed
```

#### Run specific test file:
```bash
cd frontend
npx playwright test e2e/home.spec.ts
```

#### Run with UI mode (interactive):
```bash
cd frontend
npx playwright test --ui
```

#### Debug a specific test:
```bash
cd frontend
npx playwright test e2e/home.spec.ts --debug
```

### Test Artifacts

After running tests, artifacts are saved in:
- **Screenshots:** `frontend/.test-results/screenshots/`
- **Test results:** `frontend/playwright-report/`
- **Traces:** `frontend/.test-results/` (for failed tests)

View test report:
```bash
cd frontend
npx playwright show-report
```

### Adding New E2E Tests

1. Create a new `.spec.ts` file in `frontend/e2e/`
2. Import Playwright test utilities
3. Use descriptive test names
4. Add visual regression checks with `toHaveScreenshot()`

Example:
```typescript
import { test, expect } from '@playwright/test';

test.describe('My Feature', () => {
  test('should display correctly', async ({ page }) => {
    await page.goto('http://localhost:5173/my-feature');
    
    // Wait for content
    await page.waitForSelector('[data-testid="my-element"]');
    
    // Assertions
    await expect(page.locator('h1')).toContainText('My Feature');
    
    // Visual regression
    await expect(page).toHaveScreenshot('my-feature.png', {
      fullPage: true,
      animations: 'disabled',
    });
  });
});
```

---

## 📸 Visual Regression Testing

Visual regression testing helps detect unintended UI changes by comparing screenshots.

### How It Works

1. **Baseline Creation:** First run creates baseline screenshots
2. **Comparison:** Subsequent runs compare against baselines
3. **Diff Generation:** Differences are highlighted in diff images
4. **Approval:** Review and approve or reject changes

### Using Playwright's Built-in Visual Testing

Playwright automatically manages visual regression:

```typescript
// Full page screenshot
await expect(page).toHaveScreenshot('page-name.png', {
  fullPage: true,
  animations: 'disabled',
});

// Element screenshot
await expect(element).toHaveScreenshot('element-name.png', {
  animations: 'disabled',
});
```

**First run:** Creates baseline in `e2e/**/*-snapshots/`  
**Subsequent runs:** Compares against baseline  
**Update baselines:** `npx playwright test --update-snapshots`

### Using Custom Visual Diff Utility

For more control, use the custom visual diff script:

```bash
# Compare screenshots
node tests/utils/visual-diff.js \
  tests/baseline \
  frontend/.test-results/screenshots \
  tests/diff \
  0.1
```

**Arguments:**
- `tests/baseline`: Directory with baseline screenshots
- `frontend/.test-results/screenshots`: Directory with current screenshots
- `tests/diff`: Output directory for diff images
- `0.1`: Threshold (10% difference allowed)

### Managing Baselines

#### Update baselines after approved changes:
```bash
cd frontend
npx playwright test --update-snapshots
```

#### Copy screenshots to baseline directory:
```bash
cp frontend/.test-results/screenshots/*.png tests/baseline/
```

#### Commit new baselines:
```bash
git add frontend/e2e/**/*-snapshots/
git add tests/baseline/
git commit -m "Update visual regression baselines"
```

### Visual Diff Configuration

Configure visual regression in `playwright.config.ts`:

```typescript
expect: {
  toHaveScreenshot: {
    maxDiffPixels: 100,    // Maximum different pixels
    threshold: 0.2,         // Threshold for pixel difference (0-1)
  },
},
```

---

## 🔄 CI/CD Integration

### GitHub Actions Workflow

The `agents_ci.yml` workflow runs automatically on:
- Push to `master` branch
- Pull requests to `master` branch

### Workflow Jobs

1. **backend-tests:** Runs all backend pytest tests
2. **frontend-e2e:** Runs Playwright E2E tests with visual snapshots
3. **visual-regression:** Compares screenshots against baselines (PR only)

### Viewing Test Results

#### In GitHub:
1. Go to Actions tab
2. Select the workflow run
3. View job logs and test results
4. Download artifacts (screenshots, diffs, reports)

#### Artifacts Available:
- `playwright-report`: Full test report
- `screenshots`: Current test screenshots
- `visual-baselines`: Baseline screenshots (master branch)
- `visual-diffs`: Diff images (if tests fail)

### PR Comments

On pull requests, the bot automatically comments with:
- ✅ Visual tests passed
- ⚠️ Visual differences detected
- ℹ️ No baselines found

---

## 🔍 QA Workflow

### For Each PR

1. **Automated Tests**
   - [ ] Review CI/CD test results
   - [ ] Download and review screenshots
   - [ ] Check for visual regressions

2. **Manual Testing**
   - [ ] Follow QA checklist: `tests/QA_CHECKLIST.md`
   - [ ] Test on different browsers (Chrome, Firefox, Safari)
   - [ ] Test responsive design (mobile, tablet, desktop)

3. **Code Review**
   - [ ] Review test changes
   - [ ] Verify test coverage
   - [ ] Check for proper assertions

4. **Approval**
   - [ ] All tests passing
   - [ ] Visual changes approved
   - [ ] Code reviewed
   - [ ] QA checklist completed

### Local QA Commands

```bash
# Run all tests
make test  # If Makefile exists

# Or manually:
cd backend && PYTHONPATH=src pytest tests/ -v
cd frontend && npm run e2e

# Generate and review visual diffs
node tests/utils/visual-diff.js tests/baseline frontend/.test-results/screenshots tests/diff 0.1

# Review artifacts
open frontend/playwright-report/index.html
open tests/diff/
```

---

## 🔧 Troubleshooting

### Backend Tests Fail

**Issue:** `ModuleNotFoundError: No module named 'stocklighthouse'`

**Solution:** Set PYTHONPATH:
```bash
cd backend
PYTHONPATH=src pytest tests/ -v
```

**Issue:** Tests fail with network errors

**Solution:** Tests should use mocks. Check test file for proper mocking:
```python
@patch('stocklighthouse.ingest.yfinance_ingestor.yf.Ticker')
def test_fetch_ticker(mock_ticker_class):
    # Test implementation
```

### E2E Tests Fail

**Issue:** `Error: connect ECONNREFUSED`

**Solution:** Ensure backend and frontend are running:
```bash
# Check if services are running
curl http://localhost:8000/health
curl http://localhost:5173
```

**Issue:** Timeout waiting for selector

**Solution:** Increase timeout or check if element exists:
```typescript
await page.waitForSelector('[data-testid="element"]', { 
  timeout: 15000 
});
```

**Issue:** Visual regression tests fail

**Solution:** 
1. Review diff images in `tests/diff/`
2. If changes are intentional: `npx playwright test --update-snapshots`
3. Commit updated baselines

### Playwright Issues

**Issue:** Browser not installed

**Solution:**
```bash
cd frontend
npx playwright install chromium
```

**Issue:** Tests are flaky

**Solution:**
- Disable animations: `animations: 'disabled'`
- Wait for network idle: `await page.waitForLoadState('networkidle')`
- Use proper selectors: `data-testid` attributes

### Visual Diff Script Issues

**Issue:** `Cannot find module 'pngjs'`

**Solution:**
```bash
npm install pngjs
```

**Issue:** Directory not found

**Solution:** Ensure directories exist:
```bash
mkdir -p tests/baseline tests/diff
```

---

## 📚 Additional Resources

- [Playwright Documentation](https://playwright.dev/)
- [Pytest Documentation](https://docs.pytest.org/)
- [Visual Regression Testing Best Practices](https://playwright.dev/docs/test-snapshots)
- [QA Checklist](./QA_CHECKLIST.md)

---

## 🤝 Contributing

When adding new tests:

1. Follow existing test patterns
2. Use descriptive test names
3. Add visual regression for UI changes
4. Update this documentation
5. Update QA checklist if needed

---

## 📞 Support

For questions or issues:
1. Check this documentation
2. Review troubleshooting section
3. Open an issue on GitHub
4. Contact the development team
