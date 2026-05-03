<script lang="ts">
	// Utility icons with no Indian equivalent — kept as lucide generics
	import { Search, UserPlus } from 'lucide-svelte';

	// Indian-themed custom icon set
	import Diya from '$lib/components/icons/Diya.svelte';
	import KalashaCheck from '$lib/components/icons/KalashaCheck.svelte';
	import TempleBell from '$lib/components/icons/TempleBell.svelte';
	import PalmLeafScroll from '$lib/components/icons/PalmLeafScroll.svelte';
	import Akshat from '$lib/components/icons/Akshat.svelte';
	import Lotus from '$lib/components/icons/Lotus.svelte';
	import Shankha from '$lib/components/icons/Shankha.svelte';
	import MangoLeafGarland from '$lib/components/icons/MangoLeafGarland.svelte';

	import KalashaDivider from '$lib/components/KalashaDivider.svelte';
	import PaisleyAccent from '$lib/components/PaisleyAccent.svelte';
	import Logo from '$lib/components/Logo.svelte';
	let { data } = $props();
</script>

<svelte:head>
	<title>Marathya Kalaynam — Find Your Partner</title>
	<meta
		name="description"
		content="Marathya Kalaynam — మరాఠా కల్యాణం. The trusted matrimonial platform for Maratha families in Andhra, Telangana, Maharashtra and other states. Find your perfect life partner."
	/>
</svelte:head>

