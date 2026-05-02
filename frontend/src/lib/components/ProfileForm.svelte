<script lang="ts">
	import { untrack } from 'svelte';
	import type { Profile, ProfilePayload } from '$lib/api';

	let {
		initialData = {},
		onSubmit,
		submitting = false,
		serverErrors = {}
	}: {
		initialData?: Partial<Profile>;
		onSubmit: (data: Partial<ProfilePayload>) => void;
		submitting?: boolean;
		serverErrors?: Record<string, string>;
	} = $props();

	// Form state — seeded once from initialData using untrack to avoid reactive capture warning.
	// This is intentionally one-shot: the form owns its own state after first render.
	let gender = $state<'bride' | 'groom'>(untrack(() => initialData.gender ?? 'bride'));
	let first_name = $state(untrack(() => initialData.first_name ?? ''));
	let last_name = $state(untrack(() => initialData.last_name ?? ''));
	let dob = $state(untrack(() => initialData.dob ?? ''));
	let height_cm = $state(untrack(() => initialData.height_cm ?? 160));
	let complexion = $state(untrack(() => initialData.complexion ?? ''));
	let education = $state(untrack(() => initialData.education ?? ''));
	let occupation = $state(untrack(() => initialData.occupation ?? ''));
	let annual_income_inr = $state<number | ''>(untrack(() => initialData.annual_income_inr ?? ''));
	let city = $state(untrack(() => initialData.city ?? ''));
	let state_field = $state(untrack(() => initialData.state ?? 'Telangana'));
	let country = $state(untrack(() => initialData.country ?? 'India'));
	let gotra = $state(untrack(() => initialData.gotra ?? ''));
	let kuldevata = $state(untrack(() => initialData.kuldevata ?? ''));
	let devak = $state(untrack(() => initialData.devak ?? ''));
	let surname_clan = $state(untrack(() => initialData.surname_clan ?? ''));
	let nakshatram = $state(untrack(() => initialData.nakshatram ?? ''));
	let rashi = $state(untrack(() => initialData.rashi ?? ''));
	let manglik = $state<'yes' | 'no' | 'partial' | 'unknown'>(untrack(() => initialData.manglik ?? 'unknown'));
	let mother_tongue = $state(untrack(() => initialData.mother_tongue ?? 'Telugu'));
	let diet = $state<'veg' | 'non-veg' | 'eggetarian'>(untrack(() => initialData.diet ?? 'veg'));
	let about = $state(untrack(() => initialData.about ?? ''));
	let partner_expectations = $state(untrack(() => initialData.partner_expectations ?? ''));

	let errors = $state<Record<string, string>>({});

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

	const INDIA_STATES = [
		'Andhra Pradesh', 'Arunachal Pradesh', 'Assam', 'Bihar', 'Chhattisgarh',
		'Goa', 'Gujarat', 'Haryana', 'Himachal Pradesh', 'Jharkhand', 'Karnataka',
		'Kerala', 'Madhya Pradesh', 'Maharashtra', 'Manipur', 'Meghalaya', 'Mizoram',
		'Nagaland', 'Odisha', 'Punjab', 'Rajasthan', 'Sikkim', 'Tamil Nadu',
		'Telangana', 'Tripura', 'Uttar Pradesh', 'Uttarakhand', 'West Bengal',
		'Delhi', 'Jammu & Kashmir', 'Ladakh', 'Puducherry', 'Other'
	];

	const COMPLEXIONS = ['Very Fair', 'Fair', 'Wheatish', 'Wheatish Brown', 'Dark'];

	function validate(): boolean {
		const e: Record<string, string> = {};
		if (!first_name.trim()) e.first_name = 'Required';
		if (!last_name.trim()) e.last_name = 'Required';
		if (!dob) e.dob = 'Date of birth is required';
		else {
			const age = new Date().getFullYear() - new Date(dob).getFullYear();
			if (age < 18) e.dob = 'Must be at least 18 years old';
		}
		if (!education.trim()) e.education = 'Required';
		if (!occupation.trim()) e.occupation = 'Required';
		if (!city.trim()) e.city = 'Required';
		if (!gotra.trim()) e.gotra = 'Required';
		if (!nakshatram) e.nakshatram = 'Required';
		if (!rashi) e.rashi = 'Required';
		if (about.length > 500) e.about = 'Max 500 characters';
		if (partner_expectations.length > 500) e.partner_expectations = 'Max 500 characters';
		errors = e;
		return Object.keys(e).length === 0;
	}

	function handleSubmit(e: Event) {
		e.preventDefault();
		if (!validate()) return;

		const data: Partial<ProfilePayload> = {
			gender,
			first_name: first_name.trim(),
			last_name: last_name.trim(),
			dob,
			height_cm: Number(height_cm),
			complexion,
			education: education.trim(),
			occupation: occupation.trim(),
			annual_income_inr: annual_income_inr === '' ? null : Number(annual_income_inr),
			city: city.trim(),
			state: state_field,
			country: country.trim(),
			gotra: gotra.trim(),
			kuldevata: kuldevata.trim(),
			devak: devak.trim(),
			surname_clan: surname_clan.trim(),
			nakshatram,
			rashi,
			manglik,
			mother_tongue: mother_tongue.trim(),
			diet,
			about: about.trim(),
			partner_expectations: partner_expectations.trim()
		};
		onSubmit(data);
	}

	// Merge server errors into local errors
	$effect(() => {
		if (Object.keys(serverErrors).length > 0) {
			errors = { ...errors, ...serverErrors };
		}
	});
