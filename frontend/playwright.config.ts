import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: 'frontend/e2e',
  outputDir: '.test-results/screenshots',
  timeout: 30 * 1000,
  retries: 0,
  use: {
    headless: true,
    viewport: { width: 1280, height: 720 },
    actionTimeout: 10 * 1000,
  },
  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
  ],
});