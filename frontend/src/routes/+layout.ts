import { auth } from '$lib/api';
import type { LayoutLoad } from './$types';

export const ssr = false; // SPA mode — all auth checked client-side

export const load: LayoutLoad = async () => {
	try {
		const user = await auth.me();
		return { user };
	} catch {
		return { user: null };
	}
};
