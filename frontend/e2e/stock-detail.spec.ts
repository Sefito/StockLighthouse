/**
 * E2E test for Stock Detail Page
 */
import { test, expect } from '@playwright/test';

test.describe('Stock Detail Page', () => {
  test('should load stock details and display KPI table', async ({ page }) => {
    await page.goto('http://localhost:5173/stock/AAPL');
    
    // Wait for page to load
    await page.waitForSelector('[data-testid="stock-detail-page"]', { timeout: 10000 });
    
    // Check title
    await expect(page.locator('h1')).toContainText('AAPL');
    
    // Check KPI table is visible
    const kpiTable = page.locator('[data-testid="kpi-table"]');
    await expect(kpiTable).toBeVisible();
    
    // Take full page screenshot
    await page.screenshot({ 
      path: '.test-results/screenshots/stock-detail-full.png',
      fullPage: true 
    });
    
    // Take screenshot of KPI table
    await kpiTable.screenshot({ 
      path: '.test-results/screenshots/stock-detail-kpi.png' 
    });
  });

  test('should display price history chart', async ({ page }) => {
    await page.goto('http://localhost:5173/stock/AAPL');
    
    // Wait for chart to render
    await page.waitForSelector('[data-testid="price-chart"]', { timeout: 10000 });
    
    // Check chart is visible
    const priceChart = page.locator('[data-testid="price-chart"]');
    await expect(priceChart).toBeVisible();
    
    // Wait for plotly chart to render
    await page.waitForSelector('.js-plotly-plot', { timeout: 10000 });
    
    // Take screenshot of chart
    await priceChart.screenshot({ 
      path: '.test-results/screenshots/stock-detail-price-chart.png' 
    });
  });

  test('should display PE distribution chart', async ({ page }) => {
    await page.goto('http://localhost:5173/stock/AAPL');
    
    // Wait for chart to render
    await page.waitForSelector('[data-testid="pe-chart"]', { timeout: 10000 });
    
    // Check chart is visible
    const peChart = page.locator('[data-testid="pe-chart"]');
    await expect(peChart).toBeVisible();
    
    // Wait for plotly chart to render
    await page.waitForSelector('.js-plotly-plot', { timeout: 10000 });
    
    // Take screenshot of chart
    await peChart.screenshot({ 
      path: '.test-results/screenshots/stock-detail-pe-chart.png' 
    });
  });

  test('should navigate back and to sector page', async ({ page }) => {
    await page.goto('http://localhost:5173/stock/AAPL');
    
    // Wait for page to load
    await page.waitForSelector('[data-testid="stock-detail-page"]');
    
    // Click sector button if available
    const sectorButton = page.locator('.sector-button');
    if (await sectorButton.isVisible()) {
      await sectorButton.click();
      await page.waitForURL(/\/sector\/.+/);
      await expect(page.locator('[data-testid="sector-dashboard"]')).toBeVisible();
    }
  });
});
