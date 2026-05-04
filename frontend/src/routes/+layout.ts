import { auth, site } from '$lib/api';
import type { LayoutLoad } from './$types';

export const ssr = false; // SPA mode — all auth checked client-side

export const load: LayoutLoad = async () => {
	const [user, siteInfo] = await Promise.all([
		auth.me().catch(() => null),
		site.info().catch(() => ({ is_prod: true, site_url: '' }))
	]);
	return { user, siteInfo };
};
