# Frontend E2E Tests

This directory contains end-to-end (E2E) tests for the StockLighthouse frontend using Playwright.

## Test Structure

```
e2e/
├── home.spec.ts              # Home page tests (3 tests)
├── sector-dashboard.spec.ts  # Sector dashboard tests (5 tests)
└── stock-detail.spec.ts      # Stock detail page tests (4 tests)
```

**Total: 12 E2E tests**

## Running Tests

### Prerequisites

```bash
cd frontend
npm ci
npx playwright install chromium
```

### Run All E2E Tests

```bash
cd frontend
npm run e2e
```

### Run in Headed Mode

```bash
cd frontend
npx playwright test --headed
```

### Run Specific Test File

```bash
cd frontend
npx playwright test e2e/home.spec.ts
```

### Run in UI Mode (Interactive)

```bash
cd frontend
npx playwright test --ui
```

### Debug Tests

```bash
cd frontend
npx playwright test --debug
```

## Test Coverage

### Home Page Tests (3 tests)

**home.spec.ts** - Tests for `/` route

- ✅ Load and display search bar
  - Verifies page loads
  - Checks title presence
  - Validates search input visibility
  - Captures full page and hero section screenshots
  
- ✅ Display popular stocks list
  - Waits for stock data to load
  - Validates stock cards are visible
  - Captures stock list screenshot
  
- ✅ Navigate to stock detail page
  - Tests click navigation
  - Verifies URL change
  - Confirms detail page loads

### Sector Dashboard Tests (5 tests)

**sector-dashboard.spec.ts** - Tests for `/sectors` route

- ✅ Load and display sector tiles
  - Verifies dashboard loads
  - Checks title and heatmap
  - Captures full page screenshot
  
- ✅ Display dashboard statistics
  - Validates stat cards (3 cards)
  - Captures statistics screenshot
  
- ✅ Display sector heatmap with color coding
  - Verifies sector tiles render
  - Checks color coding
  - Captures heatmap screenshot
  
- ✅ Display legend
  - Checks legend visibility
  - Validates legend content
  - Captures legend screenshot
  
- ✅ Navigate to home
  - Tests back button functionality
  - Verifies navigation works

### Stock Detail Tests (4 tests)

**stock-detail.spec.ts** - Tests for `/stock/:symbol` route

- ✅ Load stock details and display KPI table
  - Tests with AAPL symbol
  - Validates KPI table
  - Captures full page and KPI table screenshots
  
- ✅ Display price history chart
  - Waits for Plotly chart to render
  - Validates chart visibility
  - Captures chart screenshot
  
- ✅ Display PE distribution chart
  - Validates PE chart renders
  - Captures chart screenshot
  
- ✅ Navigate back and to sector page
  - Tests sector button navigation
  - Verifies conditional navigation

## Visual Regression Testing

All tests include visual regression checks using Playwright's `toHaveScreenshot()`:

```typescript
// Full page screenshot
await expect(page).toHaveScreenshot('home-page-full.png', {
  fullPage: true,
  animations: 'disabled',
});

// Element screenshot
await expect(element).toHaveScreenshot('element.png', {
  animations: 'disabled',
});
```

### Screenshot Locations

- **Baselines:** `e2e/*-snapshots/` (Playwright managed)
- **Current:** `.test-results/screenshots/`
- **Diffs:** `.test-results/` (on failures)

### Managing Baselines

Update baselines after approved visual changes:

```bash
cd frontend
npx playwright test --update-snapshots
```

View test report with visual diffs:

```bash
cd frontend
npx playwright show-report
```

## Configuration

### Playwright Config

File: `playwright.config.ts`

Key settings:
```typescript
{
  testDir: './e2e',
  outputDir: '.test-results/screenshots',
  fullyParallel: true,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  use: {
    baseURL: 'http://localhost:5173',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
  },
  expect: {
    toHaveScreenshot: {
      maxDiffPixels: 100,
      threshold: 0.2,
    },
  },
}
```

### Visual Regression Thresholds

- **maxDiffPixels:** 100 (maximum different pixels allowed)
- **threshold:** 0.2 (20% color difference threshold)

Adjust in `playwright.config.ts` if needed.

## Writing New Tests

### Test Structure

```typescript
import { test, expect } from '@playwright/test';

test.describe('Feature Name', () => {
  test('should do something', async ({ page }) => {
    // Navigate to page
    await page.goto('http://localhost:5173/path');
    
    // Wait for content
    await page.waitForSelector('[data-testid="element"]');
    
    // Assertions
    await expect(page.locator('h1')).toContainText('Title');
    
    // Visual regression
    await expect(page).toHaveScreenshot('feature-name.png', {
      fullPage: true,
      animations: 'disabled',
    });
  });
});
```

