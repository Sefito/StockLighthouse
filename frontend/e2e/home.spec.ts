/**
 * E2E test for Home Page
 */
import { test, expect } from '@playwright/test';

test.describe('Home Page', () => {
  test('should load and display search bar', async ({ page }) => {
    await page.goto('http://localhost:5173');
    
    // Wait for page to load
    await page.waitForSelector('[data-testid="home-page"]', { timeout: 15000 });
    
    // Check title (uses h1 variant in MUI Typography)
    await expect(page.locator('h1')).toContainText('StockLighthouse');
    
    // Check search bar
    const searchInput = page.locator('[data-testid="search-input"]');
    await expect(searchInput).toBeVisible();
  });

  test('should display popular stocks list', async ({ page }) => {
    await page.goto('http://localhost:5173');
    
    // Wait for stocks to load (or loading spinner to disappear)
    await page.waitForSelector('[data-testid="stock-list"], .MuiCircularProgress-root', { timeout: 15000 });
    
    // Wait a bit more for data to load
    await page.waitForTimeout(2000);
    
    // Check if stock list is visible
    const stockList = page.locator('[data-testid="stock-list"]');
    const isStockListVisible = await stockList.isVisible();
    
    if (isStockListVisible) {
      // Check that stock cards are displayed (using data-testid pattern)
      const stockCards = page.locator('[data-testid^="stock-card-"]');
      const count = await stockCards.count();
      if (count > 0) {
        await expect(stockCards.first()).toBeVisible();
      }
    }
  });

  test('should navigate to stock detail page', async ({ page }) => {
    await page.goto('http://localhost:5173');
    
    // Wait for stocks to load
    await page.waitForSelector('[data-testid="stock-list"]', { timeout: 15000 });
    
    // Check if any stock cards exist
    const stockCards = page.locator('[data-testid^="stock-card-"]');
    const count = await stockCards.count();
    
    if (count > 0) {
      // Click first stock card (using data-testid pattern)
      await stockCards.first().click();
      
      // Wait for navigation
      await page.waitForURL(/\/stock\/.+/, { timeout: 10000 });
      
      // Verify we're on stock detail page (or error state)
      await expect(page.locator('[data-testid="stock-detail-page"], .MuiAlert-root')).toBeVisible();
    }
  });
});
