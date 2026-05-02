<script lang="ts">
	import './layout.css';
	import { page } from '$app/stores';
	import { goto, invalidateAll } from '$app/navigation';
	import { auth as authApi, type User } from '$lib/api';
	import { toastStore } from '$lib/stores/toast.svelte';
	import ToastContainer from '$lib/components/ToastContainer.svelte';
	import Logo from '$lib/components/Logo.svelte';
	import { Menu, X } from 'lucide-svelte';
	import { T } from '$lib/i18n';

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
			? 'text-amber font-semibold border-b-2 border-amber pb-0.5'
			: 'text-cream/80 hover:text-amber transition-colors duration-150';
	}

	function drawerLinkClass(href: string) {
		return isActive(href)
			? 'flex items-center gap-2 rounded-lg px-3 py-2.5 bg-tangerine/20 text-tangerine font-semibold'
			: 'flex items-center gap-2 rounded-lg px-3 py-2.5 text-ink hover:bg-amber/20 hover:text-terracotta transition-colors duration-150';
	}
</script>

<svelte:head>
	<title>Telugu–Maratha Kalyana Vedika</title>
	<meta name="description" content="Telugu–Maratha Kalyana Vedika — the trusted matrimonial platform for Telugu-Maratha families across Andhra Pradesh, Telangana and Maharashtra. Find your perfect life partner with admin-verified profiles, gotra/nakshatram matching, and privacy-first photo sharing." />

	<!-- Open Graph (Facebook, LinkedIn, WhatsApp) -->
	<meta property="og:type" content="website" />
	<meta property="og:site_name" content="Telugu–Maratha Kalyana Vedika" />
	<meta property="og:title" content="Telugu–Maratha Kalyana Vedika · తెలుగు–మరాఠా కల్యాణ వేదిక" />
	<meta property="og:description" content="Trusted matrimonial platform for Telugu-Maratha families across AP, Telangana and Maharashtra. Admin-verified profiles. Gotra, nakshatram and kuldevata matching. Privacy-first." />
	<meta property="og:url" content="https://marathakalyanam.com/" />
	<meta property="og:image" content="https://images.unsplash.com/photo-1583939003579-730e3918a45a?auto=format&fit=crop&w=1200&h=630&q=80" />
	<meta property="og:image:width" content="1200" />
	<meta property="og:image:height" content="630" />
	<meta property="og:image:alt" content="Indian wedding mandap with flowers and lights" />
	<meta property="og:locale" content="en_IN" />
	<meta property="og:locale:alternate" content="te_IN" />

	<!-- Twitter / X -->
	<meta name="twitter:card" content="summary_large_image" />
	<meta name="twitter:title" content="Telugu–Maratha Kalyana Vedika · తెలుగు–మరాఠా కల్యాణ వేదిక" />
	<meta name="twitter:description" content="Trusted matrimonial platform for Telugu-Maratha families. Admin-verified profiles. Privacy-first." />
	<meta name="twitter:image" content="https://images.unsplash.com/photo-1583939003579-730e3918a45a?auto=format&fit=crop&w=1200&h=630&q=80" />
	<meta name="twitter:image:alt" content="Indian wedding mandap with flowers and lights" />

	<!-- Theme + canonical -->
	<meta name="theme-color" content="#C8102E" />
	<link rel="canonical" href="https://marathakalyanam.com/" />
</svelte:head>

