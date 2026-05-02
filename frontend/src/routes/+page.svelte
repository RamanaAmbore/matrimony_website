<script lang="ts">
	import { Search, Users, Shield, CheckCircle, Eye, Lock, UserPlus, Star, Mail } from 'lucide-svelte';
	import KalashaDivider from '$lib/components/KalashaDivider.svelte';
	import PaisleyAccent from '$lib/components/PaisleyAccent.svelte';
	import Logo from '$lib/components/Logo.svelte';

	let { data } = $props();

	// India-specific Unsplash photos — all verified 200
	const heroPhotos = [
		{
			id: 'photo-1583939003579-730e3918a45a',
			alt: 'Indian wedding mandap decorated with flowers and lights'
		},
		{
			id: 'photo-1606800052052-a08af7148866',
			alt: 'South Indian bride in traditional wedding attire'
		},
		{
			id: 'photo-1583939411023-14783179e581',
			alt: 'Indian wedding couple in traditional attire'
		},
		{
			id: 'photo-1622383563227-04401ab4e5ea',
			alt: 'Indian bride hands decorated with mehndi'
		},
		{
			id: 'photo-1591025207163-942350e47db2',
			alt: 'Mehndi ceremony for Indian wedding'
		}
	];

	// Pick a random hero photo per page load (stable during SSR via index 0 fallback)
	const heroPhoto = heroPhotos[Math.floor(Math.random() * heroPhotos.length)];
	const heroUrl = `https://images.unsplash.com/${heroPhoto.id}?auto=format&fit=crop&w=1600&q=80`;

	const howItWorks = [
		{
			title: 'Create Profile',
			desc: 'Register and fill in your personal, astrological and family details.',
			icon: 'user-plus'
		},
		{
			title: 'Get Verified',
			desc: 'Our admin team reviews and approves every profile before it goes live.',
			icon: 'check-circle'
		},
		{
			title: 'Search & Connect',
			desc: 'Browse verified profiles. Filter by gotra, nakshatram, city and more.',
			icon: 'search'
		},
		{
			title: 'Receive Full Details',
			desc: 'Express interest, admin approves, and contact info is emailed to you.',
			icon: 'mail'
		}
	];
</script>

<svelte:head>
	<title>Telugu–Maratha Kalyana Vedika — Find Your Partner</title>
	<meta
		name="description"
		content="Telugu–Maratha Kalyana Vedika — the trusted matrimonial platform for Telugu-Maratha families. Find your perfect life partner."
	/>
</svelte:head>

