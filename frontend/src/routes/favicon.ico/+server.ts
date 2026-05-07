import type { RequestHandler } from './$types';
import faviconUrl from '$lib/favicon-bytes.ico?url';

/**
 * Serve /favicon.ico with an explicit Content-Type. SvelteKit's static
 * handler returns the bytes but does not set a MIME type for `.ico`,
 * which trips up Google's favicon fetcher and a few other crawlers.
 *
 * Vite's `?url` import bundles the asset into the build with a hashed
 * filename, then we read it back over the same SvelteKit fetch context
 * so it works in dev and prod identically.
 */
let cached: ArrayBuffer | null = null;

export const GET: RequestHandler = async ({ fetch }) => {
	if (!cached) {
		const r = await fetch(faviconUrl);
		cached = await r.arrayBuffer();
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
