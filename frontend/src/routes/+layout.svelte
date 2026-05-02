<script lang="ts">
	import './layout.css';
	import { page } from '$app/stores';
	import { goto, invalidateAll } from '$app/navigation';
	import { auth as authApi, type User } from '$lib/api';
	import { toastStore } from '$lib/stores/toast.svelte';
	import ToastContainer from '$lib/components/ToastContainer.svelte';
	import { Menu, X, Heart } from 'lucide-svelte';

	let { data, children } = $props();

	let user = $derived<User | null>(data.user ?? null);
	let drawerOpen = $state(false);
	let drawerEl = $state<HTMLElement | null>(null);

	function openDrawer() {
		drawerOpen = true;
		// trap focus — give DOM time to render
		setTimeout(() => drawerEl?.focus(), 10);
	}

	function closeDrawer() {
		drawerOpen = false;
	}

	function handleDrawerKeydown(e: KeyboardEvent) {
		if (e.key === 'Escape') closeDrawer();
		// basic focus trap: Tab within drawer
		if (e.key === 'Tab' && drawerEl) {
			const focusable = drawerEl.querySelectorAll<HTMLElement>(
				'a, button, [tabindex]:not([tabindex="-1"])'
			);
			const first = focusable[0];
			const last = focusable[focusable.length - 1];
			if (e.shiftKey && document.activeElement === first) {
				e.preventDefault();
				last.focus();
			} else if (!e.shiftKey && document.activeElement === last) {
				e.preventDefault();
				first.focus();
			}
		}
	}

	async function logout() {
		try {
			await authApi.logout();
			closeDrawer();
			await invalidateAll();
			toastStore.success('Logged out successfully');
			goto('/');
		} catch {
			toastStore.error('Logout failed. Try again.');
		}
	}

	// Current path for active link highlighting
	let currentPath = $derived($page.url.pathname);

	function isActive(href: string) {
		return currentPath === href || (href !== '/' && currentPath.startsWith(href));
	}

	function navLinkClass(href: string) {
		return isActive(href)
			? 'text-saffron font-semibold border-b-2 border-saffron pb-0.5'
			: 'text-cream/80 hover:text-saffron transition-colors duration-150';
	}

	function drawerLinkClass(href: string) {
		return isActive(href)
			? 'flex items-center gap-2 rounded-lg px-3 py-2.5 bg-saffron/20 text-saffron font-semibold'
			: 'flex items-center gap-2 rounded-lg px-3 py-2.5 text-ink hover:bg-saffron/10 hover:text-maroon transition-colors duration-150';
	}
</script>

<svelte:head>
	<title>Maratha Kalyanam — Telugu-Maratha Matrimony</title>
</svelte:head>

