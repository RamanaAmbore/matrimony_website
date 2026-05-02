<script lang="ts">
	import { Heart, Search, Users, Shield } from 'lucide-svelte';
	import KalashaDivider from '$lib/components/KalashaDivider.svelte';
	import PaisleyAccent from '$lib/components/PaisleyAccent.svelte';

	let { data } = $props();
</script>

<svelte:head>
	<title>Maratha Kalyanam — Find Your Partner</title>
	<meta
		name="description"
		content="Maratha Kalyanam — the trusted matrimonial platform for Telugu-Maratha families. Find your perfect life partner."
	/>
</svelte:head>

<!-- ── Hero section ─────────────────────────────────────────────────────── -->
<section
	class="relative overflow-hidden bg-gradient-to-br from-maroon via-maroon/90 to-ink px-4 py-20 text-center md:py-32"
>
	<!-- Paisley corner accents -->
	<PaisleyAccent class="absolute top-4 left-4 rotate-45" size={64} color="#c9a227" opacity={0.25} />
	<PaisleyAccent
		class="absolute top-4 right-4 -rotate-45 scale-x-[-1]"
		size={64}
		color="#c9a227"
		opacity={0.25}
	/>
	<PaisleyAccent
		class="absolute bottom-4 left-4 rotate-180"
		size={48}
		color="#f4a300"
		opacity={0.2}
	/>
	<PaisleyAccent
		class="absolute right-4 bottom-4 -rotate-[135deg]"
		size={48}
		color="#f4a300"
		opacity={0.2}
	/>

	<div class="relative mx-auto max-w-3xl">
		<!-- Devanagari subtitle -->
		<p class="mb-2 font-serif text-base text-saffron/80 md:text-lg">
			तेलुगु–मराठा विवाह सेवा
		</p>

		<h1 class="mb-4 font-serif text-4xl font-bold text-cream md:text-6xl">
			मराठा <span class="text-saffron">कल्याणम्</span>
		</h1>
		<p class="mb-2 text-xl text-cream/70 md:text-2xl">
			<em>Maratha Kalyanam</em>
		</p>

		<p class="mb-8 text-base text-cream/60 md:text-lg">
			The trusted matrimonial platform for Telugu-Maratha families.<br
				class="hidden md:block"
			/>
			Connecting hearts across Andhra Pradesh, Telangana, and Maharashtra.
		</p>

		<div class="flex flex-col items-center justify-center gap-3 sm:flex-row">
			<a
				href="/search"
				class="inline-flex items-center gap-2 rounded-lg bg-saffron px-6 py-3 font-semibold text-ink shadow-lg transition-all duration-200 hover:bg-marigold hover:shadow-xl focus-visible:outline-2 focus-visible:outline-white"
			>
				<Search size={18} />
				Find Your Partner
			</a>

			{#if !data.user}
				<a
					href="/register"
					class="inline-flex items-center gap-2 rounded-lg border-2 border-saffron/60 px-6 py-3 font-semibold text-cream transition-all duration-200 hover:border-saffron hover:bg-saffron/10 focus-visible:outline-2 focus-visible:outline-white"
				>
					<Heart size={18} />
					Create Profile
				</a>
			{:else}
				<a
					href="/dashboard"
					class="inline-flex items-center gap-2 rounded-lg border-2 border-saffron/60 px-6 py-3 font-semibold text-cream transition-all duration-200 hover:border-saffron hover:bg-saffron/10 focus-visible:outline-2 focus-visible:outline-white"
				>
					My Profiles
				</a>
			{/if}
		</div>
	</div>

	<!-- Decorative bottom wave -->
	<div class="absolute right-0 bottom-0 left-0 overflow-hidden" aria-hidden="true">
		<svg viewBox="0 0 1440 60" fill="none" xmlns="http://www.w3.org/2000/svg" class="w-full">
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

		<h2 class="mt-6 mb-12 text-center font-serif text-3xl font-semibold text-maroon md:text-4xl">
			Why Maratha Kalyanam?
		</h2>

		<div class="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
			<!-- Card 1 -->
			<div class="card group text-center transition-shadow duration-200 hover:shadow-md">
				<div
					class="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-full bg-saffron/10 group-hover:bg-saffron/20"
				>
					<Users size={28} class="text-saffron" />
				</div>
				<h3 class="mb-2 font-serif text-xl font-semibold text-maroon">Community-Focused</h3>
				<p class="text-sm text-ink/70">
					Built specifically for Telugu-Maratha families with deep respect for gotra, nakshatram,
					kuldevata, and devak traditions.
				</p>
			</div>

			<!-- Card 2 -->
			<div class="card group text-center transition-shadow duration-200 hover:shadow-md">
				<div
					class="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-full bg-vermilion/10 group-hover:bg-vermilion/20"
				>
					<Shield size={28} class="text-vermilion" />
				</div>
				<h3 class="mb-2 font-serif text-xl font-semibold text-maroon">Admin-Verified</h3>
				<p class="text-sm text-ink/70">
					Every profile is reviewed and approved by our team. Contact details shared only after
					mutual interest and admin approval.
				</p>
			</div>

			<!-- Card 3 -->
			<div class="card group text-center transition-shadow duration-200 hover:shadow-md sm:col-span-2 lg:col-span-1">
				<div
					class="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-full bg-gold/10 group-hover:bg-gold/20"
				>
					<Heart size={28} class="text-gold" fill="currentColor" />
				</div>
				<h3 class="mb-2 font-serif text-xl font-semibold text-maroon">Privacy First</h3>
				<p class="text-sm text-ink/70">
					Photos are blurred in search results. Full details — including passport photo — are emailed
					only after admin approval of a request.
				</p>
			</div>
		</div>

		<KalashaDivider class="mt-12" />
	</div>
</section>

<!-- ── How it works ──────────────────────────────────────────────────────── -->
<section class="bg-white px-4 py-16">
	<div class="mx-auto max-w-4xl">
		<h2 class="mb-12 text-center font-serif text-3xl font-semibold text-maroon md:text-4xl">
			How It Works
		</h2>

		<ol class="relative border-l-2 border-gold/40 pl-8 space-y-10">
			{#each [
				{ step: '01', title: 'Register & Verify', desc: 'Create an account with your email and verify it. Email verification is required before creating a profile.', color: 'bg-saffron' },
				{ step: '02', title: 'Create Your Profile', desc: 'Fill in your personal, astrological (gotra, nakshatram, rashi), and family details. Upload a clear passport-style photo.', color: 'bg-gold' },
				{ step: '03', title: 'Admin Reviews', desc: 'Our team reviews your profile for accuracy and approves it. You\'ll be notified once it\'s live.', color: 'bg-vermilion' },
				{ step: '04', title: 'Browse & Request', desc: 'Search approved profiles. When you find a match, click "Request Full Details". Admin will verify and email the full info.', color: 'bg-maroon' }
			] as item}
				<li class="relative">
					<span
						class="absolute -left-[2.85rem] flex h-9 w-9 items-center justify-center rounded-full text-sm font-bold text-cream {item.color}"
					>
						{item.step}
					</span>
					<h3 class="mb-1 font-serif text-xl font-semibold text-maroon">{item.title}</h3>
					<p class="text-ink/70">{item.desc}</p>
				</li>
			{/each}
		</ol>

		<div class="mt-12 text-center">
			<a
				href="/register"
				class="inline-flex items-center gap-2 rounded-lg bg-maroon px-8 py-3 font-semibold text-cream shadow-md transition-all duration-200 hover:border hover:border-gold hover:shadow-lg focus-visible:outline-2 focus-visible:outline-saffron"
			>
				<Heart size={18} />
				Get Started Today
			</a>
		</div>
	</div>
</section>
