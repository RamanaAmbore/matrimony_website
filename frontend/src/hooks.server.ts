import type { Handle } from '@sveltejs/kit';

/**
 * Proxy /api/* on the SvelteKit server to the Litestar backend.
 *
 * Why: SvelteKit's `event.fetch('/api/...')` short-circuits same-origin
 * requests through its own dispatcher. /api/* is not a SvelteKit route, so
 * during SSR the load functions in +layout.ts (auth.me, site.info) get a
 * 404 from the dispatcher, the page renders with user=null, and the user
 * sees the anonymous version (or an "internal server error" when the page
 * expects authenticated state).
 *
 * In production, browser requests to /api/* go through nginx → port 8003
 * directly (bypassing this hook entirely). This hook only fires for the
 * SvelteKit-side internal short-circuit during SSR.
 *
 * In dev, vite.config.ts already proxies /api/* to localhost:8000.
 *
 * The hook forwards the original method, headers (including the Cookie
 * which SvelteKit's event.fetch propagates), query string, and body. It
 * strips the /api prefix to match nginx's behaviour
 * (`location /api/ { proxy_pass http://127.0.0.1:8003/; }`).
 */
const BACKEND_URL = process.env.BACKEND_URL || 'http://127.0.0.1:8003';

export const handle: Handle = async ({ event, resolve }) => {
	const path = event.url.pathname;
	if (path.startsWith('/api/')) {
		const target = `${BACKEND_URL}${path.slice(4)}${event.url.search}`;
		const method = event.request.method;
		const body = method === 'GET' || method === 'HEAD' ? undefined : await event.request.arrayBuffer();
		const headers = new Headers(event.request.headers);
		// host header would otherwise still say marathakalyanam.com — backend
		// doesn't care, but cleaner to drop it for the loopback request.
		headers.delete('host');

		const response = await fetch(target, {
			method,
			headers,
			body,
			redirect: 'manual'
		});

		// Pass through status + headers. Set-Cookie may need special handling
		// for multi-value, but we don't expect /api/* to issue cookies during
		// SSR-time fetches (login/logout only run client-side).
		return new Response(response.body, {
			status: response.status,
			statusText: response.statusText,
			headers: response.headers
		});
	}

	return resolve(event);
};
