import { admin } from '$lib/api';
import type { PageLoad } from './$types';
import { redirect } from '@sveltejs/kit';

export const load: PageLoad = async ({ parent, fetch: _fetch }) => {
	const { user } = await parent();
	if (!user?.is_super) {
		throw redirect(302, '/admin');
	}
	// Initial page load — fetch first page
	// Pass the event.fetch through so SSR works
	try {
		const result = await admin.auditLog({ page: 1, per_page: 50 });
		return { auditLog: result };
	} catch {
		return { auditLog: { items: [], page: 1, per_page: 50, total: 0 } };
	}
};
