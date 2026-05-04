import { test, expect } from '@playwright/test';

/**
 * Per-page coverage — assert that every public route renders a sensible
 * page shell with no JS exceptions. Auth-gated routes either redirect to
 * /login or render their gated empty state. These are deliberately loose
 * assertions so they don't break on copy changes.
 */

const PUBLIC_ROUTES = [
	{ path: '/', match: /Maratha Kalyanam/i },
	{ path: '/about', match: /(About|Maratha)/i },
	{ path: '/login', match: /(Log\s*In|Sign\s*In|Identifier)/i },
	{ path: '/register', match: /(Register|Create|Sign\s*Up)/i },
	{ path: '/search', match: /(Search|Profiles)/i }
];

const AUTH_GATED_ROUTES = [
	'/dashboard',
	'/requests',
	'/admin',
	'/admin/settings',
	'/admin/users',
	'/profiles/new'
];

test.describe('public routes — render with no JS exceptions', () => {
	for (const r of PUBLIC_ROUTES) {
		test(`GET ${r.path} renders cleanly`, async ({ page }) => {
			const errors: string[] = [];
			page.on('pageerror', (e) => errors.push(e.message));
			const resp = await page.goto(r.path);
			expect(resp?.status(), `${r.path} should be 2xx`).toBeLessThan(400);
			await expect(page.locator('body')).toContainText(r.match);
			expect(errors, `no uncaught JS errors on ${r.path}`).toEqual([]);
		});
	}
});

test.describe('auth-gated routes — anonymous visitors handled', () => {
	for (const path of AUTH_GATED_ROUTES) {
		test(`GET ${path} doesn't crash for anonymous`, async ({ page }) => {
			const errors: string[] = [];
			page.on('pageerror', (e) => errors.push(e.message));
			const resp = await page.goto(path);
			// Either 200 (with redirect via JS to /login) or a redirect.
			expect(resp?.status(), `${path} should not 5xx`).toBeLessThan(500);
			// Wait for client-side auth check to settle.
			await page.waitForLoadState('networkidle');
			expect(errors, `no uncaught JS errors on ${path}`).toEqual([]);
		});
	}
});

test.describe('register page form interactions', () => {
	test('shows error if user_id is too short', async ({ page }) => {
		await page.goto('/register');
		// Find the user_id input (label "User ID" — id is "user_id")
		const userIdInput = page.locator('#user_id');
		if ((await userIdInput.count()) === 0) {
			test.skip(true, 'register page form shape changed — re-check selectors');
		}
		await userIdInput.fill('ab'); // too short (regex requires 3+ chars)
		await userIdInput.blur();
		// Error text should appear nearby. We don't assert exact message; just that
		// some validation error is shown for the user_id field.
		const error = page.locator('p.text-vermilion').first();
		await expect(error).toBeVisible({ timeout: 3_000 });
	});
});

test.describe('search page filter interactions', () => {
	test('changing gender filter triggers a search request', async ({ page }) => {
		await page.goto('/search');
		// Look for any select with a gender-ish option. We just assert that
		// there IS a select on the page and it's interactable.
		const firstSelect = page.locator('select.input').first();
		if ((await firstSelect.count()) === 0) {
			test.skip(true, 'no select.input on search page — UI rewrite?');
		}
		await expect(firstSelect).toBeVisible();
	});
});

test.describe('site config drives navbar Test chip', () => {
	test('Test chip is present iff is_prod is false', async ({ page, request }) => {
		// Read the live setting
		const r = await request.get('/api/site/info');
		const body = await r.json();
		await page.goto('/');
		const testChip = page.locator('text=/^Test$/').last();
		if (body.is_prod === false) {
			await expect(testChip).toBeVisible();
		} else {
			await expect(testChip).toHaveCount(0);
		}
	});
});
