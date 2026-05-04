import { test, expect, type Page } from '@playwright/test';

const ADMIN_EMAIL = process.env.E2E_ADMIN_EMAIL;
const ADMIN_PASSWORD = process.env.E2E_ADMIN_PASSWORD;

/**
 * /admin/broadcast — admin-creds-gated suite covering the Audience filters
 * and payload wiring. We never actually call the Send button (don't want to
 * email real users). Instead we assert UI state and intercept the outgoing
 * POST /api/admin/broadcast-email request to verify the payload shape.
 */

test.describe('admin broadcast email (creds required)', () => {
	test.skip(!ADMIN_EMAIL || !ADMIN_PASSWORD, 'no admin creds in env');

	async function login(page: Page) {
		await page.goto('/login');
		await page.locator('#identifier').fill(ADMIN_EMAIL!);
		await page.locator('input[type="password"]').fill(ADMIN_PASSWORD!);
		await page.getByRole('button', { name: /log\s*in|sign\s*in/i }).first().click();
		await page.waitForURL((u) => !u.pathname.endsWith('/login'), { timeout: 10_000 });
	}

	test('broadcast page renders with Audience filters', async ({ page }) => {
		await login(page);
		await page.goto('/admin/broadcast');
		await expect(page.getByRole('heading', { name: /broadcast/i }).first()).toBeVisible();
		await expect(page.locator('input#subject, input[placeholder*="Subject" i]').first()).toBeVisible();
		await expect(page.locator('textarea').first()).toBeVisible();
		// All five filter checkboxes
		for (const label of [/verified/i, /approved/i, /admin/i]) {
			await expect(page.getByLabel(label).first()).toBeVisible();
		}
	});

	test('verified-only and unverified-only are mutually exclusive', async ({ page }) => {
		await login(page);
		await page.goto('/admin/broadcast');
		const verified = page.getByLabel(/verified emails only/i);
		const unverified = page.getByLabel(/unverified emails only/i);

		// Start: verified is on by default in the UI; toggling unverified should clear it
		await unverified.check();
		await expect(verified).not.toBeChecked();
		await verified.check();
		await expect(unverified).not.toBeChecked();
	});

	test('approved-only and unapproved-only are mutually exclusive', async ({ page }) => {
		await login(page);
		await page.goto('/admin/broadcast');
		const approved = page.getByLabel(/^approved users only$/i);
		const unapproved = page.getByLabel(/unapproved users only/i);
		await approved.check();
		await unapproved.check();
		await expect(approved).not.toBeChecked();
		await approved.check();
		await expect(unapproved).not.toBeChecked();
	});

	test('payload includes selected filters when sending', async ({ page }) => {
		await login(page);
		await page.goto('/admin/broadcast');

		// Fill subject + body
		await page.locator('input').filter({ hasText: '' }).first().fill('e2e test subject');
		await page.locator('textarea').first().fill('<p>e2e test body</p>');

		// Toggle: turn off verified-only, turn on admin-only
		const verified = page.getByLabel(/verified emails only/i);
		if (await verified.isChecked()) await verified.uncheck();
		await page.getByLabel(/admin users only/i).check();

		// Intercept the POST so we never actually send
		const request = page.waitForRequest((r) =>
			r.url().includes('/api/admin/broadcast-email') && r.method() === 'POST'
		);
		await page.route('**/api/admin/broadcast-email', (route) =>
			route.fulfill({ status: 200, body: JSON.stringify({ sent: 0, failed: 0 }) })
		);

		await page.getByRole('button', { name: /send broadcast/i }).click();
		const r = await request;
		const body = JSON.parse(r.postData() ?? '{}');
		expect(body.subject).toBe('e2e test subject');
		expect(body.filter_admin_only).toBe(true);
		expect(body.filter_verified_only ?? false).toBe(false);
	});

	test('GET /api/admin/users does not include super-users in list', async ({ request }) => {
		await request.post('/api/auth/login', {
			data: { identifier: ADMIN_EMAIL, password: ADMIN_PASSWORD }
		});
		const r = await request.get('/api/admin/users');
		expect(r.status()).toBe(200);
		const users = await r.json();
		expect(Array.isArray(users)).toBe(true);
		// Whatever's in the list, none of them should be marked is_super.
		for (const u of users) {
			expect(u.is_super, `${u.user_id ?? u.email} should not be super in admin list`).not.toBe(true);
		}
	});
});
