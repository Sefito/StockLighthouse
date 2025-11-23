# Visual Regression Testing Guide

This guide explains how to use visual regression testing in StockLighthouse to detect unintended UI changes.

---

## 📖 Overview

Visual regression testing compares screenshots of your UI before and after changes. It helps catch:
- Layout shifts
- Color changes
- Font modifications
- Spacing issues
- Missing or moved elements

---

## 🎯 When to Use Visual Regression

Use visual regression testing for:
- ✅ UI component changes
- ✅ CSS/styling updates
- ✅ Layout modifications
- ✅ New features with visual elements
- ✅ Responsive design changes

Skip for:
- ❌ Pure backend logic
- ❌ API-only changes
- ❌ Documentation updates

---

## 🛠️ Tools Used

### 1. Playwright Built-in Visual Testing
Playwright provides `toHaveScreenshot()` matcher for pixel-perfect comparisons.

**Pros:**
- Integrated with test framework
- Automatic baseline management
- Cross-browser support
- Simple API

**Cons:**
- Strict pixel comparison (can be sensitive)
- Requires baseline updates for intentional changes

### 2. Custom Visual Diff Script
Our custom `visual-diff.js` provides more flexibility.

**Pros:**
- Configurable threshold
- Detailed diff reports
- Works with any screenshot source
- Custom diff highlighting

**Cons:**
- Requires separate execution
- Manual baseline management

---

## 📸 Using Playwright Visual Testing

### Basic Usage

```typescript
import { test, expect } from '@playwright/test';

test('homepage looks correct', async ({ page }) => {
  await page.goto('http://localhost:5173');
  
  // Wait for content to load
  await page.waitForSelector('[data-testid="home-page"]');
  
  // Take screenshot and compare
  await expect(page).toHaveScreenshot('homepage.png');
});
```

### Full Page Screenshots

```typescript
await expect(page).toHaveScreenshot('homepage-full.png', {
  fullPage: true,
});
```

### Element Screenshots

```typescript
const header = page.locator('header');
await expect(header).toHaveScreenshot('header.png');
```

### Configuration Options

```typescript
await expect(page).toHaveScreenshot('page.png', {
  fullPage: true,              // Capture entire page
  animations: 'disabled',      // Disable animations
  maxDiffPixels: 100,          // Allow up to 100 different pixels
  threshold: 0.2,              // 20% color difference threshold
  clip: { x: 0, y: 0, width: 800, height: 600 }, // Crop region
});
```

### Best Practices

1. **Disable animations:** Always set `animations: 'disabled'`
2. **Wait for content:** Ensure dynamic content is loaded
3. **Consistent environment:** Use same viewport size
4. **Descriptive names:** Use clear screenshot names

Example:
```typescript
test('stock detail page displays correctly', async ({ page }) => {
  await page.goto('http://localhost:5173/stock/AAPL');
  
  // Wait for dynamic content
  await page.waitForSelector('[data-testid="stock-detail-page"]');
  await page.waitForLoadState('networkidle');
  
  // Disable animations
  await page.emulateMedia({ reducedMotion: 'reduce' });
  
  // Take screenshot
  await expect(page).toHaveScreenshot('stock-detail-aapl.png', {
    fullPage: true,
    animations: 'disabled',
  });
});
```

---

## 🔄 Managing Baselines

### First Run: Creating Baselines

When you first run a test with `toHaveScreenshot()`, Playwright creates a baseline:

```bash
cd frontend
npx playwright test
```

Baselines are stored in:
```
frontend/e2e/
  home.spec.ts-snapshots/
    homepage-chromium.png
  sector-dashboard.spec.ts-snapshots/
    sector-dashboard-full-chromium.png
```

### Updating Baselines

When UI changes are intentional:

```bash
# Update all baselines
npx playwright test --update-snapshots

# Update specific test baselines
npx playwright test home.spec.ts --update-snapshots

# Update in headed mode (see what's captured)
npx playwright test --update-snapshots --headed
```

### Reviewing Changes

Before updating baselines:

1. **Run tests:** `npx playwright test`
2. **Review failures:** Check which tests failed
3. **View diffs:** Open `playwright-report/index.html`
4. **Inspect screenshots:** Look at actual vs expected
5. **Decide:** Are changes intentional?
6. **Update if needed:** `npx playwright test --update-snapshots`

### Committing Baselines

Always commit baseline screenshots:

```bash
git add frontend/e2e/**/*-snapshots/
git commit -m "Update visual regression baselines for header redesign"
git push
```

---

## 🔧 Using Custom Visual Diff Script

### Installation

The script requires `pngjs`:

```bash
npm install pngjs
```

### Basic Usage

```bash
node tests/utils/visual-diff.js \
  <baseline-dir> \
  <current-dir> \
  <diff-dir> \
  [threshold]
```

### Example

```bash
# Compare current screenshots against baseline
node tests/utils/visual-diff.js \
  tests/baseline \
  frontend/.test-results/screenshots \
  tests/diff \
  0.1
```

**Parameters:**
- `tests/baseline`: Directory with baseline screenshots
- `frontend/.test-results/screenshots`: Current screenshots
- `tests/diff`: Output directory for diff images
- `0.1`: 10% difference threshold (optional, default: 0.1)

### Output

The script provides:
- ✅ Pass/fail status for each screenshot
- 📊 Difference percentage
- 🖼️ Highlighted diff images (red highlights)
- 📝 Summary report

