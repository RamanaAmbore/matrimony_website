import type { RequestHandler } from './$types';
import { readFile } from 'node:fs/promises';
import { join } from 'node:path';

/**
 * Serve /favicon.ico with an explicit Content-Type. SvelteKit's static
 * handler returns the bytes but does not set a MIME type for `.ico`,
 * which trips up Google's favicon fetcher and a few other crawlers.
 *
 * The file lives in static/favicon.ico — we read it once at build time
 * via a relative path. Cache aggressively (immutable until we change it).
 */
const FAVICON_PATH = join(process.cwd(), 'static', 'favicon.ico');
let cached: Buffer | null = null;

export const GET: RequestHandler = async () => {
	if (!cached) {
		cached = await readFile(FAVICON_PATH);
	}
	return new Response(cached, {
		status: 200,
		headers: {
			'Content-Type': 'image/x-icon',
			'Cache-Control': 'public, max-age=86400, immutable'
		}
	});
};

export const prerender = false;
