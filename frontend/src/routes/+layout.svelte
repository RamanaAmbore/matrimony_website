<script lang="ts">
	import './layout.css';
	import { page } from '$app/stores';
	import { goto, invalidateAll } from '$app/navigation';
	import { auth as authApi, type User } from '$lib/api';
	import { toastStore } from '$lib/stores/toast.svelte';
	import ToastContainer from '$lib/components/ToastContainer.svelte';
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
	<title>Maratha Kalyanam — మరాఠా కల్యాణం</title>
	<meta name="description" content="Maratha Kalyanam — మరాఠా కల్యాణం. The trusted matrimonial platform for Maratha families across Andhra, Telangana, Maharashtra and other states. Admin-verified profiles, gotra/nakshatram matching, privacy-first photo sharing." />

	<!-- Open Graph (Facebook, LinkedIn, WhatsApp) -->
	<meta property="og:type" content="website" />
	<meta property="og:site_name" content="Maratha Kalyanam" />
	<meta property="og:title" content="Maratha Kalyanam · మరాఠా కల్యాణం" />
	<meta property="og:description" content="Trusted matrimonial platform for Maratha families across Andhra, Telangana, Maharashtra and other states. Admin-verified profiles. Gotra, nakshatram and kuldevata matching. Privacy-first." />
	<meta property="og:url" content="https://marathakalyanam.com/" />
	<meta property="og:image" content="https://marathakalyanam.com/brand/og-image.png" />
	<meta property="og:image:width" content="1200" />
	<meta property="og:image:height" content="630" />
	<meta property="og:image:alt" content="Maratha Kalyanam — Telugu Maratha Matrimony" />
	<meta property="og:locale" content="en_IN" />
	<meta property="og:locale:alternate" content="te_IN" />

	<!-- Twitter / X -->
	<meta name="twitter:card" content="summary_large_image" />
	<meta name="twitter:title" content="Maratha Kalyanam · మరాఠా కల్యాణం" />
	<meta name="twitter:description" content="Trusted matrimonial platform for Maratha families. Admin-verified profiles. Privacy-first." />
	<meta name="twitter:image" content="https://marathakalyanam.com/brand/og-image.png" />
	<meta name="twitter:image:alt" content="Maratha Kalyanam — Telugu Maratha Matrimony" />

	<!-- PWA manifest + icons -->
	<link rel="manifest" href="/manifest.webmanifest" />
	<link rel="icon" type="image/png" sizes="512x512" href="/brand/icon-512.png" />
	<link rel="icon" type="image/png" href="/favicon.png" />
	<link rel="apple-touch-icon" href="/brand/icon-192.png" />
	<meta name="mobile-web-app-capable" content="yes" />
	<meta name="apple-mobile-web-app-capable" content="yes" />
	<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent" />
	<meta name="apple-mobile-web-app-title" content="Maratha Kalyanam" />

	<!-- Theme + canonical + crawling -->
	<meta name="theme-color" content="#6B0F1A" />
	<link rel="canonical" href="https://marathakalyanam.com/" />
	<meta name="robots" content="index, follow, max-image-preview:large" />
	<meta name="googlebot" content="index, follow" />
	<meta name="author" content="Maratha Kalyanam" />
	<meta name="publisher" content="Maratha Kalyanam" />
	<meta name="keywords" content="Maratha matrimony, Maratha Kalyanam, Maratha Kalyanam, Telugu Maratha matrimony, Andhra Pradesh matrimony, Telangana matrimony, Maharashtra matrimony, gotra matching, nakshatram matching, Maratha wedding, kuldevata, devak, Indian matrimony" />

	<!-- JSON-LD structured data: Organization + WebSite (with sitelink search action) -->
	<script type="application/ld+json">
		{
			"@context": "https://schema.org",
			"@type": "Organization",
			"name": "Maratha Kalyanam",
			"alternateName": "మరాఠా కల్యాణం",
			"url": "https://marathakalyanam.com",
			"logo": "https://marathakalyanam.com/brand/logo.png",
			"description": "Trusted matrimonial platform for Maratha families across Andhra, Telangana, Maharashtra and other states.",
			"areaServed": [
				{ "@type": "AdministrativeArea", "name": "Andhra Pradesh" },
				{ "@type": "AdministrativeArea", "name": "Telangana" },
				{ "@type": "AdministrativeArea", "name": "Maharashtra" }
			]
		}
	</script>
	<script type="application/ld+json">
		{
			"@context": "https://schema.org",
			"@type": "WebSite",
			"name": "Maratha Kalyanam",
			"url": "https://marathakalyanam.com",
			"potentialAction": {
				"@type": "SearchAction",
				"target": "https://marathakalyanam.com/search?gotra={search_term_string}",
				"query-input": "required name=search_term_string"
			}
		}
	</script>
</svelte:head>

