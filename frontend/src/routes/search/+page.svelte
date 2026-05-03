<script lang="ts">
	import { onMount } from 'svelte';
	import {
		search as searchApi,
		type SearchResult,
		type PreviewSearchResult,
		type SearchParams
	} from '$lib/api';
	import { toastStore } from '$lib/stores/toast.svelte';
	import { ChevronLeft, ChevronRight, User, Loader, Search } from 'lucide-svelte';
	import DualRangeSlider from '$lib/components/DualRangeSlider.svelte';

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
	let height_min = $state(140);
	let height_max = $state(210);
	let weight_min = $state(40);
	let weight_max = $state(120);
	let gotra = $state('');
	let nakshatram = $state('');
	let rashi = $state('');
	let city = $state('');
	let state_filter = $state('');
	let country_filter = $state('');
	let pin_code_filter = $state('');
	let mother_tongue_filter = $state('');
	let manglik = $state('');
	let diet = $state('');
	let page = $state(1);
	const PER_PAGE = 12;

	let results = $state<(SearchResult | PreviewSearchResult)[]>([]);
	let total = $state(0);
	let loading = $state(false);
	let isPreview = $state(false);   // true → anonymous preview tier (capped 6, no name/edu/job)
	let debounceTimer: ReturnType<typeof setTimeout>;

	const totalPages = $derived(isPreview ? 1 : Math.ceil(total / PER_PAGE));

	async function doSearch() {
		loading = true;
		try {
			const params: SearchParams = {
				gender: gender as SearchParams['gender'] || undefined,
				age_min: age_min !== 18 ? age_min : undefined,
				age_max: age_max !== 60 ? age_max : undefined,
				height_min: height_min !== 140 ? height_min : undefined,
				height_max: height_max !== 210 ? height_max : undefined,
				weight_min: weight_min !== 40 ? weight_min : undefined,
				weight_max: weight_max !== 120 ? weight_max : undefined,
				gotra: gotra || undefined,
				nakshatram: nakshatram || undefined,
				rashi: rashi || undefined,
				city: city || undefined,
				state: state_filter || undefined,
				country: country_filter || undefined,
				pin_code: pin_code_filter || undefined,
				mother_tongue: mother_tongue_filter || undefined,
				manglik: manglik as SearchParams['manglik'] || undefined,
				diet: diet as SearchParams['diet'] || undefined,
				page,
				per_page: PER_PAGE
			};
			const res = await searchApi.query(params);
			isPreview = 'requires_registration' in res && res.requires_registration === true;
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
		[gender, gotra, nakshatram, rashi, city, state_filter, country_filter, pin_code_filter, mother_tongue_filter, manglik, diet, age_min, age_max, height_min, height_max, weight_min, weight_max].join('|')
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

	function cmToFtIn(cm: number): string {
		const totalInches = Math.round(cm / 2.54);
		const feet = Math.floor(totalInches / 12);
		const inches = totalInches % 12;
		return `${feet}'${inches}"`;
	}
</script>

<svelte:head>
	<title>Search Profiles — Maratha Kalyanam</title>
</svelte:head>

<div class="mx-auto max-w-7xl px-4 py-8">
	<div class="mb-6">
		<h1 class="font-serif text-3xl font-bold text-maroon">
			Find Your Partner
			<span class="block text-base font-normal sm:inline sm:ml-2" lang="te">
				 జీవిత భాగస్వామిని కనుగొనండి
			</span>
		</h1>
	</div>

	<div class="flex flex-col gap-6 md:flex-row">
		<!-- ── Filters sidebar — always visible (no toggle) ────────────────── -->
		<aside class="w-full shrink-0 md:w-64">
			<div class="card space-y-4 sticky top-4">
				<h2 class="font-serif text-lg font-semibold text-maroon">
					Filters · <span lang="te">వడపోత</span>
				</h2>

				<!-- Gender -->
				<div>
					<label for="f-gender" class="label">
						Looking for · <span lang="te">వెతుకుతున్నది</span>
					</label>
					<select id="f-gender" class="input text-sm" bind:value={gender}>
						<option value="">Any</option>
						<option value="bride">Bride</option>
						<option value="groom">Groom</option>
					</select>
				</div>

				<!-- Age range — dual-handle slider 18–60 -->
				<div>
					<p class="label">
						Age {age_min}–{age_max} yrs · <span lang="te">వయసు</span>
					</p>
					<div class="mt-2">
						<DualRangeSlider min={18} max={60} bind:valueMin={age_min} bind:valueMax={age_max} />
					</div>
					<p class="mt-0.5 text-xs text-ink/45">Filters by date of birth on record · జన్మ తేదీ ఆధారంగా</p>
				</div>

				<!-- Height range -->
				<div>
					<p class="label">
						Height {cmToFtIn(height_min)}–{cmToFtIn(height_max)} · <span lang="te">ఎత్తు</span>
					</p>
					<div class="mt-2">
						<DualRangeSlider min={140} max={210} bind:valueMin={height_min} bind:valueMax={height_max} />
					</div>
					<p class="mt-0.5 text-xs text-ink/45">Stored in cm, shown in ft/in · సెంటీమీటర్లలో నమోదు</p>
				</div>

				<!-- Weight range -->
				<div>
					<p class="label">
						Weight {weight_min}–{weight_max} kg · <span lang="te">బరువు</span>
					</p>
					<div class="mt-2">
						<DualRangeSlider min={40} max={120} bind:valueMin={weight_min} bind:valueMax={weight_max} />
					</div>
				</div>

				<!-- Gotra -->
				<div>
					<label for="f-gotra" class="label">Gotra · <span lang="te">గోత్రం</span></label>
					<input id="f-gotra" type="text" class="input text-sm" bind:value={gotra} placeholder="Any gotra" />
					<p class="mt-0.5 text-xs text-ink/45">Exact or partial gotra name · గోత్రం</p>
				</div>

				<!-- Nakshatram -->
				<div>
					<label for="f-naksh" class="label">Nakshatram · <span lang="te">నక్షత్రం</span></label>
					<select id="f-naksh" class="input text-sm" bind:value={nakshatram}>
						<option value="">Any</option>
						{#each NAKSHATRAS as n}
							<option value={n}>{n}</option>
						{/each}
					</select>
				</div>

				<!-- Rashi -->
				<div>
					<label for="f-rashi" class="label">Rashi · <span lang="te">రాశి</span></label>
					<select id="f-rashi" class="input text-sm" bind:value={rashi}>
						<option value="">Any</option>
						{#each RASHIS as r}
							<option value={r}>{r}</option>
						{/each}
					</select>
				</div>

				<!-- City -->
				<div>
					<label for="f-city" class="label">City · <span lang="te">నగరం</span></label>
					<input id="f-city" type="text" class="input text-sm" bind:value={city} placeholder="Any city" />
					<p class="mt-0.5 text-xs text-ink/45">Partial match — 'Hyder' matches Hyderabad · నగరం పేరు</p>
				</div>

				<!-- State -->
				<div>
					<label for="f-state" class="label">State · <span lang="te">రాష్ట్రం</span></label>
					<input id="f-state" type="text" class="input text-sm" bind:value={state_filter} placeholder="Any state" />
				</div>

				<!-- Country -->
				<div>
					<label for="f-country" class="label">Country · <span lang="te">దేశం</span></label>
					<input id="f-country" type="text" class="input text-sm" bind:value={country_filter} placeholder="Any country" />
				</div>

				<!-- Pin Code -->
				<div>
					<label for="f-pin" class="label">Pin Code · <span lang="te">పిన్ కోడ్</span></label>
					<input id="f-pin" type="text" inputmode="numeric" maxlength="10" class="input text-sm" bind:value={pin_code_filter} placeholder="e.g. 500001" />
					<p class="mt-0.5 text-xs text-ink/45">Matches profiles starting with this pin · పిన్ తో మొదలయ్యే</p>
				</div>

				<!-- Language -->
				<div>
					<label for="f-lang" class="label">Language · <span lang="te">భాష</span></label>
					<input id="f-lang" type="text" class="input text-sm" bind:value={mother_tongue_filter} placeholder="e.g. Telugu" />
					<p class="mt-0.5 text-xs text-ink/45">e.g. Telugu, Hindi, Marathi · భాష పేరు</p>
				</div>

				<!-- Manglik -->
				<div>
					<label for="f-manglik" class="label">Manglik · <span lang="te">మాంగళిక్</span></label>
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
					<label for="f-diet" class="label">Diet · <span lang="te">ఆహారం</span></label>
					<select id="f-diet" class="input text-sm" bind:value={diet}>
						<option value="">Any</option>
						<option value="veg">Vegetarian</option>
						<option value="non-veg">Non-Vegetarian</option>
						<option value="eggetarian">Eggetarian</option>
					</select>
				</div>

				<button
					onclick={() => {
						gender = ''; age_min = 18; age_max = 60; height_min = 140; height_max = 210; weight_min = 40; weight_max = 120; gotra = ''; nakshatram = '';
						rashi = ''; city = ''; state_filter = ''; country_filter = ''; pin_code_filter = ''; mother_tongue_filter = '';
						manglik = ''; diet = '';
					}}
					class="btn-secondary w-full text-sm py-2"
				>
					Clear Filters · <span lang="te">వడపోతలు తీసివేయి</span>
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
					<Loader size={36} class="animate-spin text-tangerine" />
				</div>
			{:else if results.length === 0}
				<div class="py-20 text-center">
					<div class="mx-auto mb-4 flex h-20 w-20 items-center justify-center rounded-full bg-cream/60 border-2 border-gold/30">
						<Search size={36} class="text-gold/50" />
					</div>
					<h2 class="mt-2 font-serif text-xl font-semibold text-maroon">No profiles found</h2>
					<p class="mt-2 text-ink/60">Try adjusting your filters.</p>
				</div>
			{:else}
				<!-- Preview banner -->
				{#if isPreview}
					<div class="mb-6 rounded-lg border border-saffron/40 bg-saffron/10 p-4">
						<p class="font-serif text-lg font-semibold text-maroon">
							Showing {results.length} of {total} matching profile{total === 1 ? '' : 's'}
							<span class="font-sans text-sm font-normal text-ink/70" lang="te">
								· {total} ప్రొఫైళ్లలో {results.length} చూపబడుతున్నవి
							</span>
						</p>
						<p class="mt-1 text-sm text-ink/80">
							Register for free to see all matches, full profile details, photos and contact your potential match.
						</p>
						<a
							href="/register"
							class="btn-primary mt-3 inline-flex items-center gap-2 text-sm px-3 py-1.5"
						>
							Register Free · <span lang="te">ఉచిత నమోదు</span>
						</a>
					</div>
				{/if}

				<div class="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
					{#each results as r (r.id)}
						{@const card = r as PreviewSearchResult & SearchResult}
						<a
							href={isPreview ? '/register' : `/profiles/${r.id}`}
							class="card group flex flex-col overflow-hidden p-0 transition-all duration-200 hover:shadow-md focus-visible:outline-2 focus-visible:outline-maroon"
						>
							<!-- Blurred photo -->
							<div class="relative aspect-[4/3] overflow-hidden bg-marigold/15">
								{#if card.blurred_url || card.blurred_photo_url}
									<img
										src={card.blurred_url || card.blurred_photo_url}
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
								<span class="absolute top-2 left-2 rounded bg-maroon/90 px-2 py-0.5 text-xs font-medium text-cream capitalize">
									{r.gender}
								</span>
							</div>

							<!-- Info -->
							<div class="space-y-1 p-4">
								<h3 class="font-serif text-lg font-semibold text-maroon">
									{#if isPreview}
										{card.age} yrs
									{:else}
										{card.first_name}, {calcAge(card.dob)} yrs
									{/if}
								</h3>
								<p class="text-sm text-ink/80">
									{r.height_cm} cm{#if !isPreview} · {card.diet}{/if}
								</p>
								{#if !isPreview}
									<p class="text-sm text-ink/80">{card.occupation}</p>
								{/if}
								<p class="text-sm text-ink/70">{r.city}, {r.state}</p>

								<div class="mt-2 flex flex-wrap gap-1.5">
									{#if r.gotra}
										<span class="rounded-full border border-gold/20 bg-gold/10 px-2 py-0.5 text-xs text-maroon">
											{r.gotra}
										</span>
									{/if}
									{#if r.nakshatram}
										<span class="rounded-full border border-saffron/30 bg-saffron/10 px-2 py-0.5 text-xs text-maroon">
											{r.nakshatram}
										</span>
									{/if}
									{#if !isPreview && card.manglik && card.manglik !== 'unknown'}
										<span class="rounded-full border border-ink/10 bg-ink/5 px-2 py-0.5 text-xs text-ink/70">
											Manglik: {card.manglik}
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
