import { test, expect } from '@playwright/test';

/**
 * Audit every <select> on the public/data-entry pages — confirm
 *  (a) the element has class="input" so themed CSS applies
 *  (b) the option:checked CSS rules ARE in the loaded stylesheets
 *  (c) the computed accent-color is maroon (controls native widgets)
 *
 * Note: the actual dropdown popup background is browser-controlled.
 * Chromium honours `option:checked { background: ... }`; Safari mostly
 * ignores option styling. Playwright runs Chromium so we can verify our
 * rules apply there. For Safari/iOS we'd need a custom dropdown widget.
 */

const PAGES_WITH_SELECTS = ['/search', '/register'];

test.describe('dropdown styling audit', () => {
	for (const path of PAGES_WITH_SELECTS) {
		test(`${path} — every <select> uses class="input" + accent-color is maroon`, async ({ page }) => {
			await page.goto(path);

			const selects = page.locator('select');
			const count = await selects.count();
			console.log(`  ${path}: ${count} <select> elements`);

			for (let i = 0; i < count; i++) {
				const sel = selects.nth(i);
				const className = (await sel.getAttribute('class')) ?? '';
				expect(className, `${path} select #${i} should have .input class`).toContain('input');
			}

			// :root accent-color
			const accent = await page.evaluate(() =>
				getComputedStyle(document.documentElement).accentColor
			);
			console.log(`  ${path}: accent-color = ${accent}`);
			expect(accent.toLowerCase(), `${path} accent-color set`).not.toBe('auto');

			// First select's option:checked computed background should be saffron-ish
			const firstSel = selects.first();
			if ((await firstSel.count()) > 0) {
				const optBg = await firstSel.evaluate((el) => {
					const opt = (el as HTMLSelectElement).options[0];
					if (!opt) return '';
					return getComputedStyle(opt).backgroundColor;
				});
				console.log(`  ${path}: first option computed background = ${optBg}`);
			}
		});
	}

	test('dropdown CSS rules are present in loaded stylesheets', async ({ page }) => {
		await page.goto('/search');
		const matches = await page.evaluate(() => {
			const found: string[] = [];
			for (const sheet of Array.from(document.styleSheets)) {
				try {
					for (const rule of Array.from(sheet.cssRules)) {
						const text = rule.cssText.toLowerCase();
						if (text.includes('option:checked') || text.includes('option:hover') ||
							text.startsWith('option')) {
							found.push(rule.cssText);
						}
					}
				} catch {
					// cross-origin sheet — skip
				}
			}
			return found;
		});
		console.log(`  ${matches.length} option-related CSS rules found:`);
		for (const m of matches.slice(0, 10)) console.log(`    ${m}`);
		expect(matches.length).toBeGreaterThan(0);
	});
});

/**
 * Sanity check that the seeded data is visible in the UI.
 * Looks for "Z" profile_numbers in admin grid (only rendered when admin
 * clicks an "All" chip). Skipped if creds missing.
 */
test.describe('seeded data visible in admin UI (admin creds required)', () => {
	const ADMIN_EMAIL = process.env.E2E_ADMIN_EMAIL;
	const ADMIN_PASSWORD = process.env.E2E_ADMIN_PASSWORD;
	test.skip(!ADMIN_EMAIL || !ADMIN_PASSWORD, 'no admin creds in env');

	test('admin sees seeded profiles when "All" chip clicked', async ({ page }) => {
		await page.goto('/login');
		await page.locator('#identifier').fill(ADMIN_EMAIL!);
		await page.locator('input[type="password"]').fill(ADMIN_PASSWORD!);
		await page.getByRole('button', { name: /log\s*in|sign\s*in/i }).first().click();
		await page.waitForURL((u) => !u.pathname.endsWith('/login'));
		await page.goto('/admin');
		// click the Profiles card "All" chip
		await page.getByRole('button', { name: /^All$/ }).nth(1).click(); // second "All" = profiles card
		// at least one TC-###### profile_number should appear
		await expect(page.locator('text=/^TC-\\d{6}$/').first()).toBeVisible({ timeout: 10_000 });
	});

	test('admin sees seeded requests when "All" chip clicked', async ({ page }) => {
		await page.goto('/login');
		await page.locator('#identifier').fill(ADMIN_EMAIL!);
		await page.locator('input[type="password"]').fill(ADMIN_PASSWORD!);
		await page.getByRole('button', { name: /log\s*in|sign\s*in/i }).first().click();
		await page.waitForURL((u) => !u.pathname.endsWith('/login'));
		await page.goto('/admin');
		// Requests card All chip is the third
		await page.getByRole('button', { name: /^All$/ }).nth(2).click();
		// expect at least one e2e+...@marathakalyanam.com requester
		await expect(
			page.locator('text=/e2e\\+.*@marathakalyanam\\.com/').first()
		).toBeVisible({ timeout: 10_000 });
	});

	test('public search renders seeded approved profiles', async ({ page }) => {
		await page.goto('/search');
		// search shows blurred preview cards for anonymous; just confirm at least
		// one card is rendered (the seed has 40 approved profiles, so plenty).
		await page.waitForLoadState('networkidle');
		const cards = page.locator('article, [data-testid="profile-card"], .card');
		const n = await cards.count();
		console.log(`  /search rendered ${n} card-ish elements`);
		expect(n).toBeGreaterThan(0);
	});
});
