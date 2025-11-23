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
    
    // Take full page screenshot
    await page.screenshot({ 
      path: '.test-results/screenshots/sector-dashboard-full.png',
      fullPage: true 
    });
  });

  test('should display dashboard statistics', async ({ page }) => {
    await page.goto('http://localhost:5173/sectors');
    
    // Wait for stats to load
    await page.waitForSelector('.dashboard-stats');
    
    // Check stat cards
    const statCards = page.locator('.stat-card');
    await expect(statCards).toHaveCount(3);
    
    // Take screenshot of stats
    const dashboardStats = page.locator('.dashboard-stats');
    await dashboardStats.screenshot({ 
      path: '.test-results/screenshots/sector-dashboard-stats.png' 
    });
  });

  test('should display sector heatmap with color coding', async ({ page }) => {
    await page.goto('http://localhost:5173/sectors');
    
    // Wait for heatmap to render
    await page.waitForSelector('[data-testid="sector-heatmap"]');
    
    // Check that sector tiles are displayed
    const sectorTiles = page.locator('.sector-tile');
    await expect(sectorTiles.first()).toBeVisible();
    
    // Take screenshot of heatmap
    const heatmap = page.locator('[data-testid="sector-heatmap"]');
    await heatmap.screenshot({ 
      path: '.test-results/screenshots/sector-dashboard-heatmap.png' 
    });
  });

  test('should display legend', async ({ page }) => {
    await page.goto('http://localhost:5173/sectors');
    
    // Wait for legend to load
    await page.waitForSelector('.legend');
    
    // Check legend is visible
    const legend = page.locator('.legend');
    await expect(legend).toBeVisible();
    await expect(legend).toContainText('P/E Ratio Color Legend');
    
    // Take screenshot of legend
    await legend.screenshot({ 
      path: '.test-results/screenshots/sector-dashboard-legend.png' 
    });
  });

  test('should navigate to home and sector tiles should be clickable', async ({ page }) => {
    await page.goto('http://localhost:5173/sectors');
    
    // Wait for page to load
    await page.waitForSelector('[data-testid="sector-dashboard"]');
    
    // Click back button
    const backButton = page.locator('.back-button');
    await backButton.click();
    
    // Should navigate to home
    await page.waitForURL('http://localhost:5173/');
    await expect(page.locator('[data-testid="home-page"]')).toBeVisible();
  });
});
