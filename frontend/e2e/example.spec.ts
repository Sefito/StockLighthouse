import { test, expect } from '@playwright/test';

test('search and capture stock detail', async ({ page }) => {
  // Backend must be running at http://localhost:8000 and frontend dev at 5173
  await page.goto('http://localhost:5173');
  // Fill search box (adjust selector to match your app)
  await page.fill('input[type="text"]', 'AAPL,MSFT');
  await page.click('button:has-text("Fetch")');
  // Wait for results - adjust selectors as implemented
  await page.waitForSelector('pre');
  // Full page screenshot
  await page.screenshot({ path: 'search_results.png', fullPage: true });
  // Element screenshot example
  const pre = await page.$('pre');
  if (pre) {
    await pre.screenshot({ path: 'results_pre.png' });
  }
  // Basic assertion
  const content = await page.locator('pre').innerText();
  expect(content.length).toBeGreaterThan(10);
});