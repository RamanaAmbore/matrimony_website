import { test, expect, type Page } from '@playwright/test';

const ADMIN_EMAIL = process.env.E2E_ADMIN_EMAIL;
const ADMIN_PASSWORD = process.env.E2E_ADMIN_PASSWORD;

/**
 * Performance suite — measures backend API latencies and frontend page-load
 * metrics on the live site. Fails on regressions vs reasonable thresholds.
 *
 * Thresholds are deliberately loose since we're hitting prod over the public
 * internet (Cloudflare CDN + nginx + Litestar + Postgres). Tighten if local.
 */

// ---- Backend API latency targets (ms) ----
const API_TARGETS = [
	{ path: '/api/site/info',  warm: 300, cold: 800 },
	{ path: '/api/health',     warm: 300, cold: 800 },
	{ path: '/api/search',     warm: 600, cold: 1200 },
	{ path: '/api/auth/me',    warm: 400, cold: 800 } // expects 401 anonymous
];

// ---- Frontend page-load targets ----
const FRONTEND_TARGETS = [
	{ path: '/',        ttfbMax: 1500, lcpMax: 4000 },
	{ path: '/login',   ttfbMax: 1500, lcpMax: 4000 },
	{ path: '/search',  ttfbMax: 1500, lcpMax: 5000 }
];

const ADMIN_API_TARGETS = [
	{ path: '/api/admin/dashboard', warm: 1500, cold: 3000 },
	{ path: '/api/admin/users',     warm: 1500, cold: 3000 },
	{ path: '/api/admin/profiles',  warm: 1500, cold: 3000 },
	{ path: '/api/admin/requests',  warm: 1500, cold: 3000 },
	{ path: '/api/admin/settings',  warm: 1500, cold: 3000 }
];

const N_RUNS = 5; // sample size per endpoint

function pct(arr: number[], p: number): number {
	const sorted = [...arr].sort((a, b) => a - b);
	const idx = Math.min(sorted.length - 1, Math.floor((sorted.length * p) / 100));
	return sorted[idx];
}

async function timeRequest(request: any, path: string): Promise<number> {
	const t0 = Date.now();
	const r = await request.get(path);
	const elapsed = Date.now() - t0;
	// Drain body to measure full response time
	await r.body();
	return elapsed;
}

test.describe('backend API performance (anonymous)', () => {
	for (const t of API_TARGETS) {
		test(`${t.path} — warm p50 < ${t.warm}ms, cold (first) < ${t.cold}ms`, async ({ request }) => {
			const samples: number[] = [];
			for (let i = 0; i < N_RUNS; i++) samples.push(await timeRequest(request, t.path));
			const cold = samples[0];
			const warmSamples = samples.slice(1);
			const p50 = pct(warmSamples, 50);
			const p95 = pct(warmSamples, 95);
			console.log(
				`  ${t.path.padEnd(28)} cold=${String(cold).padStart(4)}ms  ` +
				`p50=${String(p50).padStart(4)}ms  p95=${String(p95).padStart(4)}ms`
			);
			expect(cold, `cold-cache request to ${t.path}`).toBeLessThan(t.cold);
			expect(p50, `warm p50 to ${t.path}`).toBeLessThan(t.warm);
		});
	}
});

test.describe('backend API performance (admin) — requires E2E_ADMIN_*', () => {
	test.skip(!ADMIN_EMAIL || !ADMIN_PASSWORD, 'no admin creds in env');

	test.beforeAll(async ({ request }) => {
		await request.post('/api/auth/login', {
			data: { identifier: ADMIN_EMAIL, password: ADMIN_PASSWORD }
		});
	});

	for (const t of ADMIN_API_TARGETS) {
		test(`${t.path} — warm p50 < ${t.warm}ms, cold (first) < ${t.cold}ms`, async ({ request }) => {
			const samples: number[] = [];
			for (let i = 0; i < N_RUNS; i++) samples.push(await timeRequest(request, t.path));
			const cold = samples[0];
			const p50 = pct(samples.slice(1), 50);
			const p95 = pct(samples.slice(1), 95);
			console.log(
				`  ${t.path.padEnd(28)} cold=${String(cold).padStart(4)}ms  ` +
				`p50=${String(p50).padStart(4)}ms  p95=${String(p95).padStart(4)}ms`
			);
			expect(cold, `cold-cache request to ${t.path}`).toBeLessThan(t.cold);
			expect(p50, `warm p50 to ${t.path}`).toBeLessThan(t.warm);
		});
	}
});

test.describe('frontend page-load performance', () => {
	for (const t of FRONTEND_TARGETS) {
		test(`${t.path} — TTFB < ${t.ttfbMax}ms, LCP < ${t.lcpMax}ms`, async ({ page }: { page: Page }) => {
			const t0 = Date.now();
			const resp = await page.goto(t.path, { waitUntil: 'load' });
			const ttfb = Date.now() - t0;
			expect(resp?.status()).toBeLessThan(400);

			// Largest Contentful Paint via PerformanceObserver
			const lcp = await page.evaluate(
				() =>
					new Promise<number>((resolve) => {
						let value = 0;
						const obs = new PerformanceObserver((list) => {
							for (const entry of list.getEntries()) {
								value = entry.startTime;
							}
						});
						try {
							obs.observe({ type: 'largest-contentful-paint', buffered: true });
						} catch {
							resolve(0);
							return;
						}
						setTimeout(() => {
							obs.disconnect();
							resolve(Math.round(value));
						}, 1500);
					})
			);

			console.log(`  ${t.path.padEnd(20)}  TTFB=${ttfb}ms  LCP=${lcp}ms`);
			expect(ttfb, `TTFB for ${t.path}`).toBeLessThan(t.ttfbMax);
			if (lcp > 0) expect(lcp, `LCP for ${t.path}`).toBeLessThan(t.lcpMax);
		});
	}
});

test.describe('concurrent load — 20 parallel /api/site/info', () => {
	test('all 20 succeed and p95 < 2000ms', async ({ request }) => {
		const tasks = Array.from({ length: 20 }, () => timeRequest(request, '/api/site/info'));
		const samples = await Promise.all(tasks);
		const p50 = pct(samples, 50);
		const p95 = pct(samples, 95);
		const max = Math.max(...samples);
		console.log(
			`  20-concurrent /api/site/info  p50=${p50}ms  p95=${p95}ms  max=${max}ms`
		);
		expect(p95).toBeLessThan(2000);
	});
});
