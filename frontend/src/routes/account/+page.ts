import type { PageLoad } from './$types';

// Auth guard is handled client-side in +page.svelte onMount,
// consistent with other protected pages in this SPA-mode app.
export const load: PageLoad = () => {
	return {};
};
