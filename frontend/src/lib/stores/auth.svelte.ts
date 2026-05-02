// Auth store using Svelte 5 runes
import { auth as authApi, type User } from '$lib/api';

function createAuthStore() {
	let user = $state<User | null>(null);
	let loading = $state(true);

	async function fetchMe() {
		loading = true;
		try {
			user = await authApi.me();
		} catch {
			user = null;
		} finally {
			loading = false;
		}
	}

	function setUser(u: User | null) {
		user = u;
	}

	function clear() {
		user = null;
	}

	return {
		get user() {
			return user;
		},
		get loading() {
			return loading;
		},
		fetchMe,
		setUser,
		clear
	};
}

export const authStore = createAuthStore();