</script>

<form onsubmit={handleSubmit} novalidate class="space-y-8">
	<!-- ── Personal info ─────────────────────────────────────────────────── -->
	<section class="card">
		<h2 class="mb-4 font-serif text-xl font-semibold text-maroon">Personal Details</h2>

		<!-- Gender -->
		<fieldset class="mb-4">
			<legend class="label">Profile for <span class="text-vermilion">*</span></legend>
			<div class="flex gap-6 mt-1">
				{#each [{ value: 'bride', label: 'Bride' }, { value: 'groom', label: 'Groom' }] as opt}
					<label class="flex items-center gap-2 cursor-pointer">
						<input
							type="radio"
							name="gender"
							value={opt.value}
							bind:group={gender}
							class="accent-maroon"
						/>
						<span>{opt.label}</span>
					</label>
				{/each}
			</div>
		</fieldset>

		<div class="grid gap-4 sm:grid-cols-2">
			<div>
				<label for="first_name" class="label">First Name <span class="text-vermilion">*</span></label>
				<input id="first_name" type="text" class="input" class:border-vermilion={errors.first_name} bind:value={first_name} />
				{#if errors.first_name}<p class="mt-1 text-xs text-vermilion">{errors.first_name}</p>{/if}
			</div>
			<div>
				<label for="last_name" class="label">Last Name <span class="text-vermilion">*</span></label>
				<input id="last_name" type="text" class="input" class:border-vermilion={errors.last_name} bind:value={last_name} />
				{#if errors.last_name}<p class="mt-1 text-xs text-vermilion">{errors.last_name}</p>{/if}
			</div>
			<div>
				<label for="dob" class="label">Date of Birth <span class="text-vermilion">*</span></label>
				<input id="dob" type="date" class="input" class:border-vermilion={errors.dob} bind:value={dob} max={new Date().toISOString().split('T')[0]} />
				{#if errors.dob}<p class="mt-1 text-xs text-vermilion">{errors.dob}</p>{/if}
			</div>
			<div>
				<label for="height_cm" class="label">Height: {height_cm} cm</label>
				<input id="height_cm" type="range" min="120" max="220" step="1" bind:value={height_cm} class="w-full accent-maroon mt-2" />
				<div class="flex justify-between text-xs text-ink/40 mt-1">
					<span>120 cm</span><span>220 cm</span>
				</div>
			</div>
			<div>
				<label for="complexion" class="label">Complexion</label>
				<select id="complexion" class="input" bind:value={complexion}>
					<option value="">Select…</option>
					{#each COMPLEXIONS as c}
						<option value={c}>{c}</option>
					{/each}
				</select>
			</div>
			<div>
				<label for="mother_tongue" class="label">Mother Tongue</label>
				<input id="mother_tongue" type="text" class="input" bind:value={mother_tongue} placeholder="Telugu" />
			</div>
		</div>

		<!-- Diet -->
		<fieldset class="mt-4">
			<legend class="label">Diet</legend>
			<div class="flex gap-6 mt-1 flex-wrap">
				{#each [{ value: 'veg', label: 'Vegetarian' }, { value: 'non-veg', label: 'Non-Vegetarian' }, { value: 'eggetarian', label: 'Eggetarian' }] as opt}
					<label class="flex items-center gap-2 cursor-pointer">
						<input type="radio" name="diet" value={opt.value} bind:group={diet} class="accent-maroon" />
						<span>{opt.label}</span>
					</label>
				{/each}
			</div>
		</fieldset>
	</section>

	<!-- ── Education & profession ─────────────────────────────────────────── -->
	<section class="card">
		<h2 class="mb-4 font-serif text-xl font-semibold text-maroon">Education & Profession</h2>
		<div class="grid gap-4 sm:grid-cols-2">
			<div>
				<label for="education" class="label">Highest Education <span class="text-vermilion">*</span></label>
				<input id="education" type="text" class="input" class:border-vermilion={errors.education} bind:value={education} placeholder="e.g. B.Tech, M.Sc" />
				{#if errors.education}<p class="mt-1 text-xs text-vermilion">{errors.education}</p>{/if}
			</div>
			<div>
				<label for="occupation" class="label">Occupation <span class="text-vermilion">*</span></label>
				<input id="occupation" type="text" class="input" class:border-vermilion={errors.occupation} bind:value={occupation} placeholder="e.g. Software Engineer" />
				{#if errors.occupation}<p class="mt-1 text-xs text-vermilion">{errors.occupation}</p>{/if}
			</div>
			<div class="sm:col-span-2">
				<label for="annual_income" class="label">Annual Income (INR) — optional</label>
				<input id="annual_income" type="number" min="0" step="10000" class="input" bind:value={annual_income_inr} placeholder="e.g. 800000" />
			</div>
		</div>
	</section>

	<!-- ── Location ─────────────────────────────────────────────────────── -->
	<section class="card">
		<h2 class="mb-4 font-serif text-xl font-semibold text-maroon">Location</h2>
		<div class="grid gap-4 sm:grid-cols-3">
			<div>
				<label for="city" class="label">City <span class="text-vermilion">*</span></label>
				<input id="city" type="text" class="input" class:border-vermilion={errors.city} bind:value={city} />
				{#if errors.city}<p class="mt-1 text-xs text-vermilion">{errors.city}</p>{/if}
			</div>
			<div>
				<label for="state" class="label">State</label>
				<select id="state" class="input" bind:value={state_field}>
					{#each INDIA_STATES as s}
						<option value={s}>{s}</option>
					{/each}
				</select>
			</div>
			<div>
				<label for="country" class="label">Country</label>
				<input id="country" type="text" class="input" bind:value={country} placeholder="India" />
			</div>
		</div>
	</section>

	<!-- ── Astrological / family ─────────────────────────────────────────── -->
	<section class="card">
		<h2 class="mb-4 font-serif text-xl font-semibold text-maroon">Astrological & Family Details</h2>
		<div class="grid gap-4 sm:grid-cols-2">
			<div>
				<label for="gotra" class="label">Gotra <span class="text-vermilion">*</span></label>
				<input id="gotra" type="text" class="input" class:border-vermilion={errors.gotra} bind:value={gotra} />
				{#if errors.gotra}<p class="mt-1 text-xs text-vermilion">{errors.gotra}</p>{/if}
			</div>
			<div>
				<label for="kuldevata" class="label">Kuldevata</label>
				<input id="kuldevata" type="text" class="input" bind:value={kuldevata} />
			</div>
			<div>
				<label for="devak" class="label">Devak</label>
				<input id="devak" type="text" class="input" bind:value={devak} />
			</div>
			<div>
				<label for="surname_clan" class="label">Surname / Clan</label>
				<input id="surname_clan" type="text" class="input" bind:value={surname_clan} />
			</div>
			<div>
				<label for="nakshatram" class="label">Nakshatram <span class="text-vermilion">*</span></label>
				<select id="nakshatram" class="input" class:border-vermilion={errors.nakshatram} bind:value={nakshatram}>
					<option value="">Select…</option>
					{#each NAKSHATRAS as n}
						<option value={n}>{n}</option>
					{/each}
				</select>
				{#if errors.nakshatram}<p class="mt-1 text-xs text-vermilion">{errors.nakshatram}</p>{/if}
			</div>
			<div>
				<label for="rashi" class="label">Rashi <span class="text-vermilion">*</span></label>
				<select id="rashi" class="input" class:border-vermilion={errors.rashi} bind:value={rashi}>
					<option value="">Select…</option>
					{#each RASHIS as r}
						<option value={r}>{r}</option>
					{/each}
				</select>
				{#if errors.rashi}<p class="mt-1 text-xs text-vermilion">{errors.rashi}</p>{/if}
			</div>
		</div>

		<!-- Manglik -->
		<fieldset class="mt-4">
			<legend class="label">Manglik</legend>
			<div class="flex gap-4 mt-1 flex-wrap">
				{#each [{ value: 'yes', label: 'Yes' }, { value: 'no', label: 'No' }, { value: 'partial', label: 'Partial' }, { value: 'unknown', label: 'Unknown / Don\'t Know' }] as opt}
					<label class="flex items-center gap-2 cursor-pointer">
						<input type="radio" name="manglik" value={opt.value} bind:group={manglik} class="accent-maroon" />
						<span>{opt.label}</span>
					</label>
				{/each}
			</div>
		</fieldset>
	</section>

	<!-- ── About / expectations ─────────────────────────────────────────── -->
	<section class="card">
		<h2 class="mb-4 font-serif text-xl font-semibold text-maroon">About &amp; Expectations</h2>

		<div class="space-y-4">
			<div>
				<label for="about" class="label">About Me</label>
				<textarea
					id="about"
					class="input min-h-[120px] resize-y"
					class:border-vermilion={errors.about}
					bind:value={about}
					maxlength={500}
					placeholder="A short description about yourself, your family, and interests…"
				></textarea>
				<div class="flex justify-between mt-1">
					{#if errors.about}
						<p class="text-xs text-vermilion">{errors.about}</p>
					{:else}
						<span></span>
					{/if}
					<p class="text-xs text-ink/40">{about.length}/500</p>
				</div>
			</div>

			<div>
				<label for="expectations" class="label">Partner Expectations</label>
				<textarea
					id="expectations"
					class="input min-h-[120px] resize-y"
					class:border-vermilion={errors.partner_expectations}
					bind:value={partner_expectations}
					maxlength={500}
					placeholder="Describe what you're looking for in a partner…"
				></textarea>
				<div class="flex justify-between mt-1">
					{#if errors.partner_expectations}
						<p class="text-xs text-vermilion">{errors.partner_expectations}</p>
					{:else}
						<span></span>
					{/if}
					<p class="text-xs text-ink/40">{partner_expectations.length}/500</p>
				</div>
			</div>
		</div>
	</section>

	<!-- Submit -->
	<div class="flex justify-end gap-3 pb-8">
		<a href="/dashboard" class="btn-secondary">Cancel</a>
		<button type="submit" class="btn-primary px-8" disabled={submitting}>
			{submitting ? 'Saving…' : 'Save Profile'}
		</button>
	</div>
</form>
