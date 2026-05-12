import type { PageLoad } from './$types';
import { redirect } from '@sveltejs/kit';

export const load: PageLoad = ({ url }) => {
	const token = url.searchParams.get('token');
	if (!token) {
		throw redirect(302, '/forgot-password');
	}
	return { token };
};
