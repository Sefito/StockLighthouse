/**
 * E2E test for Sector Dashboard
 */
import { test, expect } from '@playwright/test';

test.describe('Sector Dashboard', () => {
  test('should load and display sector tiles', async ({ page }) => {
    await page.goto('http://localhost:5173/sectors');
    
    // Wait for page to load
    await page.waitForSelector('[data-testid="sector-dashboard"]', { timeout: 10000 });
    
    // Check title
    await expect(page.locator('h1')).toContainText('Sector Dashboard');
    
    // Check heatmap is visible
    const heatmap = page.locator('[data-testid="sector-heatmap"]');
    await expect(heatmap).toBeVisible();
  });

  test('should display dashboard statistics', async ({ page }) => {
    await page.goto('http://localhost:5173/sectors');
    
    // Wait for dashboard to load
    await page.waitForSelector('[data-testid="sector-dashboard"]', { timeout: 10000 });
    
    // Check that stat cards are displayed (MUI Card components in Grid)
    const statCards = page.locator('[data-testid="sector-dashboard"] .MuiCard-root');
    // Should have multiple cards: 3 stats + 1 legend + sector tiles
    await expect(statCards.first()).toBeVisible();
  });

  test('should display sector heatmap with color coding', async ({ page }) => {
    await page.goto('http://localhost:5173/sectors');
    
    // Wait for heatmap to render
    await page.waitForSelector('[data-testid="sector-heatmap"]');
    
    // Check that sector tiles are displayed (using data-testid pattern)
    const sectorTiles = page.locator('[data-testid^="sector-tile-"]');
    await expect(sectorTiles.first()).toBeVisible();
  });

  test('should display legend with P/E ratio colors', async ({ page }) => {
    await page.goto('http://localhost:5173/sectors');
    
    // Wait for dashboard to load
    await page.waitForSelector('[data-testid="sector-dashboard"]');
    
    // Check legend text is visible
    await expect(page.getByText('P/E Ratio Color Legend')).toBeVisible();
  });

  test('should navigate to home when back button clicked', async ({ page }) => {
    await page.goto('http://localhost:5173/sectors');
    
    // Wait for page to load
    await page.waitForSelector('[data-testid="sector-dashboard"]');
    
    // Click back button (MUI Button with Home text)
    await page.getByRole('button', { name: /home/i }).click();
    
    // Should navigate to home
    await page.waitForURL('http://localhost:5173/');
    await expect(page.locator('[data-testid="home-page"]')).toBeVisible();
  });
});
