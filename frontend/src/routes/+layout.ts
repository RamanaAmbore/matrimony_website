import { auth, site } from '$lib/api';
import type { LayoutLoad } from './$types';

// SSR is enabled so search engines (and the first paint for real users) get
// fully-rendered HTML. Auth state is determined from the cookie at request
// time on the server, then handed off to the client at hydration.
//
// Anonymous crawlers (no cookie) get user=null — exactly the public-page
// rendering path. The .catch() guards make the load function resilient to
// the API being slow or unavailable during a server render.

export const load: LayoutLoad = async ({ fetch }) => {
	const [user, siteInfo] = await Promise.all([
		auth.me(fetch).catch(() => null),
		site.info(fetch).catch(() => ({ is_prod: true, site_url: '' }))
	]);
	return { user, siteInfo };
};
