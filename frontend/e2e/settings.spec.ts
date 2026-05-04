import { test, expect, type Page } from '@playwright/test';

const ADMIN_EMAIL = process.env.E2E_ADMIN_EMAIL;
const ADMIN_PASSWORD = process.env.E2E_ADMIN_PASSWORD;

test.describe('admin settings (requires E2E_ADMIN_EMAIL & E2E_ADMIN_PASSWORD)', () => {
	test.skip(!ADMIN_EMAIL || !ADMIN_PASSWORD, 'no admin creds in env');

	async function loginAsAdmin(page: Page) {
		await page.goto('/login');
		await page.locator('#identifier').fill(ADMIN_EMAIL!);
		await page.locator('input[type="password"]').fill(ADMIN_PASSWORD!);
		await page.getByRole('button', { name: /log\s*in|sign\s*in/i }).first().click();
		await page.waitForURL((url) => !url.pathname.endsWith('/login'), { timeout: 10_000 });
	}

	test('settings page loads with current values', async ({ page }) => {
		await loginAsAdmin(page);
		await page.goto('/admin/settings');
		await expect(page.getByRole('heading', { name: /^Settings$/i })).toBeVisible();
		await expect(page.locator('#s-owner_email')).toBeVisible();
		// owner_email field should be pre-populated, not empty
		const ownerEmail = await page.locator('#s-owner_email').inputValue();
		expect(ownerEmail.length, 'owner_email pre-populated from server').toBeGreaterThan(0);
	});

	test('save with current values succeeds (regression: smtp_from "Name <addr>" form)', async ({ page }) => {
		// This is the bug we just fixed — reading existing settings and clicking
		// Save without changes used to fail because smtp_from is in
		// "Display Name <addr@example.com>" RFC form, which a strict regex rejected.
		await loginAsAdmin(page);
		await page.goto('/admin/settings');
		await expect(page.locator('#s-owner_email')).toBeVisible();

		// Start listening for the success toast before clicking
		const savePromise = page.waitForResponse(
			(r) => r.url().includes('/api/admin/settings') && r.request().method() === 'PUT'
		);
		await page.getByRole('button', { name: /save/i }).first().click();
		const resp = await savePromise;
		expect(resp.status(), 'PUT /admin/settings should accept current values').toBe(200);
	});

	test('invalid owner_email is rejected with inline error', async ({ page }) => {
		await loginAsAdmin(page);
		await page.goto('/admin/settings');
		const input = page.locator('#s-owner_email');
		await input.waitFor();
		const original = await input.inputValue();

		await input.fill('not-an-email');
		await input.blur(); // triggers validateAll on the field
		await expect(page.locator('text=/Enter a valid email/i').first()).toBeVisible();

		// restore so the test isn't destructive
		await input.fill(original);
	});

	test('valid display-name form "Name <addr>" is accepted', async ({ page }) => {
		await loginAsAdmin(page);
		await page.goto('/admin/settings');
		const smtpFrom = page.locator('#s-smtp_from');
		await smtpFrom.waitFor();
		const original = await smtpFrom.inputValue();

		// Ensure the display-name format passes validation (no inline error appears)
		await smtpFrom.fill('Maratha Kalyanam <admin.marathakalyanam@gmail.com>');
		await smtpFrom.blur();
		// No vermilion-class error message should appear for this field
		const errorAfterField = page.locator('#s-smtp_from + p.text-vermilion');
		await expect(errorAfterField).toHaveCount(0);

		// restore
		await smtpFrom.fill(original);
	});

	test('toggling is_prod updates navbar Test chip without reload', async ({ page }) => {
		await loginAsAdmin(page);
		await page.goto('/admin/settings');

		// Find the is_prod checkbox and capture its initial state
		const isProdCheckbox = page.locator('#s-is_prod');
		await isProdCheckbox.waitFor();
		const initiallyChecked = await isProdCheckbox.isChecked();

		// Flip is_prod and save
		if (initiallyChecked) {
			await isProdCheckbox.uncheck();
		} else {
			await isProdCheckbox.check();
		}
		const savePromise = page.waitForResponse(
			(r) => r.url().includes('/api/admin/settings') && r.request().method() === 'PUT'
		);
		await page.getByRole('button', { name: /save/i }).first().click();
		await savePromise;

		// After save, when is_prod is FALSE the "Test" chip is visible.
		// invalidateAll() should refresh layout; give it a beat.
		await page.waitForTimeout(500);
		const expectTestChipVisible = initiallyChecked; // we just flipped, so opposite of initial
		const testChip = page.locator('text=/^Test$/').last();
		if (expectTestChipVisible) {
			await expect(testChip).toBeVisible({ timeout: 5_000 });
		} else {
			await expect(testChip).toHaveCount(0);
		}

		// Flip back to original state to keep prod stable
		if (initiallyChecked) {
			await isProdCheckbox.check();
		} else {
			await isProdCheckbox.uncheck();
		}
		const restorePromise = page.waitForResponse(
			(r) => r.url().includes('/api/admin/settings') && r.request().method() === 'PUT'
		);
		await page.getByRole('button', { name: /save/i }).first().click();
		await restorePromise;
	});
});