Example output:
```
🔍 Visual Regression Testing
Baseline: tests/baseline
Current:  frontend/.test-results/screenshots
Diff:     tests/diff
Threshold: 10.00%
---
✅ home-page-full.png: Passed (diff: 0.02%)
✅ home-page-hero.png: Passed (diff: 0.15%)
❌ sector-dashboard-full.png: Difference 12.45% exceeds threshold 10.00%
---
📊 Summary:
Total tests: 3
✅ Passed: 2
❌ Failed: 1
```

### Interpreting Diff Images

Diff images use color coding:
- **Red pixels:** Differences between baseline and current
- **Gray pixels:** Identical areas (semi-transparent)

Review diff images:
```bash
open tests/diff/sector-dashboard-full.png
```

---

## 🔍 Debugging Visual Regressions

### Common Causes

1. **Dynamic Content**
   - Timestamps
   - Random data
   - Live stock prices
   
   **Solution:** Mock data or use fixed timestamps

2. **Animations**
   - CSS transitions
   - Loading spinners
   - Hover effects
   
   **Solution:** Disable animations in tests

3. **Font Rendering**
   - Different OS font rendering
   - Font loading delays
   
   **Solution:** Wait for fonts to load, use consistent environment

4. **Viewport Size**
   - Different screen resolutions
   - Responsive breakpoints
   
   **Solution:** Set explicit viewport size

### Debugging Techniques

#### 1. Run in Headed Mode

```bash
npx playwright test --headed --debug
```

#### 2. Add Wait Conditions

```typescript
// Wait for fonts
await page.waitForLoadState('networkidle');

// Wait for animations
await page.waitForTimeout(500);

// Wait for specific content
await page.waitForSelector('.content-loaded');
```

#### 3. Mask Dynamic Content

```typescript
await expect(page).toHaveScreenshot('page.png', {
  mask: [page.locator('.timestamp')], // Mask timestamps
});
```

#### 4. Increase Threshold

```typescript
await expect(page).toHaveScreenshot('page.png', {
  maxDiffPixels: 200,  // Allow more differences
  threshold: 0.3,      // Higher threshold
});
```

---

## 📋 Visual Regression Workflow

### For Developers

1. **Make UI changes**
2. **Run tests locally:**
   ```bash
   cd frontend
   npm run e2e
   ```
3. **Review failures:** Check if differences are expected
4. **Update baselines if needed:**
   ```bash
   npx playwright test --update-snapshots
   ```
5. **Commit changes:**
   ```bash
   git add frontend/e2e/**/*-snapshots/
   git commit -m "Update baselines for button redesign"
   ```
6. **Push to PR**

### For Reviewers

1. **Check CI results:** Review GitHub Actions output
2. **Download artifacts:** Get screenshots and diffs
3. **Review diffs:** Look at visual changes
4. **Approve or request changes:**
   - ✅ Approve if changes look correct
   - ❌ Request changes if unintended

### In CI/CD

The workflow automatically:
1. Runs E2E tests with screenshot capture
2. Compares against baselines (PR only)
3. Uploads screenshots and diffs as artifacts
4. Comments on PR with results

---

## ⚙️ Configuration

### Playwright Config

Edit `frontend/playwright.config.ts`:

```typescript
export default defineConfig({
  expect: {
    toHaveScreenshot: {
      maxDiffPixels: 100,     // Max different pixels
      threshold: 0.2,         // Color difference threshold
      animations: 'disabled', // Disable animations
    },
  },
});
```

### Visual Diff Script

Modify `tests/utils/visual-diff.js`:

```javascript
// Change default threshold
const threshold = thresholdStr ? parseFloat(thresholdStr) : 0.1;

// Adjust color difference sensitivity
const isDifferent = Math.abs(r1 - r2) > 10 || 
                    Math.abs(g1 - g2) > 10 || 
                    Math.abs(b1 - b2) > 10;
```

---

## 🏆 Best Practices

### DO ✅

- **Use descriptive names:** `stock-detail-aapl.png` not `test1.png`
- **Disable animations:** Always set `animations: 'disabled'`
- **Wait for content:** Ensure page is fully loaded
- **Test responsive:** Cover different viewport sizes
- **Review before updating:** Always check diffs before updating baselines
- **Commit baselines:** Include screenshots in version control
- **Document changes:** Note why baselines were updated

### DON'T ❌

- **Don't ignore failures:** Always investigate visual differences
- **Don't skip reviews:** Visual changes need human review
- **Don't test dynamic data:** Mock timestamps, random data
- **Don't use huge thresholds:** Keep threshold < 20%
- **Don't forget CI:** Ensure tests pass in CI before merge

---

## 🐛 Troubleshooting

### Tests Fail Locally but Pass in CI

**Cause:** Different rendering environments

**Solution:**
- Use consistent viewport size
- Disable font anti-aliasing differences
- Run in Docker for consistency

### Baselines Keep Changing

**Cause:** Non-deterministic rendering

**Solution:**
- Mock dynamic data (dates, prices)
- Wait for animations to complete
- Use `networkidle` load state

### High Diff Percentages

**Cause:** Major visual changes or environment differences

**Solution:**
- Review actual changes
- Increase threshold if appropriate
- Update baselines if intentional

---

## 📚 Resources

- [Playwright Visual Comparisons](https://playwright.dev/docs/test-snapshots)
- [Visual Testing Best Practices](https://playwright.dev/docs/best-practices)
- [QA Checklist](./QA_CHECKLIST.md)
- [Testing Guide](./README.md)

---

## 🤝 Contributing

When adding new visual tests:

1. Create meaningful test scenarios
2. Use consistent naming
3. Document expected behavior
4. Update this guide if needed
5. Review diffs carefully before committing baselines