<!-- ── Header ─────────────────────────────────────────────────────────────── -->
<header class="bg-maroon shadow-md">
	<div class="mx-auto flex max-w-7xl items-center justify-between px-4 py-3">
		<!-- Brand wordmark -->
		<a
			href="/"
			class="flex items-center gap-2 focus-visible:outline-2 focus-visible:outline-saffron"
		>
			<Heart size={22} class="text-saffron" fill="currentColor" />
			<span class="font-serif text-lg font-semibold leading-tight text-cream">
				<span class="text-saffron">मराठा</span> कल्याणम्
				<span class="ml-1 hidden text-sm font-normal text-cream/70 sm:inline">
					· Maratha Kalyanam
				</span>
			</span>
		</a>

		<!-- Desktop nav -->
		<nav class="hidden items-center gap-6 md:flex" aria-label="Main navigation">
			<a href="/" class={navLinkClass('/')}>Home</a>
			<a href="/search" class={navLinkClass('/search')}>Search</a>
			<a href="/about" class={navLinkClass('/about')}>About</a>

			{#if user}
				<a href="/dashboard" class={navLinkClass('/dashboard')}>My Profiles</a>
				<a href="/requests" class={navLinkClass('/requests')}>Requests</a>
				{#if user.is_admin}
					<a href="/admin" class={navLinkClass('/admin')}>Admin</a>
				{/if}
				<button
					onclick={logout}
					class="rounded border border-saffron/50 px-3 py-1 text-sm text-cream/80 hover:border-saffron hover:text-saffron focus-visible:outline-2 focus-visible:outline-saffron"
				>
					Logout
				</button>
			{:else}
				<a href="/login" class="btn-secondary text-sm">Login</a>
				<a href="/register" class="btn-primary text-sm">Register</a>
			{/if}
		</nav>

		<!-- Mobile hamburger -->
		<button
			class="rounded p-2 text-cream hover:bg-white/10 focus-visible:outline-2 focus-visible:outline-saffron md:hidden"
			onclick={openDrawer}
			aria-label="Open menu"
			aria-expanded={drawerOpen}
			aria-controls="mobile-drawer"
		>
			<Menu size={24} />
		</button>
	</div>
</header>

<!-- ── Mobile drawer ─────────────────────────────────────────────────────── -->
{#if drawerOpen}
	<!-- Backdrop -->
	<!-- svelte-ignore a11y_click_events_have_key_events -->
	<!-- svelte-ignore a11y_no_static_element_interactions -->
	<div
		class="fixed inset-0 z-40 bg-ink/60 backdrop-blur-sm"
		onclick={closeDrawer}
		aria-hidden="true"
	></div>

	<!-- Drawer panel -->
	<div
		id="mobile-drawer"
		role="dialog"
		aria-modal="true"
		aria-label="Navigation menu"
		bind:this={drawerEl}
		tabindex="-1"
		onkeydown={handleDrawerKeydown}
		class="fixed inset-y-0 right-0 z-50 flex w-72 flex-col bg-cream shadow-2xl focus:outline-none"
	>
		<!-- Drawer header -->
		<div class="flex items-center justify-between border-b border-gold/30 bg-maroon px-4 py-3">
			<span class="font-serif text-lg text-cream">मराठा कल्याणम्</span>
			<button
				onclick={closeDrawer}
				class="rounded p-1.5 text-cream hover:bg-white/10 focus-visible:outline-2 focus-visible:outline-saffron"
				aria-label="Close menu"
			>
				<X size={22} />
			</button>
		</div>

		<!-- Drawer nav links -->
		<nav class="flex flex-col gap-1 p-4" aria-label="Mobile navigation">
			<a href="/" class={drawerLinkClass('/')} onclick={closeDrawer}>Home</a>
			<a href="/search" class={drawerLinkClass('/search')} onclick={closeDrawer}>Search</a>
			<a href="/about" class={drawerLinkClass('/about')} onclick={closeDrawer}>About</a>

			{#if user}
				<div class="my-2 h-px bg-gold/20"></div>
				<a href="/dashboard" class={drawerLinkClass('/dashboard')} onclick={closeDrawer}>
					My Profiles
				</a>
				<a href="/requests" class={drawerLinkClass('/requests')} onclick={closeDrawer}>
					Requests
				</a>
				{#if user.is_admin}
					<div class="my-2 h-px bg-gold/20"></div>
					<p class="px-3 text-xs font-semibold tracking-wider text-ink/40 uppercase">Admin</p>
					<a href="/admin" class={drawerLinkClass('/admin')} onclick={closeDrawer}>Dashboard</a>
					<a href="/admin/profiles" class={drawerLinkClass('/admin/profiles')} onclick={closeDrawer}>
						Profiles
					</a>
					<a href="/admin/requests" class={drawerLinkClass('/admin/requests')} onclick={closeDrawer}>
						Requests
					</a>
					<a href="/admin/users" class={drawerLinkClass('/admin/users')} onclick={closeDrawer}>
						Users
					</a>
					<a href="/admin/settings" class={drawerLinkClass('/admin/settings')} onclick={closeDrawer}>
						Settings
					</a>
				{/if}
				<div class="my-2 h-px bg-gold/20"></div>
				<button
					onclick={logout}
					class="flex w-full items-center gap-2 rounded-lg px-3 py-2.5 text-left text-vermilion hover:bg-vermilion/10 focus-visible:outline-2 focus-visible:outline-saffron"
				>
					Logout
				</button>
			{:else}
				<div class="my-2 h-px bg-gold/20"></div>
				<a href="/login" class={drawerLinkClass('/login')} onclick={closeDrawer}>Login</a>
				<a
					href="/register"
					class="flex items-center gap-2 rounded-lg bg-maroon px-3 py-2.5 text-cream hover:bg-maroon/90"
					onclick={closeDrawer}
				>
					Register
				</a>
			{/if}
		</nav>
	</div>
{/if}

<!-- ── Main content ──────────────────────────────────────────────────────── -->
<main class="min-h-[calc(100vh-64px-80px)]">
	{@render children()}
</main>

<!-- ── Footer ─────────────────────────────────────────────────────────────── -->
<footer class="border-t border-gold/20 bg-maroon/5 py-8">
	<div class="mx-auto max-w-7xl px-4">
		<div class="flex flex-col items-center gap-4 text-center md:flex-row md:justify-between md:text-left">
			<div>
				<p class="font-serif text-lg font-semibold text-maroon">मराठा कल्याणम्</p>
				<p class="text-sm text-ink/60">Telugu-Maratha matrimonial site</p>
			</div>
			<div class="flex flex-wrap justify-center gap-4 text-sm text-ink/60 md:justify-end">
				<a href="/about" class="hover:text-maroon">About</a>
				<a href="/search" class="hover:text-maroon">Search</a>
				<a href="/contact" class="hover:text-maroon">Contact</a>
				<a href="/privacy" class="hover:text-maroon">Privacy</a>
			</div>
		</div>
		<p class="mt-6 text-center text-xs text-ink/40">
			© 2026 Maratha Kalyanam · marathakalyanam.com ·
			<a href="mailto:admin@marathakalyanam.com" class="hover:text-maroon">
				admin@marathakalyanam.com
			</a>
		</p>
	</div>
</footer>

<!-- ── Toast notifications ────────────────────────────────────────────────── -->
<ToastContainer />
