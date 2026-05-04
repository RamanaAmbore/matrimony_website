import { defineConfig, devices } from '@playwright/test';

const BASE_URL = process.env.E2E_BASE_URL ?? 'https://marathakalyanam.com';

export default defineConfig({
	testDir: './e2e',
	timeout: 30_000,
	expect: { timeout: 10_000 },
	fullyParallel: false,
	retries: 0,
	workers: 1,
	reporter: [['list']],
	use: {
		baseURL: BASE_URL,
		trace: 'retain-on-failure',
		screenshot: 'only-on-failure',
		viewport: { width: 1280, height: 800 }
	},
	projects: [
		{ name: 'chromium-desktop', use: { ...devices['Desktop Chrome'] } },
		// "Pixel 7" uses Chromium under the hood (no WebKit install needed)
		{ name: 'mobile-chrome', use: { ...devices['Pixel 7'] } }
	]
});
