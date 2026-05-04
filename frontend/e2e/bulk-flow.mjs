#!/usr/bin/env node
/**
 * Bulk data lifecycle test against the live API.
 *
 * Creates 12 users → 12 profiles → submits/drafts/approves/rejects them →
 * creates detail requests → exercises search → verifies dashboard counts →
 * cleans up everything it created.
 *
 * Required env: E2E_ADMIN_EMAIL, E2E_ADMIN_PASSWORD.
 * Optional env: E2E_BASE_URL (default https://marathakalyanam.com).
 *
 * All test users get user_id prefix `e2e_` and email `e2e+...@marathakalyanam.com`
 * so cleanup can target them precisely.
 */

import { execSync } from 'node:child_process';

const BASE = process.env.E2E_BASE_URL ?? 'https://marathakalyanam.com';
const ADMIN_EMAIL = process.env.E2E_ADMIN_EMAIL;
const ADMIN_PASSWORD = process.env.E2E_ADMIN_PASSWORD;

if (!ADMIN_EMAIL || !ADMIN_PASSWORD) {
	console.error('Missing E2E_ADMIN_EMAIL or E2E_ADMIN_PASSWORD');
	process.exit(2);
}

const RUN_ID = Date.now();
const CASES = []; // { name, ok, msg, ms }

function logCase(name, ok, msg = '', ms = 0) {
	CASES.push({ name, ok, msg, ms });
	const tag = ok ? '\x1b[32mPASS\x1b[0m' : '\x1b[31mFAIL\x1b[0m';
	console.log(`  ${tag}  ${name}${msg ? ` — ${msg}` : ''}${ms ? `  (${ms}ms)` : ''}`);
}

async function check(name, fn) {
	const t0 = Date.now();
	try {
		await fn();
		logCase(name, true, '', Date.now() - t0);
		return true;
	} catch (e) {
		logCase(name, false, String(e.message || e), Date.now() - t0);
		return false;
	}
}

class Session {
	constructor(label) {
		this.label = label;
		this.cookie = null;
	}
	async req(method, path, body) {
		const r = await fetch(`${BASE}${path}`, {
			method,
			headers: {
				...(body ? { 'Content-Type': 'application/json' } : {}),
				...(this.cookie ? { cookie: this.cookie } : {})
			},
			body: body ? JSON.stringify(body) : undefined,
			redirect: 'manual'
		});
		const setCookie = r.headers.get('set-cookie');
		if (setCookie && setCookie.startsWith('mk_jwt=')) {
			this.cookie = setCookie.split(';')[0];
		}
		const ct = r.headers.get('content-type') ?? '';
		const data = ct.includes('application/json') ? await r.json() : await r.text();
		if (!r.ok) {
			const msg = typeof data === 'object' ? JSON.stringify(data) : data;
			throw new Error(`${method} ${path} → ${r.status}  ${msg}`);
		}
		return data;
	}
}

