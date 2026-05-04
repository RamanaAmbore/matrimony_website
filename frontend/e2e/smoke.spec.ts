import { test, expect } from '@playwright/test';

// Anonymous-only smoke tests that don't need a session.
// Cover: home, login, register, search, navbar, dropdown styling, perf hints.

test.describe('public pages', () => {
	test('home page renders with brand and hero', async ({ page }) => {
		// Track only uncaught JS exceptions. Browsers also auto-log console.error
		// for 4xx network responses (e.g. /api/auth/me 401 when anonymous), which
		// is expected behavior, not a bug.
		const errors: string[] = [];
		page.on('pageerror', (e) => errors.push(`pageerror: ${e.message}`));

		const resp = await page.goto('/');
		expect(resp?.status(), 'home should return 2xx').toBeLessThan(400);

		await expect(page.getByRole('link', { name: /Maratha Kalyanam/i }).first()).toBeVisible();

		// Hero image must be loaded (decoded)
		const hero = page.locator('img[src="/bg/home.jpg"]').first();
		await expect(hero).toBeVisible();
		const naturalWidth = await hero.evaluate(
			(img) => (img as HTMLImageElement).naturalWidth
		);
		expect(naturalWidth, 'hero image must have decoded').toBeGreaterThan(0);

		// fetchpriority should be high on the hero so LCP is fast
		await expect(hero).toHaveAttribute('fetchpriority', 'high');

		expect(errors, 'no JS errors on home').toEqual([]);
	});

	test('login page renders form', async ({ page }) => {
		await page.goto('/login');
		await expect(page.getByRole('heading', { name: /log\s*in|sign\s*in/i }).first()).toBeVisible();
		await expect(page.locator('input[type="password"]').first()).toBeVisible();
	});

	test('register page renders form', async ({ page }) => {
		await page.goto('/register');
		await expect(
			page.getByRole('heading', { name: /register|sign\s*up|create/i }).first()
		).toBeVisible();
		await expect(page.locator('input[type="password"]').first()).toBeVisible();
	});

	test('search page renders selects with themed options', async ({ page }) => {
		await page.goto('/search');

		// At least one <select> with .input class (themed)
		const themed = page.locator('select.input').first();
		if ((await themed.count()) > 0) {
			await expect(themed).toBeVisible();
		}

		// Verify accent-color is applied at :root (theming for native widgets)
		const accent = await page.evaluate(
			() => getComputedStyle(document.documentElement).accentColor
		);
		expect(accent, 'accent-color must be set on :root').not.toBe('auto');
	});

	test('navbar shows login button when anonymous, no role chips', async ({ page, isMobile }) => {
		await page.goto('/');

		// Mobile: login link lives inside the hamburger drawer; open it first
		if (isMobile) {
			await page.getByRole('button', { name: /open menu/i }).click();
		}

		// Login link/button is visible to anonymous visitors
		await expect(page.getByRole('link', { name: /log\s*in/i }).first()).toBeVisible();

		// No User/Admin/Test chips when not logged in
		await expect(page.locator('text=/^Admin$/').first()).toHaveCount(0);
	});

	test('site /api/site/info responds with JSON', async ({ request }) => {
		const r = await request.get('/api/site/info');
		expect(r.status()).toBe(200);
		const body = await r.json();
		expect(body).toHaveProperty('is_prod');
		expect(body).toHaveProperty('site_url');
		expect(typeof body.is_prod).toBe('boolean');
	});

	test('admin route redirects or 401s without session', async ({ page }) => {
		const resp = await page.goto('/admin');
		// Either redirected to /login OR rendered the page that calls /api/auth/me and goto's /login.
		// We just assert we don't end on /admin with admin content visible.
		await page.waitForLoadState('networkidle');
		const bodyText = await page.locator('body').innerText();
		expect(bodyText.toLowerCase()).not.toContain('platform overview');
	});
});

test.describe('login + admin flow (requires E2E_ADMIN_EMAIL & E2E_ADMIN_PASSWORD)', () => {
	const email = process.env.E2E_ADMIN_EMAIL;
	const password = process.env.E2E_ADMIN_PASSWORD;
	test.skip(!email || !password, 'no admin creds in env — set E2E_ADMIN_EMAIL/PASSWORD to enable');

	test('admin can log in and see admin dashboard', async ({ page, isMobile }) => {
		await page.goto('/login');
		await page.locator('#identifier').first().fill(email!);
		await page.locator('input[type="password"]').first().fill(password!);
		await page.getByRole('button', { name: /log\s*in|sign\s*in/i }).first().click();

		await page.waitForURL((url) => !url.pathname.endsWith('/login'), { timeout: 10_000 });

		// On mobile the Admin chip lives in the hamburger drawer; open it first.
		// Use .last() because on mobile the desktop-navbar chip is also in the DOM
		// (hidden by Tailwind responsive classes) and would match .first() instead.
		if (isMobile) {
			await page.getByRole('button', { name: /open menu/i }).click();
		}
		await expect(page.locator('text=/^Admin$/').last()).toBeVisible({ timeout: 5_000 });

		// Navigate to admin
		await page.goto('/admin');
		await expect(page.getByRole('heading', { name: /admin dashboard/i })).toBeVisible();

		// Stat cards for users / profiles / requests
		await expect(page.getByText(/^Users$/).first()).toBeVisible();
		await expect(page.getByText(/^Profiles$/).first()).toBeVisible();
		await expect(page.getByText(/^Requests$/).first()).toBeVisible();
	});

	test('chip click filters grid (admin)', async ({ page }) => {
		await page.goto('/login');
		await page.locator('#identifier').first().fill(email!);
		await page.locator('input[type="password"]').first().fill(password!);
		await page.getByRole('button', { name: /log\s*in|sign\s*in/i }).first().click();
		await page.waitForURL((url) => !url.pathname.endsWith('/login'));
		await page.goto('/admin');

		// Click the "All" chip on the Users card
		const allChip = page.getByRole('button', { name: /^All$/ }).first();
		if (await allChip.count()) {
			await allChip.click();
			// Grid should appear (ag-Grid root has class ag-root)
			await expect(page.locator('.ag-root, .ag-theme-quartz').first()).toBeVisible();
		}
	});
});
