/**
 * E2E test for Home Page
 */
import { test, expect } from '@playwright/test';

test.describe('Home Page', () => {
  test('should load and display search bar', async ({ page }) => {
    await page.goto('http://localhost:5173');
    
    // Wait for page to load
    await page.waitForSelector('[data-testid="home-page"]');
    
    // Check title
    await expect(page.locator('h1')).toContainText('StockLighthouse');
    
    // Check search bar
    const searchInput = page.locator('[data-testid="search-input"]');
    await expect(searchInput).toBeVisible();
  });

  test('should display popular stocks list', async ({ page }) => {
    await page.goto('http://localhost:5173');
    
    // Wait for stocks to load
    await page.waitForSelector('[data-testid="stock-list"]', { timeout: 10000 });
    
    // Check that stock cards are displayed
    const stockCards = page.locator('.stock-card');
    await expect(stockCards.first()).toBeVisible();
  });

  test('should navigate to stock detail page', async ({ page }) => {
    await page.goto('http://localhost:5173');
    
    // Wait for stocks to load
    await page.waitForSelector('[data-testid="stock-list"]');
    
    // Click first stock card
    await page.locator('.stock-card').first().click();
    
    // Wait for navigation
    await page.waitForURL(/\/stock\/.+/);
    
    // Verify we're on stock detail page
    await expect(page.locator('[data-testid="stock-detail-page"]')).toBeVisible();
  });
});
