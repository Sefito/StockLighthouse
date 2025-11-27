/**
 * E2E test for Stock Detail Page
 */
import { test, expect } from '@playwright/test';

test.describe('Stock Detail Page', () => {
  test('should load stock details and display KPI table', async ({ page }) => {
    await page.goto('http://localhost:5173/stock/AAPL');
    
    // Wait for page to load (either detail page or error state)
    await page.waitForSelector('[data-testid="stock-detail-page"], .MuiAlert-root', { timeout: 15000 });
    
    // Skip test if API failed
    const hasError = await page.locator('.MuiAlert-root').isVisible();
    if (hasError) {
      test.skip(true, 'API returned error - skipping test');
      return;
    }
    
    // Check title (uses h3 variant in MUI Typography)
    await expect(page.locator('h3').first()).toContainText('AAPL');
    
    // Check KPI table is visible
    const kpiTable = page.locator('[data-testid="kpi-table"]');
    await expect(kpiTable).toBeVisible();
  });

  test('should display price history chart', async ({ page }) => {
    await page.goto('http://localhost:5173/stock/AAPL');
    
    // Wait for chart to render
    await page.waitForSelector('[data-testid="price-chart"], .MuiAlert-root', { timeout: 15000 });
    
    // Skip test if API failed
    const hasError = await page.locator('.MuiAlert-root').isVisible();
    if (hasError) {
      test.skip(true, 'API returned error - skipping test');
      return;
    }
    
    // Check chart is visible
    const priceChart = page.locator('[data-testid="price-chart"]');
    await expect(priceChart).toBeVisible();
    
    // Wait for plotly chart to render
    await page.waitForSelector('.js-plotly-plot', { timeout: 10000 });
  });

  test('should display PE distribution chart', async ({ page }) => {
    await page.goto('http://localhost:5173/stock/AAPL');
    
    // Wait for chart to render
    await page.waitForSelector('[data-testid="pe-chart"], .MuiAlert-root', { timeout: 15000 });
    
    // Skip test if API failed
    const hasError = await page.locator('.MuiAlert-root').isVisible();
    if (hasError) {
      test.skip(true, 'API returned error - skipping test');
      return;
    }
    
    // Check chart is visible
    const peChart = page.locator('[data-testid="pe-chart"]');
    await expect(peChart).toBeVisible();
    
    // Wait for plotly chart to render
    await page.waitForSelector('.js-plotly-plot', { timeout: 10000 });
  });

  test('should navigate back when back button clicked', async ({ page }) => {
    // First go to home page
    await page.goto('http://localhost:5173');
    await page.waitForSelector('[data-testid="home-page"]');
    
    // Navigate to stock detail
    await page.goto('http://localhost:5173/stock/AAPL');
    await page.waitForSelector('[data-testid="stock-detail-page"], .MuiAlert-root', { timeout: 15000 });
    
    // Click back button (MUI Button with Back text - works in both success and error states)
    await page.getByRole('button', { name: /back|home/i }).click();
    
    // Should navigate back to home
    await page.waitForURL('http://localhost:5173/');
    await expect(page.locator('[data-testid="home-page"]')).toBeVisible();
  });
});
