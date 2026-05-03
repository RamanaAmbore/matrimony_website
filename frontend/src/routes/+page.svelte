<script lang="ts">
	import { Search, UserPlus } from 'lucide-svelte';
	import PaisleyAccent from '$lib/components/PaisleyAccent.svelte';
	let { data } = $props();
</script>

<svelte:head>
	<title>Maratha Kalyanam — Find Your Partner</title>
	<meta
		name="description"
		content="Maratha Kalyanam — మరాఠా కల్యాణం. The trusted matrimonial platform for Maratha families in Andhra, Telangana, Maharashtra and other states. Find your perfect life partner."
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
			<!-- Platform description -->
			<p
				class="mb-2 max-w-lg text-base text-cream/95 md:text-lg"
				style="text-shadow: 0 1px 6px rgba(43,10,14,0.95), 0 2px 12px rgba(43,10,14,0.7);"
			>
				The trusted matrimonial platform for the Maratha community settled across Andhra, Telangana,
				Maharashtra and other states. Admin-verified profiles. Privacy-first photo sharing.
			</p>
			<p
				class="mb-8 max-w-lg text-base md:text-lg"
				lang="te"
				style="color: #ffe066; text-shadow: -1px -1px 0 rgba(43,10,14,0.95), 1px -1px 0 rgba(43,10,14,0.95), -1px 1px 0 rgba(43,10,14,0.95), 1px 1px 0 rgba(43,10,14,0.95), 0 0 10px rgba(255,176,0,0.6);"
			>
				ఆంధ్రప్రదేశ్, తెలంగాణ, మహారాష్ట్రలలో నివసించే మరాఠా కుటుంబాలకు విశ్వసనీయమైన వివాహ వేదిక. నిర్వాహకులు ధృవీకరించిన ప్రొఫైళ్లు. గోప్యత అగ్రగామి.
			</p>

			<div class="flex flex-col items-stretch justify-center gap-3 sm:flex-row">
				<a
					href="/search"
					class="inline-flex h-14 w-full items-center justify-center gap-2 rounded-lg bg-maroon px-6 font-semibold text-cream shadow-lg transition-all duration-200 hover:bg-saffron hover:text-ink hover:shadow-xl focus-visible:outline-2 focus-visible:outline-cream sm:w-64"
				>
					<Search size={18} />
					<span>Find Your Partner<br /><span class="text-xs font-normal" lang="te" style="color:inherit">జీవిత భాగస్వామిని కనుగొనండి</span></span>
				</a>

				{#if !data.user}
					<a
						href="/register"
						class="inline-flex h-14 w-full items-center justify-center gap-2 rounded-lg border-2 border-cream px-6 font-semibold text-cream backdrop-blur-sm transition-all duration-200 hover:border-cream hover:bg-cream/15 focus-visible:outline-2 focus-visible:outline-cream sm:w-64"
					>
						<UserPlus size={18} />
						<span>Create Profile<br /><span class="text-xs font-normal" lang="te" style="color:inherit">ప్రొఫైల్ సృష్టించండి</span></span>
					</a>
				{:else}
					<a
						href="/dashboard"
						class="inline-flex h-14 w-full items-center justify-center gap-2 rounded-lg border-2 border-cream px-6 font-semibold text-cream backdrop-blur-sm transition-all duration-200 hover:border-cream hover:bg-cream/15 focus-visible:outline-2 focus-visible:outline-cream sm:w-64"
					>
						<span>My Profiles<br /><span class="text-xs font-normal" lang="te" style="color:inherit">నా ప్రొఫైళ్లు</span></span>
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

		<h2 class="mt-6 mb-1 text-center font-serif text-3xl font-semibold text-maroon md:text-4xl">
			Why Maratha Kalyanam?
		</h2>
		<p class="mb-12 text-center text-sm" lang="te">మరాఠా కల్యాణం ఎందుకు?</p>

		<div class="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
			<!-- Community-Focused — oil lamp 🪔 -->
			<div class="card group text-center transition-all duration-200 hover:shadow-md">
				<div
					class="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-full bg-maroon/10 text-3xl group-hover:bg-maroon/20 transition-colors duration-200"
					aria-hidden="true"
				>🪔</div>
				<h3 class="mb-0.5 font-serif text-xl font-semibold text-maroon">Community-Focused</h3>
				<p class="mb-2 text-xs" lang="te">సమాజ కేంద్రంగా</p>
				<p class="text-sm text-ink/80">
					Built for Maratha families with deep respect for gotra, nakshatram,
					kuldevata, and devak traditions.
				</p>
				<p class="mt-1 text-xs" lang="te">గోత్రం, నక్షత్రం, కుల్‍దేవత మరియు దేవక్ సంప్రదాయాలను గౌరవించే మరాఠా కుటుంబాల కోసం నిర్మించబడింది.</p>
			</div>

			<!-- Admin-Verified — kalash pot 🪬 -->
			<div class="card group text-center transition-all duration-200 hover:shadow-md">
				<div
					class="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-full bg-saffron/15 text-3xl group-hover:bg-saffron/25 transition-colors duration-200"
					aria-hidden="true"
				>🛕</div>
				<h3 class="mb-0.5 font-serif text-xl font-semibold text-maroon">Admin-Verified</h3>
				<p class="mb-2 text-xs" lang="te">నిర్వాహక ధృవీకరణ</p>
				<p class="text-sm text-ink/80">
					Every profile is reviewed and approved by our team before going live.
					Contact details shared only after mutual interest.
				</p>
				<p class="mt-1 text-xs" lang="te">ప్రతి ప్రొఫైల్ మా బృందం ధృవీకరించిన తర్వాతే ప్రచురితమవుతుంది. పరస్పర ఆసక్తి తర్వాతే సంప్రదింపు వివరాలు అందుతాయి.</p>
			</div>

			<!-- Privacy First — lotus flower 🪷 -->
			<div class="card group text-center transition-all duration-200 hover:shadow-md sm:col-span-2 lg:col-span-1">
				<div
					class="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-full bg-gold/15 text-3xl group-hover:bg-gold/25 transition-colors duration-200"
					aria-hidden="true"
				>🪷</div>
				<h3 class="mb-0.5 font-serif text-xl font-semibold text-maroon">Privacy First</h3>
				<p class="mb-2 text-xs" lang="te">గోప్యత అగ్రగామి</p>
				<p class="text-sm text-ink/80">
					Photos are blurred in search results. Full details are shared only after
					admin approval of a request.
				</p>
				<p class="mt-1 text-xs" lang="te">శోధన ఫలితాలలో ఫోటోలు బ్లర్ చేయబడతాయి. నిర్వాహకుని అనుమతి తర్వాతే పూర్తి వివరాలు అందుతాయి.</p>
			</div>
		</div>

	</div>
</section>

