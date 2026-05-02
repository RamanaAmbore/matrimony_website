<script lang="ts">
	import { onMount } from 'svelte';
	import { search as searchApi, type SearchResult, type SearchParams } from '$lib/api';
	import { toastStore } from '$lib/stores/toast.svelte';
	import { SlidersHorizontal, ChevronLeft, ChevronRight, User, Loader, Search } from 'lucide-svelte';

	const NAKSHATRAS = [
		'Ashwini', 'Bharani', 'Krittika', 'Rohini', 'Mrigashirsha', 'Ardra',
		'Punarvasu', 'Pushya', 'Ashlesha', 'Magha', 'Purva Phalguni', 'Uttara Phalguni',
		'Hasta', 'Chitra', 'Swati', 'Vishakha', 'Anuradha', 'Jyeshtha',
		'Mula', 'Purva Ashadha', 'Uttara Ashadha', 'Shravana', 'Dhanishtha',
		'Shatabhisha', 'Purva Bhadrapada', 'Uttara Bhadrapada', 'Revati'
	];
	const RASHIS = [
		'Mesha (Aries)', 'Vrishabha (Taurus)', 'Mithuna (Gemini)', 'Karka (Cancer)',
		'Simha (Leo)', 'Kanya (Virgo)', 'Tula (Libra)', 'Vrishchika (Scorpio)',
		'Dhanu (Sagittarius)', 'Makara (Capricorn)', 'Kumbha (Aquarius)', 'Meena (Pisces)'
	];

	// Filter state
	let gender = $state<'bride' | 'groom' | ''>('');
	let age_min = $state(18);
	let age_max = $state(60);
	let gotra = $state('');
	let nakshatram = $state('');
	let rashi = $state('');
	let city = $state('');
	let state_filter = $state('');
	let manglik = $state('');
	let diet = $state('');
	let page = $state(1);
	const PER_PAGE = 12;

	let results = $state<SearchResult[]>([]);
	let total = $state(0);
	let loading = $state(false);
	let sidebarOpen = $state(false);
	let debounceTimer: ReturnType<typeof setTimeout>;

	const totalPages = $derived(Math.ceil(total / PER_PAGE));

	async function doSearch() {
		loading = true;
		try {
			const params: SearchParams = {
				gender: gender as SearchParams['gender'] || undefined,
				age_min: age_min !== 18 ? age_min : undefined,
				age_max: age_max !== 60 ? age_max : undefined,
				gotra: gotra || undefined,
				nakshatram: nakshatram || undefined,
				rashi: rashi || undefined,
				city: city || undefined,
				state: state_filter || undefined,
				manglik: manglik as SearchParams['manglik'] || undefined,
				diet: diet as SearchParams['diet'] || undefined,
				page,
				per_page: PER_PAGE
			};
			const res = await searchApi.query(params);
			results = res.results;
			total = res.total;
		} catch {
			toastStore.error('Search failed. Try again.');
		} finally {
			loading = false;
		}
	}

	function scheduleSearch() {
		clearTimeout(debounceTimer);
		page = 1;
		debounceTimer = setTimeout(doSearch, 400);
	}

	function goToPage(p: number) {
		page = p;
		doSearch();
		window.scrollTo({ top: 0, behavior: 'smooth' });
	}

	// Reactive filter signature — changing any filter triggers a debounced re-search
	const filterKey = $derived(
		[gender, gotra, nakshatram, rashi, city, state_filter, manglik, diet, age_min, age_max].join('|')
	);

	let mounted = $state(false);

	onMount(() => {
		mounted = true;
		doSearch();
	});

	$effect(() => {
		// eslint-disable-next-line @typescript-eslint/no-unused-expressions
		filterKey; // read to subscribe
		if (!mounted) return;
		scheduleSearch();
	});

	function calcAge(dob: string): number {
		const birth = new Date(dob);
		const now = new Date();
		let age = now.getFullYear() - birth.getFullYear();
		if (now.getMonth() < birth.getMonth() || (now.getMonth() === birth.getMonth() && now.getDate() < birth.getDate())) {
			age--;
		}
		return age;
	}
</script>

<svelte:head>
	<title>Search Profiles — Maratha Kalyanam</title>
</svelte:head>