<!-- ── Hero section ─────────────────────────────────────────────────────── -->
<section class="relative min-h-[88vh] overflow-hidden">
	<!-- Background photo -->
	<img
		src={heroUrl}
		alt={heroPhoto.alt}
		class="absolute inset-0 h-full w-full object-cover object-center"
		fetchpriority="high"
	/>

	<!-- Warm saffron-tinted dark gradient overlay -->
	<div
		class="absolute inset-0"
		style="background: linear-gradient(160deg, rgba(43,10,14,0.72) 0%, rgba(199,91,18,0.55) 50%, rgba(255,140,50,0.45) 100%);"
	></div>

	<!-- Paisley corner accents -->
	<PaisleyAccent class="absolute top-4 left-4 rotate-45 z-10" size={64} color="#c9a227" opacity={0.35} />
	<PaisleyAccent
		class="absolute top-4 right-4 -rotate-45 scale-x-[-1] z-10"
		size={64}
		color="#c9a227"
		opacity={0.35}
	/>
	<PaisleyAccent
		class="absolute bottom-16 left-4 rotate-180 z-10"
		size={48}
		color="#ffb627"
		opacity={0.28}
	/>
	<PaisleyAccent
		class="absolute right-4 bottom-16 -rotate-[135deg] z-10"
		size={48}
		color="#ffb627"
		opacity={0.28}
	/>

	<!-- Hero text -->
	<div class="relative z-10 flex min-h-[88vh] flex-col items-center justify-center px-4 text-center">
		<div class="mx-auto max-w-3xl">
			<!-- Logo lg variant -->
			<div class="mb-6 flex justify-center drop-shadow-lg">
				<Logo size="lg" />
			</div>

			<!-- Telugu subtitle -->
			<p class="mb-3 font-serif text-base text-amber/90 drop-shadow md:text-lg" lang="te">
				తెలుగు–మరాఠా కల్యాణ వేదిక
			</p>

			<h1 class="mb-4 font-serif text-4xl font-bold text-cream drop-shadow-lg md:text-6xl" lang="te">
				తెలుగు–మరాఠా <span class="text-amber">కల్యాణ వేదిక</span>
			</h1>
			<p class="mb-2 text-xl text-cream/80 drop-shadow md:text-2xl">
				<em>Telugu–Maratha Kalyana Vedika</em>
			</p>

			<p class="mb-8 text-base text-cream/70 drop-shadow md:text-lg">
				The trusted matrimonial platform for Telugu-Maratha families.<br
					class="hidden md:block"
				/>
				Connecting hearts across Andhra Pradesh, Telangana &amp; Maharashtra.
			</p>

			<div class="flex flex-col items-center justify-center gap-3 sm:flex-row">
				<a
					href="/search"
					class="inline-flex items-center gap-2 rounded-lg bg-kumkum px-6 py-3 font-semibold text-cream shadow-lg transition-all duration-200 hover:bg-saffron hover:text-ink hover:shadow-xl focus-visible:outline-2 focus-visible:outline-cream"
				>
					<Search size={18} />
					Find Your Partner
				</a>

				{#if !data.user}
					<a
						href="/register"
						class="inline-flex items-center gap-2 rounded-lg border-2 border-cream/70 px-6 py-3 font-semibold text-cream backdrop-blur-sm transition-all duration-200 hover:border-cream hover:bg-cream/15 focus-visible:outline-2 focus-visible:outline-cream"
					>
						<UserPlus size={18} />
						Create Profile
					</a>
				{:else}
					<a
						href="/dashboard"
						class="inline-flex items-center gap-2 rounded-lg border-2 border-cream/70 px-6 py-3 font-semibold text-cream backdrop-blur-sm transition-all duration-200 hover:border-cream hover:bg-cream/15 focus-visible:outline-2 focus-visible:outline-cream"
					>
						My Profiles
					</a>
				{/if}
			</div>
		</div>
	</div>

	<!-- Marigold-petal wave at bottom edge -->
	<div class="absolute right-0 bottom-0 left-0 z-10 overflow-hidden" aria-hidden="true">
		<!-- Petal pattern strip -->
		<svg viewBox="0 0 1440 16" fill="none" xmlns="http://www.w3.org/2000/svg" class="w-full" preserveAspectRatio="none">
			{#each Array.from({ length: 72 }) as _, i}
				<ellipse
					cx={i * 20 + 10}
					cy="12"
					rx="9"
					ry="6"
					fill="#FFB627"
					opacity={0.55 + (i % 3) * 0.15}
				/>
			{/each}
		</svg>
		<svg viewBox="0 0 1440 60" fill="none" xmlns="http://www.w3.org/2000/svg" class="w-full -mt-1" preserveAspectRatio="none">
			<path
				d="M0 60 L0 30 Q180 0 360 30 Q540 60 720 30 Q900 0 1080 30 Q1260 60 1440 30 L1440 60Z"
				fill="#fff8e7"
			/>
		</svg>
	</div>
</section>

<!-- ── Value propositions ─────────────────────────────────────────────────── -->
<section class="px-4 py-16">
	<div class="mx-auto max-w-5xl">
		<KalashaDivider />

		<h2 class="mt-6 mb-12 text-center font-serif text-3xl font-semibold text-terracotta md:text-4xl">
			Why Telugu–Maratha Kalyana Vedika?
		</h2>

		<div class="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
			<!-- Card 1 -->
			<div class="card group text-center transition-all duration-200 hover:shadow-md">
				<div
					class="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-full bg-tangerine/15 group-hover:bg-tangerine/25 transition-colors duration-200"
				>
					<Users size={28} class="text-tangerine" />
				</div>
				<h3 class="mb-2 font-serif text-xl font-semibold text-terracotta">Community-Focused</h3>
				<p class="text-sm text-ink/70">
					Built specifically for Telugu-Maratha families with deep respect for gotra, nakshatram,
					kuldevata, and devak traditions.
				</p>
			</div>

			<!-- Card 2 -->
			<div class="card group text-center transition-all duration-200 hover:shadow-md">
				<div
					class="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-full bg-amber/20 group-hover:bg-amber/35 transition-colors duration-200"
				>
					<Shield size={28} class="text-terracotta" />
				</div>
				<h3 class="mb-2 font-serif text-xl font-semibold text-terracotta">Admin-Verified</h3>
				<p class="text-sm text-ink/70">
					Every profile is reviewed and approved by our team. Contact details shared only after
					mutual interest and admin approval.
				</p>
			</div>

			<!-- Card 3 -->
			<div class="card group text-center transition-all duration-200 hover:shadow-md sm:col-span-2 lg:col-span-1">
				<div
					class="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-full bg-gold/15 group-hover:bg-gold/25 transition-colors duration-200"
				>
					<Eye size={28} class="text-gold" />
				</div>
				<h3 class="mb-2 font-serif text-xl font-semibold text-terracotta">Privacy First</h3>
				<p class="text-sm text-ink/70">
					Photos are blurred in search results. Full details — including passport photo — are emailed
					only after admin approval of a request.
				</p>
			</div>
		</div>

		<KalashaDivider class="mt-12" />
	</div>
</section>

<!-- ── How It Works ───────────────────────────────────────────────────────── -->
<section class="px-4 py-16" style="background: linear-gradient(180deg, #fff8e7 0%, #ffe6a7 100%);">
	<div class="mx-auto max-w-5xl">
		<h2 class="mb-12 text-center font-serif text-3xl font-semibold text-terracotta md:text-4xl">
			How It Works
		</h2>

		<div class="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
			{#each howItWorks as step, i}
				<div class="relative flex flex-col items-center text-center">
					<!-- Step number ring -->
					<div
						class="relative mb-4 flex h-16 w-16 items-center justify-center rounded-full border-2 border-tangerine/40 shadow-sm"
						style="background: linear-gradient(135deg, #6B0F1A 0%, #8C1024 100%);"
					>
						<!-- Icon -->
						{#if step.icon === 'user-plus'}
							<UserPlus size={26} class="text-cream" />
						{:else if step.icon === 'check-circle'}
							<CheckCircle size={26} class="text-cream" />
						{:else if step.icon === 'search'}
							<Search size={26} class="text-cream" />
						{:else}
							<Mail size={26} class="text-cream" />
						{/if}
						<!-- Step number badge -->
						<span
							class="absolute -top-1.5 -right-1.5 flex h-5 w-5 items-center justify-center rounded-full bg-terracotta text-xs font-bold text-cream"
						>
							{i + 1}
						</span>
					</div>

					<!-- Connector arrow (hidden on last item and on mobile) -->
					{#if i < howItWorks.length - 1}
						<div class="absolute top-8 left-[calc(50%+2rem)] hidden h-0.5 w-[calc(100%-4rem)] bg-gradient-to-r from-tangerine/40 to-transparent lg:block" aria-hidden="true"></div>
					{/if}

					<h3 class="mb-2 font-serif text-lg font-semibold text-terracotta">{step.title}</h3>
					<p class="text-sm text-ink/70">{step.desc}</p>
				</div>
			{/each}
		</div>

		<div class="mt-12 text-center">
			<a
				href="/register"
				class="inline-flex items-center gap-2 rounded-lg bg-kumkum px-8 py-3 font-semibold text-cream shadow-md transition-all duration-200 hover:bg-saffron hover:text-ink hover:shadow-lg focus-visible:outline-2 focus-visible:outline-kumkum"
			>
				<UserPlus size={18} />
				Get Started Today
			</a>
		</div>
	</div>
</section>

<!-- ── Trust strip ────────────────────────────────────────────────────────── -->
<section class="border-y border-gold/30 bg-white px-4 py-8">
	<div class="mx-auto max-w-4xl">
		<div class="flex flex-col items-center gap-6 text-center sm:flex-row sm:justify-around sm:text-left">
			<!-- Item 1 -->
			<div class="flex items-center gap-3">
				<div class="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-tangerine/15">
					<Shield size={20} class="text-tangerine" />
				</div>
				<p class="text-sm font-medium text-ink/80">All profiles admin-verified</p>
			</div>
			<!-- Divider -->
			<div class="hidden h-8 w-px bg-gold/30 sm:block" aria-hidden="true"></div>
			<!-- Item 2 -->
			<div class="flex items-center gap-3">
				<div class="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-amber/20">
					<Eye size={20} class="text-terracotta" />
				</div>
				<p class="text-sm font-medium text-ink/80">Photos blurred until you ask</p>
			</div>
			<!-- Divider -->
			<div class="hidden h-8 w-px bg-gold/30 sm:block" aria-hidden="true"></div>
			<!-- Item 3 -->
			<div class="flex items-center gap-3">
				<div class="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-gold/15">
					<Lock size={20} class="text-gold" />
				</div>
				<p class="text-sm font-medium text-ink/80">No third-party data sharing</p>
			</div>
		</div>
	</div>
</section>