<!-- ── Hero section ─────────────────────────────────────────────────────── -->
<section class="relative min-h-[88vh] overflow-hidden">
	<!-- Custom hero photograph (provided by user) -->
	<img
		src="/bg/home.jpg"
		alt=""
		role="presentation"
		class="absolute inset-0 h-full w-full object-cover object-center"
		fetchpriority="high"
	/>

	<!-- Warm gradient overlay — keeps photo visible while ensuring text legibility -->
	<div
		class="absolute inset-0"
		style="background: linear-gradient(180deg, rgba(43,10,14,0.55) 0%, rgba(43,10,14,0.35) 35%, rgba(107,15,26,0.45) 75%, rgba(43,10,14,0.65) 100%);"
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

			<!-- Telugu brand name -->
			<p
				class="mb-2 font-serif text-base text-saffron drop-shadow-md md:text-lg"
				lang="te"
				style="text-shadow: 0 2px 8px rgba(43,10,14,0.9), 0 1px 3px rgba(0,0,0,0.7);"
			>
				మరాఠా కల్యాణం
			</p>

			<h1
				class="mb-3 font-serif text-4xl font-bold text-cream md:text-6xl"
				style="text-shadow: 0 3px 12px rgba(43,10,14,0.95), 0 1px 4px rgba(0,0,0,0.8);"
			>
				Marathya <span class="text-marigold">Kalaynam</span>
			</h1>

			<!-- Tagline 1 -->
			<p
				class="mb-1 text-base font-medium text-cream/90 drop-shadow-md md:text-lg"
				style="text-shadow: 0 2px 6px rgba(43,10,14,0.85);"
			>
				Rooted in Tradition · United by Values
			</p>
			<p
				class="mb-3 text-sm font-light text-cream/70 drop-shadow-sm"
				lang="te"
				style="text-shadow: 0 1px 4px rgba(43,10,14,0.8);"
			>
				సంప్రదాయంలో పాతుకొని · విలువలతో కలిసి
			</p>

			<!-- Tagline 2 -->
			<p
				class="mb-1 text-sm text-cream/80 drop-shadow-sm md:text-base"
				style="text-shadow: 0 1px 4px rgba(43,10,14,0.8);"
			>
				For Maratha people in Andhra, Telangana, Maharashtra and other states
			</p>
			<p
				class="mb-8 text-xs font-light text-cream/60 drop-shadow-sm md:text-sm"
				lang="te"
				style="text-shadow: 0 1px 4px rgba(43,10,14,0.8);"
			>
				ఆంధ్ర, తెలంగాణ, మహారాష్ట్ర మరియు ఇతర రాష్ట్రాలలోని మరాఠా ప్రజల కోసం
			</p>

			<div class="flex flex-col items-center justify-center gap-3 sm:flex-row">
				<a
					href="/search"
					class="inline-flex items-center gap-2 rounded-lg bg-maroon px-6 py-3 font-semibold text-cream shadow-lg transition-all duration-200 hover:bg-saffron hover:text-ink hover:shadow-xl focus-visible:outline-2 focus-visible:outline-cream"
				>
					<Search size={18} />
					Find Your Partner
				</a>

				{#if !data.user}
					<a
						href="/register"
						class="inline-flex items-center gap-2 rounded-lg border-2 border-cream px-6 py-3 font-semibold text-cream backdrop-blur-sm transition-all duration-200 hover:border-cream hover:bg-cream/15 focus-visible:outline-2 focus-visible:outline-cream"
					>
						<UserPlus size={18} />
						Create Profile
					</a>
				{:else}
					<a
						href="/dashboard"
						class="inline-flex items-center gap-2 rounded-lg border-2 border-cream px-6 py-3 font-semibold text-cream backdrop-blur-sm transition-all duration-200 hover:border-cream hover:bg-cream/15 focus-visible:outline-2 focus-visible:outline-cream"
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

		<h2 class="mt-6 mb-12 text-center font-serif text-3xl font-semibold text-maroon md:text-4xl">
			Why Marathya Kalaynam?
		</h2>

		<div class="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
			<!-- Community-Focused — Diya (oil lamp) -->
			<div class="card group text-center transition-all duration-200 hover:shadow-md">
				<div
					class="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-full bg-maroon/10 group-hover:bg-maroon/20 transition-colors duration-200"
				>
					<Diya size={28} />
				</div>
				<h3 class="mb-2 font-serif text-xl font-semibold text-maroon">Community-Focused</h3>
				<p class="text-sm text-ink/80">
					Built specifically for Maratha families with deep respect for gotra, nakshatram,
					kuldevata, and devak traditions.
				</p>
			</div>

			<!-- Admin-Verified — Kalasha with checkmark -->
			<div class="card group text-center transition-all duration-200 hover:shadow-md">
				<div
					class="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-full bg-saffron/15 group-hover:bg-saffron/28 transition-colors duration-200"
				>
					<KalashaCheck size={28} />
				</div>
				<h3 class="mb-2 font-serif text-xl font-semibold text-maroon">Admin-Verified</h3>
				<p class="text-sm text-ink/80">
					Every profile is reviewed and approved by our team. Contact details shared only after
					mutual interest and admin approval.
				</p>
			</div>

			<!-- Privacy First — Temple Bell -->
			<div class="card group text-center transition-all duration-200 hover:shadow-md sm:col-span-2 lg:col-span-1">
				<div
					class="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-full bg-gold/15 group-hover:bg-gold/25 transition-colors duration-200"
				>
					<TempleBell size={28} />
				</div>
				<h3 class="mb-2 font-serif text-xl font-semibold text-maroon">Privacy First</h3>
				<p class="text-sm text-ink/80">
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
		<h2 class="mb-12 text-center font-serif text-3xl font-semibold text-maroon md:text-4xl">
			How It Works
		</h2>

		<div class="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
			<!-- Step 1: Create Profile — Palm-leaf scroll -->
			<div class="relative flex flex-col items-center text-center">
				<div
					class="relative mb-4 flex h-16 w-16 items-center justify-center rounded-full border-2 border-saffron/40 shadow-sm"
					style="background: linear-gradient(135deg, #6B0F1A 0%, #8C1024 100%);"
				>
					<PalmLeafScroll size={26} />
					<span
						class="absolute -top-1.5 -right-1.5 flex h-5 w-5 items-center justify-center rounded-full bg-maroon text-xs font-bold text-cream"
					>1</span>
				</div>
				<div class="absolute top-8 left-[calc(50%+2rem)] hidden h-0.5 w-[calc(100%-4rem)] bg-gradient-to-r from-saffron/40 to-transparent lg:block" aria-hidden="true"></div>
				<h3 class="mb-2 font-serif text-lg font-semibold text-maroon">Create Profile</h3>
				<p class="text-sm text-ink/80">Register and fill in your personal, astrological and family details.</p>
			</div>

			<!-- Step 2: Get Verified — Akshat (rice grains) -->
			<div class="relative flex flex-col items-center text-center">
				<div
					class="relative mb-4 flex h-16 w-16 items-center justify-center rounded-full border-2 border-saffron/40 shadow-sm"
					style="background: linear-gradient(135deg, #6B0F1A 0%, #8C1024 100%);"
				>
					<Akshat size={26} />
					<span
						class="absolute -top-1.5 -right-1.5 flex h-5 w-5 items-center justify-center rounded-full bg-maroon text-xs font-bold text-cream"
					>2</span>
				</div>
				<div class="absolute top-8 left-[calc(50%+2rem)] hidden h-0.5 w-[calc(100%-4rem)] bg-gradient-to-r from-saffron/40 to-transparent lg:block" aria-hidden="true"></div>
				<h3 class="mb-2 font-serif text-lg font-semibold text-maroon">Get Verified</h3>
				<p class="text-sm text-ink/80">Our admin team reviews and approves every profile before it goes live.</p>
			</div>

			<!-- Step 3: Search & Connect — Lotus -->
			<div class="relative flex flex-col items-center text-center">
				<div
					class="relative mb-4 flex h-16 w-16 items-center justify-center rounded-full border-2 border-saffron/40 shadow-sm"
					style="background: linear-gradient(135deg, #6B0F1A 0%, #8C1024 100%);"
				>
					<Lotus size={26} />
					<span
						class="absolute -top-1.5 -right-1.5 flex h-5 w-5 items-center justify-center rounded-full bg-maroon text-xs font-bold text-cream"
					>3</span>
				</div>
				<div class="absolute top-8 left-[calc(50%+2rem)] hidden h-0.5 w-[calc(100%-4rem)] bg-gradient-to-r from-saffron/40 to-transparent lg:block" aria-hidden="true"></div>
				<h3 class="mb-2 font-serif text-lg font-semibold text-maroon">Search &amp; Connect</h3>
				<p class="text-sm text-ink/80">Browse verified profiles. Filter by gotra, nakshatram, city and more.</p>
			</div>

			<!-- Step 4: Receive Full Details — Shankha (conch shell) -->
			<div class="relative flex flex-col items-center text-center">
				<div
					class="relative mb-4 flex h-16 w-16 items-center justify-center rounded-full border-2 border-saffron/40 shadow-sm"
					style="background: linear-gradient(135deg, #6B0F1A 0%, #8C1024 100%);"
				>
					<Shankha size={26} />
					<span
						class="absolute -top-1.5 -right-1.5 flex h-5 w-5 items-center justify-center rounded-full bg-maroon text-xs font-bold text-cream"
					>4</span>
				</div>
				<h3 class="mb-2 font-serif text-lg font-semibold text-maroon">Receive Full Details</h3>
				<p class="text-sm text-ink/80">Express interest, admin approves, and contact info is emailed to you.</p>
			</div>
		</div>

		<div class="mt-12 text-center">
			<a
				href="/register"
				class="inline-flex items-center gap-2 rounded-lg bg-maroon px-8 py-3 font-semibold text-cream shadow-md transition-all duration-200 hover:bg-saffron hover:text-ink hover:shadow-lg focus-visible:outline-2 focus-visible:outline-maroon"
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
			<!-- Item 1: All profiles admin-verified — Diya -->
			<div class="flex items-center gap-3">
				<div class="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-maroon/10">
					<Diya size={20} />
				</div>
				<p class="text-sm font-medium text-ink">All profiles admin-verified</p>
			</div>
			<!-- Divider -->
			<div class="hidden h-8 w-px bg-gold/30 sm:block" aria-hidden="true"></div>
			<!-- Item 2: Photos blurred — Lotus -->
			<div class="flex items-center gap-3">
				<div class="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-saffron/15">
					<Lotus size={20} />
				</div>
				<p class="text-sm font-medium text-ink">Photos blurred until you ask</p>
			</div>
			<!-- Divider -->
			<div class="hidden h-8 w-px bg-gold/30 sm:block" aria-hidden="true"></div>
			<!-- Item 3: No data sharing — MangoLeafGarland -->
			<div class="flex items-center gap-3">
				<div class="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-gold/15">
					<MangoLeafGarland size={20} />
				</div>
				<p class="text-sm font-medium text-ink">No third-party data sharing</p>
			</div>
		</div>
	</div>
</section>