<div class="mx-auto max-w-7xl px-4 py-8">
	<div class="mb-6 flex items-center justify-between">
		<h1 class="font-serif text-3xl font-bold text-maroon">Find Your Partner</h1>
		<!-- Mobile filter toggle -->
		<button
			onclick={() => (sidebarOpen = !sidebarOpen)}
			class="btn-secondary flex items-center gap-2 md:hidden"
		>
			<SlidersHorizontal size={18} />
			Filters
		</button>
	</div>

	<div class="flex flex-col gap-6 md:flex-row">
		<!-- ── Sidebar filters ─────────────────────────────────────────────── -->
		<aside
			class="w-full md:w-64 shrink-0
				{sidebarOpen ? 'block' : 'hidden md:block'}"
		>
			<div class="card space-y-4 sticky top-4">
				<h2 class="font-serif text-lg font-semibold text-maroon">Filters</h2>

				<!-- Gender -->
				<div>
					<label for="f-gender" class="label">Looking for</label>
					<select id="f-gender" class="input text-sm" bind:value={gender}>
						<option value="">Any</option>
						<option value="bride">Bride</option>
						<option value="groom">Groom</option>
					</select>
				</div>

				<!-- Age range -->
				<div>
					<p class="label">Age: {age_min}–{age_max} yrs</p>
					<div class="space-y-2 mt-1">
						<div class="flex items-center gap-2">
							<span class="text-xs w-8 text-ink/50">Min</span>
							<input type="range" min="18" max="80" step="1" bind:value={age_min} class="flex-1 accent-maroon" />
						</div>
						<div class="flex items-center gap-2">
							<span class="text-xs w-8 text-ink/50">Max</span>
							<input type="range" min="18" max="80" step="1" bind:value={age_max} class="flex-1 accent-maroon" />
						</div>
					</div>
				</div>

				<!-- Gotra -->
				<div>
					<label for="f-gotra" class="label">Gotra</label>
					<input id="f-gotra" type="text" class="input text-sm" bind:value={gotra} placeholder="Any gotra" />
				</div>

				<!-- Nakshatram -->
				<div>
					<label for="f-naksh" class="label">Nakshatram</label>
					<select id="f-naksh" class="input text-sm" bind:value={nakshatram}>
						<option value="">Any</option>
						{#each NAKSHATRAS as n}
							<option value={n}>{n}</option>
						{/each}
					</select>
				</div>

				<!-- Rashi -->
				<div>
					<label for="f-rashi" class="label">Rashi</label>
					<select id="f-rashi" class="input text-sm" bind:value={rashi}>
						<option value="">Any</option>
						{#each RASHIS as r}
							<option value={r}>{r}</option>
						{/each}
					</select>
				</div>

				<!-- City -->
				<div>
					<label for="f-city" class="label">City</label>
					<input id="f-city" type="text" class="input text-sm" bind:value={city} placeholder="Any city" />
				</div>

				<!-- State -->
				<div>
					<label for="f-state" class="label">State</label>
					<input id="f-state" type="text" class="input text-sm" bind:value={state_filter} placeholder="Any state" />
				</div>

				<!-- Manglik -->
				<div>
					<label for="f-manglik" class="label">Manglik</label>
					<select id="f-manglik" class="input text-sm" bind:value={manglik}>
						<option value="">Any</option>
						<option value="yes">Yes</option>
						<option value="no">No</option>
						<option value="partial">Partial</option>
						<option value="unknown">Unknown</option>
					</select>
				</div>

				<!-- Diet -->
				<div>
					<label for="f-diet" class="label">Diet</label>
					<select id="f-diet" class="input text-sm" bind:value={diet}>
						<option value="">Any</option>
						<option value="veg">Vegetarian</option>
						<option value="non-veg">Non-Vegetarian</option>
						<option value="eggetarian">Eggetarian</option>
					</select>
				</div>

				<button
					onclick={() => {
						gender = ''; age_min = 18; age_max = 60; gotra = ''; nakshatram = '';
						rashi = ''; city = ''; state_filter = ''; manglik = ''; diet = '';
					}}
					class="btn-secondary w-full text-sm py-2"
				>
					Clear Filters
				</button>
			</div>
		</aside>

		<!-- ── Results ────────────────────────────────────────────────────── -->
		<div class="flex-1">
			<!-- Results count -->
			<div class="mb-4 flex items-center justify-between text-sm text-ink/60">
				<p>
					{#if loading}
						Searching…
					{:else}
						{total} profile{total !== 1 ? 's' : ''} found
					{/if}
				</p>
				{#if total > 0}
					<p>Page {page} of {totalPages}</p>
				{/if}
			</div>

			{#if loading}
				<div class="flex items-center justify-center py-24">
					<Loader size={36} class="animate-spin text-saffron" />
				</div>
			{:else if results.length === 0}
				<div class="py-20 text-center">
					<Search size={48} class="mx-auto text-gold/30" />
					<h2 class="mt-4 font-serif text-xl font-semibold text-maroon">No profiles found</h2>
					<p class="mt-2 text-ink/60">Try adjusting your filters.</p>
				</div>
			{:else}
				<div class="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
					{#each results as result (result.id)}
						<a
							href="/profiles/{result.id}"
							class="card group flex flex-col overflow-hidden p-0 transition-shadow duration-200 hover:shadow-md focus-visible:outline-2 focus-visible:outline-saffron"
						>
							<!-- Blurred photo -->
							<div class="relative aspect-[4/3] overflow-hidden bg-cream">
								{#if result.blurred_photo_url}
									<img
										src={result.blurred_photo_url}
										alt=""
										role="presentation"
										class="h-full w-full object-cover blur-sm scale-105 group-hover:blur-[6px] transition-all duration-300"
										loading="lazy"
									/>
								{:else}
									<div class="flex h-full items-center justify-center text-gold/30">
										<User size={48} />
									</div>
								{/if}
								<!-- Gender badge -->
								<span class="absolute top-2 left-2 rounded bg-maroon/80 px-2 py-0.5 text-xs font-medium text-cream capitalize">
									{result.gender}
								</span>
							</div>

							<!-- Info -->
							<div class="p-4 space-y-1">
								<h3 class="font-serif font-semibold text-maroon text-lg">
									{result.first_name}, {calcAge(result.dob)} yrs
								</h3>
								<p class="text-sm text-ink/70">
									{result.height_cm} cm · {result.diet}
								</p>
								<p class="text-sm text-ink/70">{result.occupation}</p>
								<p class="text-sm text-ink/60">{result.city}, {result.state}</p>

								<!-- Key match fields -->
								<div class="mt-2 flex flex-wrap gap-1.5">
									{#if result.gotra}
										<span class="rounded-full bg-gold/10 px-2 py-0.5 text-xs text-maroon border border-gold/20">
											{result.gotra}
										</span>
									{/if}
									{#if result.nakshatram}
										<span class="rounded-full bg-saffron/10 px-2 py-0.5 text-xs text-maroon border border-saffron/20">
											{result.nakshatram}
										</span>
									{/if}
									{#if result.manglik !== 'unknown'}
										<span class="rounded-full bg-ink/5 px-2 py-0.5 text-xs text-ink/70 border border-ink/10">
											Manglik: {result.manglik}
										</span>
									{/if}
								</div>
							</div>
						</a>
					{/each}
				</div>

				<!-- Pagination -->
				{#if totalPages > 1}
					<div class="mt-8 flex items-center justify-center gap-2">
						<button
							onclick={() => goToPage(page - 1)}
							disabled={page <= 1}
							class="btn-secondary p-2 disabled:opacity-40"
							aria-label="Previous page"
						>
							<ChevronLeft size={18} />
						</button>

						{#each Array.from({ length: totalPages }, (_, i) => i + 1) as p}
							<button
								onclick={() => goToPage(p)}
								class="px-3 py-1.5 rounded text-sm font-medium transition-colors {p === page ? 'bg-maroon text-cream' : 'hover:bg-maroon/10 text-ink'}"
							>
								{p}
							</button>
						{/each}

						<button
							onclick={() => goToPage(page + 1)}
							disabled={page >= totalPages}
							class="btn-secondary p-2 disabled:opacity-40"
							aria-label="Next page"
						>
							<ChevronRight size={18} />
						</button>
					</div>
				{/if}
			{/if}
		</div>
	</div>
</div>