### Best Practices

#### Use Data Test IDs

```typescript
// Good - use data-testid
await page.locator('[data-testid="search-input"]').fill('AAPL');

// Avoid - CSS classes can change
await page.locator('.search-input').fill('AAPL');
```

#### Wait for Content

```typescript
// Wait for specific element
await page.waitForSelector('[data-testid="stock-list"]');

// Wait for network idle
await page.waitForLoadState('networkidle');

// Wait for condition
await page.waitForFunction(() => window.dataLoaded === true);
```

#### Disable Animations

```typescript
// In test
await expect(page).toHaveScreenshot('page.png', {
  animations: 'disabled',
});

// Or globally
await page.emulateMedia({ reducedMotion: 'reduce' });
```

#### Handle Dynamic Content

```typescript
// Mock API responses
await page.route('**/api/stocks', route => {
  route.fulfill({
    status: 200,
    body: JSON.stringify({ data: mockData }),
  });
});

// Or wait for specific content
await page.waitForSelector('text=Expected Content');
```

## Test Selectors

### Recommended Selector Priority

1. **data-testid:** `[data-testid="element"]` ✅ Best
2. **aria labels:** `page.getByRole('button', { name: 'Submit' })` ✅ Good
3. **text content:** `page.getByText('Click me')` ⚠️ OK
4. **CSS classes:** `.button-class` ❌ Avoid

### Adding Test IDs

In React components:

```tsx
<div data-testid="stock-card">
  <h2 data-testid="stock-symbol">{symbol}</h2>
  <span data-testid="stock-price">${price}</span>
</div>
```

## Debugging

### View Browser

```bash
npx playwright test --headed
```

### Slow Motion

```bash
npx playwright test --headed --slow-mo=1000
```

### Debug Specific Test

```bash
npx playwright test e2e/home.spec.ts --debug
```

### Inspector

```bash
npx playwright codegen http://localhost:5173
```

This opens inspector to generate test code.

### Trace Viewer

For failed tests, view traces:

```bash
npx playwright show-trace .test-results/trace.zip
```

## CI/CD Integration

Tests run automatically in GitHub Actions:

### CI Configuration

File: `.github/workflows/agents_ci.yml`

Jobs:
1. **frontend-e2e:** Runs all E2E tests
2. **visual-regression:** Compares screenshots (PRs only)

### CI Artifacts

Available in GitHub Actions:
- `playwright-report`: HTML test report
- `screenshots`: Test screenshots
- `visual-baselines`: Baseline screenshots (master)
- `visual-diffs`: Diff images (on failures)

## Troubleshooting

### Tests Fail Locally

**Problem:** `Error: connect ECONNREFUSED`

**Solution:** Ensure services are running:
```bash
# Terminal 1: Backend
cd backend
PYTHONPATH=src uvicorn stocklighthouse.api.main:app --port 8000

# Terminal 2: Frontend
cd frontend
npm run dev
```

### Timeout Errors

**Problem:** `Timeout 30000ms exceeded`

**Solution:** Increase timeout:
```typescript
await page.waitForSelector('[data-testid="element"]', { 
  timeout: 15000 
});
```

### Visual Regression Failures

**Problem:** Screenshot comparison fails

**Solutions:**
1. Review diff: `npx playwright show-report`
2. If changes are intentional: `npx playwright test --update-snapshots`
3. If environment issue: Check font rendering, viewport size

### Browser Not Found

**Problem:** `browserType.launch: Executable doesn't exist`

**Solution:**
```bash
npx playwright install chromium
```

### Flaky Tests

**Problem:** Tests pass/fail inconsistently

**Solutions:**
- Add proper wait conditions
- Disable animations
- Mock network requests
- Use `waitForLoadState('networkidle')`

## Performance

### Test Execution Time

Target times:
- Home tests: ~10-15 seconds
- Sector tests: ~15-20 seconds
- Stock detail tests: ~20-25 seconds

**Total: ~5 minutes for full suite**

### Optimization Tips

- Run in parallel (default in config)
- Use `test.describe.serial()` for dependent tests
- Mock slow API calls
- Reuse browser context when possible

## Related Documentation

- [Main Testing Guide](../../tests/README.md)
- [Visual Regression Guide](../../tests/VISUAL_REGRESSION.md)
- [QA Checklist](../../tests/QA_CHECKLIST.md)
- [Playwright Documentation](https://playwright.dev/)

## Contributing

When adding new E2E tests:

1. Use descriptive test names
2. Add data-testid attributes to new components
3. Include visual regression checks
4. Mock external APIs
5. Handle loading states
6. Add proper wait conditions
7. Update this README with new test descriptions
8. Update visual baselines if needed