<!-- ── Header ─────────────────────────────────────────────────────────────── -->
<header class="shadow-sm border-t-4 border-saffron border-b border-cream/25" style="background: linear-gradient(135deg, #6B0F1A 0%, #6B0F1A 100%);">
	<div class="mx-auto flex w-full max-w-5xl items-center justify-center gap-2 px-4 py-2">
		<!-- Brand wordmark — shrink-0 keeps it from compressing -->
		<a
			href="/"
			class="flex shrink-0 items-center gap-2 focus-visible:outline-2 focus-visible:outline-cream"
		>
			<div class="logo-ring"><img src="/brand/logo.png" alt="Maratha Kalyanam" class="h-9 w-auto logo-glow" /></div>
			<span class="whitespace-nowrap font-serif text-base font-semibold leading-tight">
				<span class="block leading-none" style="color:#fff8e7; text-shadow: 0 0 10px rgba(201,162,39,0.9), 0 0 24px rgba(201,162,39,0.45), 1px 1px 2px rgba(0,0,0,0.95);">Maratha Kalyanam</span>
				<span class="block text-[0.7rem] font-normal leading-tight" lang="te" style="color: #f4a300;">మరాఠా కల్యాణం</span>
			</span>
		</a>

		<!-- Desktop nav — nowrap prevents each item from breaking across lines -->
		<nav class="ml-8 hidden items-center gap-4 md:flex" aria-label="Main navigation">
			<a href="/" class="whitespace-nowrap text-base {navLinkClass('/')}">
				{T.home.en}&nbsp;·&nbsp;<span class="text-[0.8em] font-normal" lang="te">{T.home.te}</span>
			</a>
			<a href="/search" class="whitespace-nowrap text-base {navLinkClass('/search')}">
				{T.search.en}&nbsp;·&nbsp;<span class="text-[0.8em] font-normal" lang="te">{T.search.te}</span>
			</a>
			<a href="/about" class="whitespace-nowrap text-base {navLinkClass('/about')}">
				{T.aboutPage.en}&nbsp;·&nbsp;<span class="text-[0.8em] font-normal" lang="te">{T.aboutPage.te}</span>
			</a>

			{#if user}
				<a href="/dashboard" class="whitespace-nowrap text-base {navLinkClass('/dashboard')}">
					{T.myProfiles.en}&nbsp;·&nbsp;<span class="text-[0.8em] font-normal" lang="te">{T.myProfiles.te}</span>
				</a>
				<a href="/requests" class="whitespace-nowrap text-base {navLinkClass('/requests')}">
					{T.requests.en}&nbsp;·&nbsp;<span class="text-[0.8em] font-normal" lang="te">{T.requests.te}</span>
				</a>
				{#if user.is_admin}
					<a href="/admin" class="whitespace-nowrap text-base {navLinkClass('/admin')}">
						{T.admin.en}&nbsp;·&nbsp;<span class="text-[0.8em] font-normal" lang="te">{T.admin.te}</span>
					</a>
				{/if}
				<span class="hidden font-mono text-xs text-cream/50 xl:inline" title={user.email}>@{user.user_handle}</span>
				<button
					onclick={logout}
					class="whitespace-nowrap rounded border border-cream/50 px-3 py-1 text-base text-cream/80 hover:border-cream hover:text-cream focus-visible:outline-2 focus-visible:outline-cream"
				>
					{T.logout.en}&nbsp;·&nbsp;<span class="text-[0.8em] font-normal" lang="te">{T.logout.te}</span>
				</button>
			{:else}
				<a href="/login" class="whitespace-nowrap rounded border border-cream px-3 py-1.5 text-base font-medium text-cream transition-all duration-200 hover:bg-cream/15 focus-visible:outline-2 focus-visible:outline-cream">
					{T.login.en}&nbsp;·&nbsp;<span class="text-[0.8em] font-normal" lang="te">{T.login.te}</span>
				</a>
				<a href="/register" class="whitespace-nowrap rounded px-3 py-1.5 text-base font-medium text-maroon transition-all duration-200 hover:opacity-90 focus-visible:outline-2 focus-visible:outline-cream" style="background:#fde8b0;">
					{T.register.en}&nbsp;·&nbsp;<span class="text-[0.8em] font-normal" lang="te">{T.register.te}</span>
				</a>
			{/if}
		</nav>

		<!-- Mobile hamburger -->
		<button
			class="ml-auto rounded p-2 text-cream hover:bg-white/15 focus-visible:outline-2 focus-visible:outline-cream md:hidden"
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
			style="background: linear-gradient(135deg, #6B0F1A 0%, #6B0F1A 100%);"
		>
			<div class="flex items-center gap-2">
				<div class="logo-ring"><img src="/brand/logo.png" alt="Maratha Kalyanam" class="h-9 w-auto logo-glow" /></div>
				<div class="font-serif leading-tight">
					<span class="block text-sm font-semibold" style="color:#fff8e7; text-shadow: 0 0 10px rgba(201,162,39,0.9), 0 0 24px rgba(201,162,39,0.45), 1px 1px 2px rgba(0,0,0,0.95);">Maratha Kalyanam</span>
					<span class="block text-xs font-normal" lang="te" style="color: #f4a300;">మరాఠా కల్యాణం</span>
				</div>
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
				{T.home.en}&nbsp;·&nbsp;<span class="text-[0.82em] font-normal opacity-80" lang="te">{T.home.te}</span>
			</a>
			<a href="/search" class={drawerLinkClass('/search')} onclick={closeDrawer}>
				{T.search.en}&nbsp;·&nbsp;<span class="text-[0.82em] font-normal opacity-80" lang="te">{T.search.te}</span>
			</a>
			<a href="/about" class={drawerLinkClass('/about')} onclick={closeDrawer}>
				{T.aboutPage.en}&nbsp;·&nbsp;<span class="text-[0.82em] font-normal opacity-80" lang="te">{T.aboutPage.te}</span>
			</a>

			{#if user}
				<div class="my-2 h-px bg-gold/20"></div>
				<a href="/dashboard" class={drawerLinkClass('/dashboard')} onclick={closeDrawer}>
					{T.myProfiles.en}&nbsp;·&nbsp;<span class="text-[0.82em] font-normal opacity-80" lang="te">{T.myProfiles.te}</span>
				</a>
				<a href="/requests" class={drawerLinkClass('/requests')} onclick={closeDrawer}>
					{T.requests.en}&nbsp;·&nbsp;<span class="text-[0.82em] font-normal opacity-80" lang="te">{T.requests.te}</span>
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
				<p class="px-3 py-1 font-mono text-sm text-ink/50" title={user.email}>@{user.user_handle}</p>
				<button
					onclick={logout}
					class="flex w-full items-center gap-2 rounded-lg px-3 py-2.5 text-left text-vermilion hover:bg-vermilion/10 focus-visible:outline-2 focus-visible:outline-tangerine"
				>
					{T.logout.en}&nbsp;·&nbsp;<span class="text-[0.82em] font-normal opacity-80" lang="te">{T.logout.te}</span>
				</button>
			{:else}
				<div class="my-2 h-px bg-gold/20"></div>
				<a href="/login" class={drawerLinkClass('/login')} onclick={closeDrawer}>
					{T.login.en}&nbsp;·&nbsp;<span class="text-[0.82em] font-normal opacity-80" lang="te">{T.login.te}</span>
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
<!-- Subtle wedding-photo background on inner pages (home has its own full-bleed hero) -->
{#if currentPath !== '/'}
	<div class="pointer-events-none fixed inset-0 -z-10" aria-hidden="true">
		<img
			src="/bg/home.jpg"
			alt=""
			class="h-full w-full object-cover object-left opacity-55"
			loading="lazy"
		/>
		<!-- Cream wash keeps text and forms readable while letting the photo show through -->
		<div class="absolute inset-0 bg-cream/72"></div>
	</div>
{/if}

<main class="relative z-0 min-h-[calc(100vh-64px-80px)]">
	{@render children()}
</main>

<!-- ── Footer ─────────────────────────────────────────────────────────────── -->
<footer class="border-t border-gold/30 bg-maroon/95 py-10 text-cream">
	<div class="mx-auto max-w-7xl px-4">
		<div class="grid gap-8 md:grid-cols-3">
			<!-- Brand column -->
			<div class="md:col-span-2">
				<div class="flex items-center gap-3">
					<div class="logo-ring"><img src="/brand/logo.png" alt="Maratha Kalyanam" class="h-14 w-auto logo-glow" /></div>
					<div>
						<p class="font-serif text-xl font-semibold text-cream">Maratha Kalyanam</p>
						<p class="text-sm" lang="te" style="color: #f4a300;">మరాఠా కల్యాణం</p>
					</div>
				</div>
			</div>

			<!-- Contact -->
			<div>
				<h3 class="mb-3 font-serif text-sm font-semibold tracking-wider text-marigold uppercase">
					Contact
				</h3>
				<ul class="space-y-2 text-sm text-cream/80">
					<li>
						<a href="mailto:admin@marathakalyanam.com" class="hover:text-marigold">
							admin@marathakalyanam.com
						</a>
					</li>
					<li class="text-cream/60">Andhra Pradesh · Telangana</li>
					<li class="text-cream/60">India</li>
				</ul>
			</div>
		</div>

		<!-- Bottom bar -->
		<div class="mt-8 flex flex-col items-center justify-between gap-3 border-t border-gold/30 pt-6 text-xs text-cream/70 md:flex-row">
			<p>
				© 2026 Maratha Kalyanam · marathakalyanam.com
			</p>
			<p>
				Designed &amp; developed by
				<span class="font-semibold text-marigold">Ambore Software</span>
			</p>
		</div>
	</div>
</footer>

<!-- ── Toast notifications ────────────────────────────────────────────────── -->
<ToastContainer />
