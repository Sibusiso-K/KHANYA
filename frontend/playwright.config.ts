import {defineConfig} from '@playwright/test';

export default defineConfig({
  testDir: './e2e',
  reporter: 'list',
  use: {baseURL: 'http://127.0.0.1:4175', viewport: {width: 375, height: 812}, browserName: 'chromium'},
  webServer: {command: 'npm run dev -- --port 4175', url: 'http://127.0.0.1:4175', reuseExistingServer: !process.env.CI, timeout: 30_000},
});