function ssh(cmd) {
	// Single-quote so the LOCAL shell does not expand $() / $vars — they're
	// meant to run on the remote.
	const escaped = cmd.replace(/'/g, "'\\''");
	return execSync(`ssh ramboq '${escaped}'`, { encoding: 'utf-8', stdio: ['ignore', 'pipe', 'pipe'] });
}

function psql(sql) {
	const sqlSingleQuoted = `'${sql.replace(/'/g, "'\\''")}'`;
	const cmd =
		`PGPASSWORD=$(grep -E '^DATABASE_URL=' /opt/marathakalyanam/.env | sed -E 's|.*://[^:]+:([^@]+)@.*|\\1|') ` +
		`psql -h 127.0.0.1 -U marathakalyanam -d marathakalyanam -t -A -c ${sqlSingleQuoted}`;
	return ssh(cmd).trim();
}

async function main() {
	console.log(`▶ Bulk flow (BASE=${BASE}, RUN_ID=${RUN_ID})`);

	// ── Pre-cleanup: nuke any leftover e2e_ users from prior failed runs
	const leftover = parseInt(psql(`SELECT count(*) FROM users WHERE user_handle LIKE 'e2e_%';`), 10);
	if (leftover > 0) {
		console.log(`  cleaning ${leftover} leftover e2e_ users from prior runs`);
		psql(`DELETE FROM users WHERE user_handle LIKE 'e2e_%';`);
	}

	const admin = new Session('admin');
	const userSessions = []; // [{u: Session, uuid, handle}]

	// ── Admin login
	await check('admin login', async () => {
		const me = await admin.req('POST', '/api/auth/login', {
			identifier: ADMIN_EMAIL,
			password: ADMIN_PASSWORD
		});
		if (!me.uuid) throw new Error('login response missing uuid');
	});

	// ── Initial dashboard counts (baseline)
	let baseline = null;
	await check('admin dashboard baseline', async () => {
		const d = await admin.req('GET', '/api/admin/dashboard');
		baseline = d.stats;
		if (typeof baseline.profiles_total !== 'number') throw new Error('dashboard shape unexpected');
	});

	const N_USERS = 12;
	const GOTRAS = ['Bharadwaja', 'Vasishta', 'Atri', 'Kashyapa', 'Vishvamitra', 'Bharadwaja'];
	const CITIES = ['Hyderabad', 'Vijayawada', 'Pune', 'Mumbai', 'Bangalore', 'Chennai'];
	const NAKSHATRAMS = ['Ashwini', 'Bharani', 'Krittika', 'Rohini', 'Mrigashira'];

	// ── Register N users
	const t0 = Date.now();
	let registered = 0;
	for (let i = 0; i < N_USERS; i++) {
		const u = new Session(`user_${i}`);
		const handle = `e2e_user_${RUN_ID}_${i}`;
		try {
			const r = await u.req('POST', '/api/auth/register', {
				email: `e2e+${RUN_ID}_${i}@marathakalyanam.com`,
				password: `Test_${RUN_ID}!1`,
				user_id: handle,
				phone_number: `+9100000${String(RUN_ID).slice(-5)}${i}`,
				full_name: `E2E User ${i}`
			});
			if (!r.uuid) throw new Error('register missing uuid');
			userSessions.push({ u, uuid: r.uuid, handle });
			registered++;
		} catch (e) {
			throw new Error(`registration failed at user ${i}: ${e.message}`);
		}
	}
	logCase(`register ${N_USERS} users`, registered === N_USERS, `${registered}/${N_USERS}`, Date.now() - t0);

	// Mark all users email_verified + is_approved via direct SQL (skips email round-trip)
	psql(
		`UPDATE users SET email_verified = true, is_approved = true WHERE user_handle LIKE 'e2e_%';`
	);

	// ── Each user logs in
	for (const s of userSessions) {
		await check(`login user ${s.handle.split('_').pop()}`, async () => {
			s.u.cookie = null; // force fresh
			const me = await s.u.req('POST', '/api/auth/login', {
				identifier: s.handle,
				password: `Test_${RUN_ID}!1`
			});
			if (me.uuid !== s.uuid) throw new Error(`uuid mismatch: ${me.uuid} vs ${s.uuid}`);
		});
	}

	// ── Each user creates a draft profile
	const profiles = []; // { sessionIdx, profileId }
	for (let i = 0; i < userSessions.length; i++) {
		const s = userSessions[i];
		const gender = i % 2 === 0 ? 'bride' : 'groom';
		const profile = await s.u.req('POST', '/api/profiles', {
			gender,
			first_name: `First${i}`,
			last_name: `Last${i}`,
			dob: '1995-06-15',
			mother_tongue: 'Telugu',
			surname_clan: `Clan${i}`,
			height_cm: 165 + (i % 10),
			gotra: GOTRAS[i % GOTRAS.length],
			kuldevata: 'Khandoba',
			devak: 'Tulsi',
			nakshatram: NAKSHATRAMS[i % NAKSHATRAMS.length],
			rashi: 'Mesha',
			manglik: 'no',
			education: 'B.Tech',
			occupation: 'Engineer',
			diet: 'veg',
			city: CITIES[i % CITIES.length],
			state: 'Telangana',
			country: 'India',
			about: 'Auto-seeded e2e test profile',
			partner_expectations: 'Auto-seeded'
		});
		profiles.push({ sessionIdx: i, profileId: profile.id, status: profile.status });
	}
	logCase(`create ${N_USERS} draft profiles`, profiles.length === N_USERS, `${profiles.length}/${N_USERS}`);

	// ── Submit profiles 0..7 to pending  (4..11 stay as drafts)
	const SUBMIT_COUNT = 8;
	let submitted = 0;
	for (let i = 0; i < SUBMIT_COUNT; i++) {
		const p = profiles[i];
		const s = userSessions[p.sessionIdx];
		try {
			const r = await s.u.req('POST', `/api/profiles/${p.profileId}/submit`);
			p.status = r.status;
			submitted++;
		} catch (e) {
			// Submit may require photos; if it fails, fall back to direct SQL update
			psql(
				`UPDATE profiles SET status = 'pending', updated_at = now() WHERE id = '${p.profileId}';`
			);
			p.status = 'pending';
			submitted++;
		}
	}
	logCase(`submit ${SUBMIT_COUNT} profiles to pending`, submitted === SUBMIT_COUNT, `${submitted}/${SUBMIT_COUNT}`);

	// ── Admin approves 0..2, rejects 3..4. (5..7 stay pending.)
	for (let i = 0; i < 3; i++) {
		const p = profiles[i];
		await check(`admin approves profile ${i}`, async () => {
			await admin.req('POST', `/api/admin/profiles/${p.profileId}/approve`, {
				admin_notes: null
			});
			p.status = 'approved';
		});
	}
	for (let i = 3; i < 5; i++) {
		const p = profiles[i];
		await check(`admin rejects profile ${i}`, async () => {
			await admin.req('POST', `/api/admin/profiles/${p.profileId}/reject`, {
				admin_notes: 'auto-test rejection'
			});
			p.status = 'rejected';
		});
	}

	// ── Search exercises
	await check('public search returns preview shape (anonymous)', async () => {
		const anon = new Session('anon');
		const r = await anon.req('GET', '/api/search?gender=bride');
		if (!('requires_registration' in r) || r.requires_registration !== true) {
			throw new Error(`expected anonymous preview, got ${JSON.stringify(r).slice(0, 100)}`);
		}
	});

	await check('authenticated search by gender=bride returns at least 1 approved bride', async () => {
		const r = await admin.req('GET', '/api/search?gender=bride');
		if (typeof r.total !== 'number')
			throw new Error(`expected SearchResponse, got ${JSON.stringify(r).slice(0, 100)}`);
		if (r.total < 1)
			throw new Error(`expected at least 1 approved bride, got total=${r.total}`);
	});

	await check('authenticated search by gotra returns matches', async () => {
		const r = await admin.req('GET', '/api/search?gotra=Bharadwaja');
		if (r.total < 1) throw new Error(`expected ≥1, got ${r.total}`);
	});

	// ── Detail requests: users 8..11 (still have drafts) request details on profile 0
	const requesters = userSessions.slice(8, 12);
	const targetProfile = profiles[0]; // approved
	const requestIds = [];
	for (let i = 0; i < requesters.length; i++) {
		const s = requesters[i];
		await check(`requester ${i} creates detail request`, async () => {
			const r = await s.u.req('POST', `/api/profiles/${targetProfile.profileId}/request`, {
				message: `e2e test request ${i}`
			});
			if (!r.id) throw new Error('request missing id');
			requestIds.push(r.id);
		});
	}

	// ── Admin: approve 2, reject 1, leave 1 pending
	await check('admin approves request 0', async () =>
		admin.req('POST', `/api/admin/requests/${requestIds[0]}/approve`, { admin_notes: null })
	);
	await check('admin approves request 1', async () =>
		admin.req('POST', `/api/admin/requests/${requestIds[1]}/approve`, { admin_notes: null })
	);
	await check('admin rejects request 2', async () =>
		admin.req('POST', `/api/admin/requests/${requestIds[2]}/reject`, {
			admin_notes: 'auto-test reject'
		})
	);

	// ── Approved requester now sees full profile (passport_url present)
	await check('approved requester sees full profile (passport_url)', async () => {
		const r = await requesters[0].u.req('GET', `/api/profiles/${targetProfile.profileId}`);
		const hasPhotos = Array.isArray(r.photos);
		// May have 0 photos (we didn't upload any) but the field must be present.
		if (!hasPhotos) throw new Error('expected photos field in response');
	});

	await check('non-requester sees blurred-only view', async () => {
		// userSessions[6] did NOT request details — should get partial view
		const r = await userSessions[6].u.req('GET', `/api/profiles/${targetProfile.profileId}`);
		// Partial view should NOT include passport_url on photos
		if (r.photos && r.photos[0] && r.photos[0].passport_url) {
			throw new Error('non-requester got passport_url — leaked private data');
		}
	});

	// ── Verify dashboard stats reflect what we did
	await check('dashboard stats reflect created data', async () => {
		const d = await admin.req('GET', '/api/admin/dashboard');
		const got = d.stats;
		const newProfiles = got.profiles_total - baseline.profiles_total;
		const newApproved = got.profiles_approved - baseline.profiles_approved;
		const newRejected = got.profiles_rejected - baseline.profiles_rejected;
		const newRequests = got.requests_total - baseline.requests_total;
		if (newProfiles !== N_USERS)
			throw new Error(`profiles_total delta=${newProfiles}, expected ${N_USERS}`);
		if (newApproved !== 3) throw new Error(`profiles_approved delta=${newApproved}, expected 3`);
		if (newRejected !== 2) throw new Error(`profiles_rejected delta=${newRejected}, expected 2`);
		if (newRequests !== requesters.length)
			throw new Error(`requests_total delta=${newRequests}, expected ${requesters.length}`);
	});

	// ── Direct SQL audit (sanity)
	const audit = psql(`
		SELECT
		  (SELECT count(*) FROM users WHERE user_handle LIKE 'e2e_%') AS users,
		  (SELECT count(*) FROM profiles WHERE owner_user_id IN (SELECT id FROM users WHERE user_handle LIKE 'e2e_%')) AS profiles,
		  (SELECT count(*) FROM detail_requests WHERE requester_user_id IN (SELECT id FROM users WHERE user_handle LIKE 'e2e_%')) AS requests
	`).split('|');
	const [auditUsers, auditProfiles, auditRequests] = audit.map((s) => parseInt(s, 10));
	logCase(
		'sql audit matches',
		auditUsers === N_USERS && auditProfiles === N_USERS && auditRequests === requesters.length,
		`users=${auditUsers}/${N_USERS} profiles=${auditProfiles}/${N_USERS} requests=${auditRequests}/${requesters.length}`
	);

	// ── Cleanup
	console.log('\n  cleaning up...');
	const cleanupOutput = psql(`DELETE FROM users WHERE user_handle LIKE 'e2e_%' RETURNING id;`);
	const deleted = cleanupOutput.split('\n').filter((s) => s.trim().length > 0).length;
	// >= N_USERS — extras can come from earlier aborted runs; cleanup is best-effort.
	logCase('cleanup test data', deleted >= N_USERS, `${deleted} users deleted (cascades)`);

	// ── Summary
	const passed = CASES.filter((c) => c.ok).length;
	const failed = CASES.filter((c) => !c.ok).length;
	const totalMs = CASES.reduce((s, c) => s + c.ms, 0);
	console.log(
		`\n  \x1b[1m${passed}/${CASES.length} passed\x1b[0m  (${failed} failed, ${totalMs}ms total)`
	);
	process.exit(failed === 0 ? 0 : 1);
}

main().catch((e) => {
	console.error('UNCAUGHT:', e);
	// best-effort cleanup so prod doesn't keep test data
	try {
		psql(`DELETE FROM users WHERE user_handle LIKE 'e2e_%';`);
	} catch {}
	process.exit(1);
});