<!-- ── Header ─────────────────────────────────────────────────────────────── -->
<header class="shadow-md" style="background: linear-gradient(135deg, #C8102E 0%, #F4A300 100%);">
	<div class="mx-auto flex max-w-7xl items-center justify-between px-4 py-3">
		<!-- Brand wordmark -->
		<a
			href="/"
			class="flex items-center gap-2 focus-visible:outline-2 focus-visible:outline-cream"
		>
			<Logo size="sm" />
			<span class="font-serif text-lg font-semibold leading-tight text-cream">
				<span lang="te">తెలుగు–మరాఠా కల్యాణ వేదిక</span>
				<span class="ml-1 hidden text-sm font-normal text-cream/75 sm:inline">
					· Telugu–Maratha Kalyana Vedika
				</span>
			</span>
		</a>

		<!-- Desktop nav -->
		<nav class="hidden items-center gap-6 md:flex" aria-label="Main navigation">
			<a href="/" class={navLinkClass('/')}>
				{T.home.en}&nbsp;·&nbsp;<span class="text-[0.8em] font-normal" lang="te">{T.home.te}</span>
			</a>
			<a href="/search" class={navLinkClass('/search')}>
				{T.search.en}&nbsp;·&nbsp;<span class="text-[0.8em] font-normal" lang="te">{T.search.te}</span>
			</a>
			<a href="/about" class={navLinkClass('/about')}>
				{T.aboutPage.en}&nbsp;·&nbsp;<span class="text-[0.8em] font-normal" lang="te">{T.aboutPage.te}</span>
			</a>

			{#if user}
				<a href="/dashboard" class={navLinkClass('/dashboard')}>
					{T.myProfiles.en}&nbsp;·&nbsp;<span class="text-[0.8em] font-normal" lang="te">{T.myProfiles.te}</span>
				</a>
				<a href="/requests" class={navLinkClass('/requests')}>
					{T.requests.en}&nbsp;·&nbsp;<span class="text-[0.8em] font-normal" lang="te">{T.requests.te}</span>
				</a>
				{#if user.is_admin}
					<a href="/admin" class={navLinkClass('/admin')}>
						{T.admin.en}&nbsp;·&nbsp;<span class="text-[0.8em] font-normal" lang="te">{T.admin.te}</span>
					</a>
				{/if}
				<button
					onclick={logout}
					class="rounded border border-cream/50 px-3 py-1 text-sm text-cream/80 hover:border-cream hover:text-cream focus-visible:outline-2 focus-visible:outline-cream"
				>
					{T.logout.en}&nbsp;·&nbsp;<span class="text-[0.8em] font-normal" lang="te">{T.logout.te}</span>
				</button>
			{:else}
				<a href="/login" class="rounded border border-cream px-3 py-1.5 text-sm font-medium text-cream transition-all duration-200 hover:bg-cream/15 focus-visible:outline-2 focus-visible:outline-cream">
					{T.login.en}&nbsp;·&nbsp;<span class="text-[0.8em] font-normal" lang="te">{T.login.te}</span>
				</a>
				<a href="/register" class="rounded bg-cream px-3 py-1.5 text-sm font-medium text-kumkum transition-all duration-200 hover:bg-haldi focus-visible:outline-2 focus-visible:outline-cream">
					{T.register.en}&nbsp;·&nbsp;<span class="text-[0.8em] font-normal" lang="te">{T.register.te}</span>
				</a>
			{/if}
		</nav>

		<!-- Mobile hamburger -->
		<button
			class="rounded p-2 text-cream hover:bg-white/15 focus-visible:outline-2 focus-visible:outline-cream md:hidden"
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
		<div
			class="flex items-center justify-between border-b border-gold/30 px-4 py-3"
			style="background: linear-gradient(135deg, #C8102E 0%, #F4A300 100%);"
		>
			<div class="flex items-center gap-2">
				<Logo size="sm" />
				<span class="font-serif text-base leading-tight text-cream" lang="te">తెలుగు–మరాఠా<br />కల్యాణ వేదిక</span>
			</div>
			<button
				onclick={closeDrawer}
				class="rounded p-1.5 text-cream hover:bg-white/15 focus-visible:outline-2 focus-visible:outline-cream"
				aria-label="Close menu"
			>
				<X size={22} />
			</button>
		</div>

		<!-- Drawer nav links -->
		<nav class="flex flex-col gap-1 p-4" aria-label="Mobile navigation">
			<a href="/" class={drawerLinkClass('/')} onclick={closeDrawer}>
				{T.home.en}&nbsp;·&nbsp;<span class="text-[0.82em] font-normal opacity-70" lang="te">{T.home.te}</span>
			</a>
			<a href="/search" class={drawerLinkClass('/search')} onclick={closeDrawer}>
				{T.search.en}&nbsp;·&nbsp;<span class="text-[0.82em] font-normal opacity-70" lang="te">{T.search.te}</span>
			</a>
			<a href="/about" class={drawerLinkClass('/about')} onclick={closeDrawer}>
				{T.aboutPage.en}&nbsp;·&nbsp;<span class="text-[0.82em] font-normal opacity-70" lang="te">{T.aboutPage.te}</span>
			</a>

			{#if user}
				<div class="my-2 h-px bg-gold/20"></div>
				<a href="/dashboard" class={drawerLinkClass('/dashboard')} onclick={closeDrawer}>
					{T.myProfiles.en}&nbsp;·&nbsp;<span class="text-[0.82em] font-normal opacity-70" lang="te">{T.myProfiles.te}</span>
				</a>
				<a href="/requests" class={drawerLinkClass('/requests')} onclick={closeDrawer}>
					{T.requests.en}&nbsp;·&nbsp;<span class="text-[0.82em] font-normal opacity-70" lang="te">{T.requests.te}</span>
				</a>
				{#if user.is_admin}
					<div class="my-2 h-px bg-gold/20"></div>
					<p class="px-3 text-xs font-semibold tracking-wider text-ink/40 uppercase">
						{T.admin.en}&nbsp;·&nbsp;<span lang="te" class="normal-case">{T.admin.te}</span>
					</p>
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
					class="flex w-full items-center gap-2 rounded-lg px-3 py-2.5 text-left text-vermilion hover:bg-vermilion/10 focus-visible:outline-2 focus-visible:outline-tangerine"
				>
					{T.logout.en}&nbsp;·&nbsp;<span class="text-[0.82em] font-normal opacity-70" lang="te">{T.logout.te}</span>
				</button>
			{:else}
				<div class="my-2 h-px bg-gold/20"></div>
				<a href="/login" class={drawerLinkClass('/login')} onclick={closeDrawer}>
					{T.login.en}&nbsp;·&nbsp;<span class="text-[0.82em] font-normal opacity-70" lang="te">{T.login.te}</span>
				</a>
				<a
					href="/register"
					class="flex items-center gap-2 rounded-lg bg-tangerine px-3 py-2.5 text-cream hover:bg-marigold hover:text-ink"
					onclick={closeDrawer}
				>
					{T.register.en}&nbsp;·&nbsp;<span class="text-[0.82em] font-normal opacity-80" lang="te">{T.register.te}</span>
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
<footer class="border-t border-gold/30 bg-honey/60 py-8">
	<div class="mx-auto max-w-7xl px-4">
		<div class="flex flex-col items-center gap-4 text-center md:flex-row md:justify-between md:text-left">
			<div class="flex items-center gap-3">
				<Logo size="sm" />
				<div>
					<p class="font-serif text-lg font-semibold text-terracotta" lang="te">తెలుగు–మరాఠా కల్యాణ వేదిక</p>
					<p class="text-xs text-ink/50">Telugu–Maratha Kalyana Vedika</p>
					<p class="text-sm text-ink/60">Telugu-Maratha matrimonial site</p>
				</div>
			</div>
			<div class="flex flex-wrap justify-center gap-4 text-sm text-ink/60 md:justify-end">
				<a href="/about" class="hover:text-tangerine">About</a>
				<a href="/search" class="hover:text-tangerine">Search</a>
				<a href="/contact" class="hover:text-tangerine">Contact</a>
				<a href="/privacy" class="hover:text-tangerine">Privacy</a>
			</div>
		</div>
		<div class="mt-4 flex flex-col items-center gap-1 text-center">
			<p class="text-xs text-ink/40">
				© 2026 Telugu–Maratha Kalyana Vedika · marathakalyanam.com ·
				<a href="mailto:admin@marathakalyanam.com" class="hover:text-tangerine">
					admin@marathakalyanam.com
				</a>
			</p>
			<p class="text-xs text-ink/30">
				Hero photos via <a href="https://unsplash.com" target="_blank" rel="noopener noreferrer" class="hover:text-tangerine underline">Unsplash</a>
			</p>
		</div>
	</div>
</footer>

<!-- ── Toast notifications ────────────────────────────────────────────────── -->
<ToastContainer />
