<script lang="ts">
	import { untrack } from 'svelte';
	import type { Profile, ProfilePayload, MaritalStatus, BodyType, BloodGroup, FamilyType, FamilyStatus, FamilyValues, SmokeDrink } from '$lib/api';
	import { T } from '$lib/i18n';
	import { asciiOnly } from '$lib/inputFilters';
	import BilingualLabel from '$lib/components/BilingualLabel.svelte';

	function cmToFtIn(cm: number): string {
		const totalInches = Math.round(cm / 2.54);
		const feet = Math.floor(totalInches / 12);
		const inches = totalInches % 12;
		return `${feet}'${inches}"`;
	}

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

	// ── Form state — seeded once from initialData ─────────────────────────────
	// Basic Information
	let gender = $state<'bride' | 'groom'>(untrack(() => initialData.gender ?? 'bride'));
	let first_name = $state(untrack(() => initialData.first_name ?? ''));
	let last_name = $state(untrack(() => initialData.last_name ?? ''));
	let dob = $state(untrack(() => initialData.dob ?? ''));
	let marital_status = $state(untrack(() => initialData.marital_status ?? ''));
	let mother_tongue = $state(untrack(() => initialData.mother_tongue ?? 'Telugu'));
	let sub_caste = $state(untrack(() => initialData.sub_caste ?? ''));
	let surname_clan = $state(untrack(() => initialData.surname_clan ?? ''));

	// Physical
	let height_cm = $state(untrack(() => initialData.height_cm ?? 160));
	let weight_kg = $state<number | ''>(untrack(() => initialData.weight_kg ?? ''));
	let complexion = $state(untrack(() => initialData.complexion ?? ''));
	let body_type = $state(untrack(() => initialData.body_type ?? ''));
	let blood_group = $state(untrack(() => initialData.blood_group ?? ''));

	// Astrology
	let gotra = $state(untrack(() => initialData.gotra ?? ''));
	let kuldevata = $state(untrack(() => initialData.kuldevata ?? ''));
	let devak = $state(untrack(() => initialData.devak ?? ''));
	let nakshatram = $state(untrack(() => initialData.nakshatram ?? ''));
	let rashi = $state(untrack(() => initialData.rashi ?? ''));
	let manglik = $state<'yes' | 'no' | 'partial' | 'unknown'>(untrack(() => initialData.manglik ?? 'unknown'));
	let time_of_birth = $state(untrack(() => initialData.time_of_birth ?? ''));
	let place_of_birth = $state(untrack(() => initialData.place_of_birth ?? ''));

	// Education & Career
	let education = $state(untrack(() => initialData.education ?? ''));
	let college_university = $state(untrack(() => initialData.college_university ?? ''));
	let occupation = $state(untrack(() => initialData.occupation ?? ''));
	let employer = $state(untrack(() => initialData.employer ?? ''));
	let annual_income_inr = $state<number | ''>(untrack(() => initialData.annual_income_inr ?? ''));
	let work_location = $state(untrack(() => initialData.work_location ?? ''));

	// Family
	let father_name = $state(untrack(() => initialData.father_name ?? ''));
	let mother_name = $state(untrack(() => initialData.mother_name ?? ''));
	let num_family_members = $state<number | ''>(untrack(() => initialData.num_family_members ?? ''));
	let father_occupation = $state(untrack(() => initialData.father_occupation ?? ''));
	let mother_occupation = $state(untrack(() => initialData.mother_occupation ?? ''));
	let num_brothers = $state<number | ''>(untrack(() => initialData.num_brothers ?? ''));
	let num_sisters = $state<number | ''>(untrack(() => initialData.num_sisters ?? ''));
	let num_brothers_married = $state<number | ''>(untrack(() => initialData.num_brothers_married ?? ''));
	let num_sisters_married = $state<number | ''>(untrack(() => initialData.num_sisters_married ?? ''));
	let family_type = $state(untrack(() => initialData.family_type ?? ''));
	let family_status = $state(untrack(() => initialData.family_status ?? ''));
	let family_values = $state(untrack(() => initialData.family_values ?? ''));
	let native_place = $state(untrack(() => initialData.native_place ?? ''));

	// Lifestyle
	let diet = $state<'veg' | 'non-veg' | 'eggetarian' | 'jain' | 'vegan'>(untrack(() => initialData.diet ?? 'veg'));
	let smokes = $state(untrack(() => initialData.smokes ?? ''));
	let drinks = $state(untrack(() => initialData.drinks ?? ''));
	let hobbies = $state(untrack(() => initialData.hobbies ?? ''));

	// Location
	let city = $state(untrack(() => initialData.city ?? ''));
	let state_field = $state(untrack(() => initialData.state ?? 'Telangana'));
	let country = $state(untrack(() => initialData.country ?? 'India'));
	let pin_code = $state(untrack(() => initialData.pin_code ?? ''));

	// About
	let about = $state(untrack(() => initialData.about ?? ''));
	let partner_expectations = $state(untrack(() => initialData.partner_expectations ?? ''));

	let errors = $state<Record<string, string>>({});

	// ── Static lookup data ───────────────────────────────────────────────────
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

	const COMPLEXIONS = [
		{ value: 'very_fair', label: 'Very Fair' },
		{ value: 'fair', label: 'Fair' },
		{ value: 'wheatish', label: 'Wheatish' },
		{ value: 'dusky', label: 'Dusky' },
		{ value: 'dark', label: 'Dark' }
	];

	const BODY_TYPES = [
		{ value: 'slim', label: 'Slim' },
		{ value: 'average', label: 'Average' },
		{ value: 'athletic', label: 'Athletic' },
		{ value: 'heavy', label: 'Heavy' }
	];

	const BLOOD_GROUPS = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-', 'unknown'];

	const MARITAL_STATUSES = [
		{ value: 'never_married', label: 'Never Married' },
		{ value: 'divorced', label: 'Divorced' },
		{ value: 'widowed', label: 'Widowed' },
		{ value: 'awaiting_divorce', label: 'Awaiting Divorce' }
	];

	const FAMILY_STATUSES = [
		{ value: 'middle_class', label: 'Middle Class' },
		{ value: 'upper_middle', label: 'Upper Middle Class' },
		{ value: 'affluent', label: 'Affluent' },
		{ value: 'rich', label: 'Rich' }
	];

	const FAMILY_VALUES_OPTS = [
		{ value: 'orthodox', label: 'Orthodox' },
		{ value: 'traditional', label: 'Traditional' },
		{ value: 'moderate', label: 'Moderate' },
		{ value: 'liberal', label: 'Liberal' }
	];

	// Small hint shown under every ASCII-only text field
	const ASCII_HINT = 'English characters only · ఆంగ్ల అక్షరాలు మాత్రమే';

	// ── Validation ───────────────────────────────────────────────────────────
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
		if (partner_expectations.length > 800) e.partner_expectations = 'Max 800 characters';
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
			marital_status: (marital_status || null) as MaritalStatus | null,
			mother_tongue: mother_tongue.trim(),
			sub_caste: sub_caste.trim() || null,
			surname_clan: surname_clan.trim(),

			height_cm: Number(height_cm),
			weight_kg: weight_kg === '' ? null : Number(weight_kg),
			complexion: complexion || null,
			body_type: (body_type || null) as BodyType | null,
			blood_group: (blood_group || null) as BloodGroup | null,

			gotra: gotra.trim(),
			kuldevata: kuldevata.trim(),
			devak: devak.trim(),
			nakshatram,
			rashi,
			manglik,
			time_of_birth: time_of_birth || null,
			place_of_birth: place_of_birth.trim() || null,

			education: education.trim(),
			college_university: college_university.trim() || null,
			occupation: occupation.trim(),
			employer: employer.trim() || null,
			annual_income_inr: annual_income_inr === '' ? null : Number(annual_income_inr),
			work_location: work_location.trim() || null,

			father_name: father_name.trim() || null,
			mother_name: mother_name.trim() || null,
			num_family_members: num_family_members === '' ? null : Number(num_family_members),
			father_occupation: father_occupation.trim() || null,
			mother_occupation: mother_occupation.trim() || null,
			num_brothers: num_brothers === '' ? null : Number(num_brothers),
			num_sisters: num_sisters === '' ? null : Number(num_sisters),
			num_brothers_married: num_brothers_married === '' ? null : Number(num_brothers_married),
			num_sisters_married: num_sisters_married === '' ? null : Number(num_sisters_married),
			family_type: (family_type || null) as FamilyType | null,
			family_status: (family_status || null) as FamilyStatus | null,
			family_values: (family_values || null) as FamilyValues | null,
			native_place: native_place.trim() || null,

			diet,
			smokes: (smokes || null) as SmokeDrink | null,
			drinks: (drinks || null) as SmokeDrink | null,
			hobbies: hobbies.trim() || null,

			city: city.trim(),
			state: state_field,
			country: country.trim(),
			pin_code: pin_code.trim() || null,

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

<form onsubmit={handleSubmit} novalidate class="space-y-6">

	<!-- ── Section: Basic Information ──────────────────────────────────────── -->
	<details open class="card">
		<summary class="cursor-pointer font-serif text-xl font-semibold text-maroon mb-1 list-none flex items-center gap-2">
			<span class="text-tangerine">▸</span>
			Basic Information
			<span class="text-sm font-normal text-ink/50 ml-1" lang="te">మూల సమాచారం</span>
		</summary>

		<div class="mt-4 space-y-4">
			<!-- Gender -->
			<fieldset>
				<legend class="label">
					<span class="block">{T.gender.en} <span class="text-vermilion">*</span></span>
					<span class="block text-xs text-ink/60 font-normal leading-tight" lang="te">{T.gender.te}</span>
				</legend>
				<div class="flex gap-6 mt-1">
					{#each [{ value: 'bride', key: 'bride' as const }, { value: 'groom', key: 'groom' as const }] as opt}
						<label class="flex items-center gap-2 cursor-pointer">
							<input
								type="radio"
								name="gender"
								value={opt.value}
								bind:group={gender}
								class="accent-maroon"
							/>
							<span>{T[opt.key].en}</span>
							<span class="text-xs text-ink/60" lang="te">{T[opt.key].te}</span>
						</label>
					{/each}
				</div>
			</fieldset>

			<div class="grid gap-4 sm:grid-cols-2">
				<!-- First Name -->
				<div>
					<BilingualLabel key="firstName" for="first_name" required />
					<input
						id="first_name"
						type="text"
						class="input"
						class:border-vermilion={errors.first_name}
						bind:value={first_name}
						oninput={(e) => first_name = asciiOnly(e.currentTarget.value)}
					/>
					<p class="mt-0.5 text-[10px] text-ink/40">{ASCII_HINT}</p>
					{#if errors.first_name}<p class="mt-1 text-xs text-vermilion">{errors.first_name}</p>{/if}
				</div>

				<!-- Last Name -->
				<div>
					<BilingualLabel key="lastName" for="last_name" required />
					<input
						id="last_name"
						type="text"
						class="input"
						class:border-vermilion={errors.last_name}
						bind:value={last_name}
						oninput={(e) => last_name = asciiOnly(e.currentTarget.value)}
					/>
					<p class="mt-0.5 text-[10px] text-ink/40">{ASCII_HINT}</p>
					{#if errors.last_name}<p class="mt-1 text-xs text-vermilion">{errors.last_name}</p>{/if}
				</div>

				<!-- Date of Birth -->
				<div>
					<BilingualLabel key="dob" for="dob" required />
					<input
						id="dob"
						type="date"
						class="input"
						class:border-vermilion={errors.dob}
						bind:value={dob}
						max={new Date().toISOString().split('T')[0]}
					/>
					{#if errors.dob}<p class="mt-1 text-xs text-vermilion">{errors.dob}</p>{/if}
				</div>

				<!-- Marital Status -->
				<div>
					<BilingualLabel key="maritalStatus" for="marital_status" />
					<select id="marital_status" class="input" bind:value={marital_status}>
						<option value="">Select…</option>
						{#each MARITAL_STATUSES as ms}
							<option value={ms.value}>{ms.label}</option>
						{/each}
					</select>
				</div>

				<!-- Mother Tongue -->
				<div>
					<BilingualLabel key="motherTongue" for="mother_tongue" />
					<input
						id="mother_tongue"
						type="text"
						class="input"
						bind:value={mother_tongue}
						oninput={(e) => mother_tongue = asciiOnly(e.currentTarget.value)}
						placeholder="Telugu"
					/>
					<p class="mt-0.5 text-[10px] text-ink/40">{ASCII_HINT}</p>
				</div>

				<!-- Surname / Clan -->
				<div>
					<BilingualLabel key="surnameClan" for="surname_clan" />
					<input
						id="surname_clan"
						type="text"
						class="input"
						bind:value={surname_clan}
						oninput={(e) => surname_clan = asciiOnly(e.currentTarget.value)}
					/>
					<p class="mt-0.5 text-[10px] text-ink/40">{ASCII_HINT}</p>
				</div>

				<!-- Sub-caste (optional) -->
				<div class="sm:col-span-2">
					<BilingualLabel key="subCaste" for="sub_caste" />
					<input
						id="sub_caste"
						type="text"
						class="input"
						bind:value={sub_caste}
						oninput={(e) => sub_caste = asciiOnly(e.currentTarget.value)}
						placeholder="Optional"
					/>
					<p class="mt-0.5 text-[10px] text-ink/40">{ASCII_HINT}</p>
				</div>
			</div>
		</div>
	</details>

	<!-- ── Section: Physical ─────────────────────────────────────────────────── -->
	<details open class="card">
		<summary class="cursor-pointer font-serif text-xl font-semibold text-maroon mb-1 list-none flex items-center gap-2">
			<span class="text-tangerine">▸</span>
			Physical
			<span class="text-sm font-normal text-ink/50 ml-1" lang="te">శారీరక వివరాలు</span>
		</summary>

		<div class="mt-4 grid gap-4 sm:grid-cols-2">
			<!-- Height -->
			<div class="sm:col-span-2">
				<BilingualLabel key="height" for="height_cm" />
				<p class="text-sm text-ink/60 mb-1">{cmToFtIn(height_cm)}</p>
				<input id="height_cm" type="range" min="120" max="220" step="1" bind:value={height_cm} class="w-full accent-maroon" />
				<div class="flex justify-between text-xs text-ink/40 mt-1">
					<span>3'11"</span><span>7'3"</span>
				</div>
			</div>

			<!-- Weight (optional) -->
			<div>
				<BilingualLabel key="weight" for="weight_kg" />
				<input
					id="weight_kg"
					type="number"
					min="30"
					max="200"
					class="input"
					bind:value={weight_kg}
					placeholder="Optional"
				/>
			</div>

			<!-- Complexion -->
			<div>
				<BilingualLabel key="complexion" for="complexion" />
				<select id="complexion" class="input" bind:value={complexion}>
					<option value="">Select…</option>
					{#each COMPLEXIONS as c}
						<option value={c.value}>{c.label}</option>
					{/each}
				</select>
			</div>

			<!-- Body Type (optional) -->
			<div>
				<BilingualLabel key="bodyType" for="body_type" />
				<select id="body_type" class="input" bind:value={body_type}>
					<option value="">Select… (optional)</option>
					{#each BODY_TYPES as bt}
						<option value={bt.value}>{bt.label}</option>
					{/each}
				</select>
			</div>

			<!-- Blood Group (optional) -->
			<div>
				<BilingualLabel key="bloodGroup" for="blood_group" />
				<select id="blood_group" class="input" bind:value={blood_group}>
					<option value="">Select… (optional)</option>
					{#each BLOOD_GROUPS as bg}
						<option value={bg}>{bg === 'unknown' ? 'Unknown' : bg}</option>
					{/each}
				</select>
			</div>
		</div>
	</details>

	<!-- ── Section: Astrology ────────────────────────────────────────────────── -->
	<details open class="card">
		<summary class="cursor-pointer font-serif text-xl font-semibold text-maroon mb-1 list-none flex items-center gap-2">
			<span class="text-tangerine">▸</span>
			Astrology
			<span class="text-sm font-normal text-ink/50 ml-1" lang="te">జ్యోతిష వివరాలు</span>
		</summary>

		<div class="mt-4 grid gap-4 sm:grid-cols-2">
			<!-- Gotra -->
			<div>
				<BilingualLabel key="gotra" for="gotra" required />
				<input
					id="gotra"
					type="text"
					class="input"
					class:border-vermilion={errors.gotra}
					bind:value={gotra}
					oninput={(e) => gotra = asciiOnly(e.currentTarget.value)}
				/>
				<p class="mt-0.5 text-[10px] text-ink/40">{ASCII_HINT}</p>
				{#if errors.gotra}<p class="mt-1 text-xs text-vermilion">{errors.gotra}</p>{/if}
			</div>

			<!-- Kuldevata -->
			<div>
				<BilingualLabel key="kuldevata" for="kuldevata" />
				<input
					id="kuldevata"
					type="text"
					class="input"
					bind:value={kuldevata}
					oninput={(e) => kuldevata = asciiOnly(e.currentTarget.value)}
				/>
				<p class="mt-0.5 text-[10px] text-ink/40">{ASCII_HINT}</p>
			</div>

			<!-- Devak -->
			<div>
				<BilingualLabel key="devak" for="devak" />
				<input
					id="devak"
					type="text"
					class="input"
					bind:value={devak}
					oninput={(e) => devak = asciiOnly(e.currentTarget.value)}
				/>
				<p class="mt-0.5 text-[10px] text-ink/40">{ASCII_HINT}</p>
			</div>

			<!-- Nakshatram -->
			<div>
				<BilingualLabel key="nakshatram" for="nakshatram" required />
				<select
					id="nakshatram"
					class="input"
					class:border-vermilion={errors.nakshatram}
					bind:value={nakshatram}
				>
					<option value="">Select…</option>
					{#each NAKSHATRAS as n}
						<option value={n}>{n}</option>
					{/each}
				</select>
				{#if errors.nakshatram}<p class="mt-1 text-xs text-vermilion">{errors.nakshatram}</p>{/if}
			</div>

			<!-- Rashi -->
			<div>
				<BilingualLabel key="rashi" for="rashi" required />
				<select
					id="rashi"
					class="input"
					class:border-vermilion={errors.rashi}
					bind:value={rashi}
				>
					<option value="">Select…</option>
					{#each RASHIS as r}
						<option value={r}>{r}</option>
					{/each}
				</select>
				{#if errors.rashi}<p class="mt-1 text-xs text-vermilion">{errors.rashi}</p>{/if}
			</div>

			<!-- Time of Birth (optional) -->
			<div>
				<BilingualLabel key="timeOfBirth" for="time_of_birth" />
				<input
					id="time_of_birth"
					type="time"
					class="input"
					bind:value={time_of_birth}
				/>
			</div>

			<!-- Place of Birth (optional) -->
			<div>
				<BilingualLabel key="placeOfBirth" for="place_of_birth" />
				<input
					id="place_of_birth"
					type="text"
					class="input"
					bind:value={place_of_birth}
					oninput={(e) => place_of_birth = asciiOnly(e.currentTarget.value)}
					placeholder="Optional"
				/>
				<p class="mt-0.5 text-[10px] text-ink/40">{ASCII_HINT}</p>
			</div>
		</div>

		<!-- Manglik -->
		<fieldset class="mt-4">
			<legend class="label">
				<span class="block">{T.manglik.en}</span>
				<span class="block text-xs text-ink/60 font-normal leading-tight" lang="te">{T.manglik.te}</span>
			</legend>
			<div class="flex gap-4 mt-1 flex-wrap">
				{#each [{ value: 'yes', label: 'Yes' }, { value: 'no', label: 'No' }, { value: 'partial', label: 'Partial' }, { value: 'unknown', label: "Unknown / Don't Know" }] as opt}
					<label class="flex items-center gap-2 cursor-pointer">
						<input type="radio" name="manglik" value={opt.value} bind:group={manglik} class="accent-maroon" />
						<span>{opt.label}</span>
					</label>
				{/each}
			</div>
		</fieldset>
	</details>

	<!-- ── Section: Education & Career ──────────────────────────────────────── -->
	<details open class="card">
		<summary class="cursor-pointer font-serif text-xl font-semibold text-maroon mb-1 list-none flex items-center gap-2">
			<span class="text-tangerine">▸</span>
			Education &amp; Career
			<span class="text-sm font-normal text-ink/50 ml-1" lang="te">విద్య &amp; వృత్తి</span>
		</summary>

		<div class="mt-4 grid gap-4 sm:grid-cols-2">
			<!-- Education -->
			<div>
				<BilingualLabel key="education" for="education" required />
				<input
					id="education"
					type="text"
					class="input"
					class:border-vermilion={errors.education}
					bind:value={education}
					oninput={(e) => education = asciiOnly(e.currentTarget.value)}
					placeholder="e.g. B.Tech, M.Sc"
				/>
				<p class="mt-0.5 text-[10px] text-ink/40">{ASCII_HINT}</p>
				{#if errors.education}<p class="mt-1 text-xs text-vermilion">{errors.education}</p>{/if}
			</div>

			<!-- College / University (optional) -->
			<div>
				<BilingualLabel key="collegeUniversity" for="college_university" />
				<input
					id="college_university"
					type="text"
					class="input"
					bind:value={college_university}
					oninput={(e) => college_university = asciiOnly(e.currentTarget.value)}
					placeholder="Optional"
				/>
				<p class="mt-0.5 text-[10px] text-ink/40">{ASCII_HINT}</p>
			</div>

			<!-- Occupation -->
			<div>
				<BilingualLabel key="occupation" for="occupation" required />
				<input
					id="occupation"
					type="text"
					class="input"
					class:border-vermilion={errors.occupation}
					bind:value={occupation}
					oninput={(e) => occupation = asciiOnly(e.currentTarget.value)}
					placeholder="e.g. Software Engineer"
				/>
				<p class="mt-0.5 text-[10px] text-ink/40">{ASCII_HINT}</p>
				{#if errors.occupation}<p class="mt-1 text-xs text-vermilion">{errors.occupation}</p>{/if}
			</div>

			<!-- Employer (optional) -->
			<div>
				<BilingualLabel key="employer" for="employer" />
				<input
					id="employer"
					type="text"
					class="input"
					bind:value={employer}
					oninput={(e) => employer = asciiOnly(e.currentTarget.value)}
					placeholder="Optional"
				/>
				<p class="mt-0.5 text-[10px] text-ink/40">{ASCII_HINT}</p>
			</div>

			<!-- Annual Income (optional) -->
			<div>
				<BilingualLabel key="income" for="annual_income" />
				<input
					id="annual_income"
					type="number"
					min="0"
					step="10000"
					class="input"
					bind:value={annual_income_inr}
					placeholder="Optional, e.g. 800000"
				/>
			</div>

			<!-- Work Location (optional) -->
			<div>
				<BilingualLabel key="workLocation" for="work_location" />
				<input
					id="work_location"
					type="text"
					class="input"
					bind:value={work_location}
					oninput={(e) => work_location = asciiOnly(e.currentTarget.value)}
					placeholder="Optional"
				/>
				<p class="mt-0.5 text-[10px] text-ink/40">{ASCII_HINT}</p>
			</div>
		</div>
	</details>

	<!-- ── Section: Family ───────────────────────────────────────────────────── -->
	<details class="card">
		<summary class="cursor-pointer font-serif text-xl font-semibold text-maroon mb-1 list-none flex items-center gap-2">
			<span class="text-tangerine">▸</span>
			Family
			<span class="text-sm font-normal text-ink/50 ml-1" lang="te">కుటుంబ వివరాలు</span>
		</summary>

		<div class="mt-4 grid gap-4 sm:grid-cols-2">
			<!-- Father Name -->
			<div>
				<BilingualLabel key="fatherName" for="father_name" />
				<input
					id="father_name"
					type="text"
					maxlength="100"
					class="input"
					bind:value={father_name}
					oninput={(e) => father_name = e.currentTarget.value}
					placeholder="Father's full name"
				/>
			</div>

			<!-- Mother Name -->
			<div>
				<BilingualLabel key="motherName" for="mother_name" />
				<input
					id="mother_name"
					type="text"
					maxlength="100"
					class="input"
					bind:value={mother_name}
					oninput={(e) => mother_name = e.currentTarget.value}
					placeholder="Mother's full name"
				/>
			</div>

			<!-- Father's Occupation -->
			<div>
				<BilingualLabel key="fatherOccupation" for="father_occupation" />
				<input
					id="father_occupation"
					type="text"
					class="input"
					bind:value={father_occupation}
					oninput={(e) => father_occupation = asciiOnly(e.currentTarget.value)}
					placeholder="Optional"
				/>
				<p class="mt-0.5 text-[10px] text-ink/40">{ASCII_HINT}</p>
			</div>

			<!-- Mother's Occupation -->
			<div>
				<BilingualLabel key="motherOccupation" for="mother_occupation" />
				<input
					id="mother_occupation"
					type="text"
					class="input"
					bind:value={mother_occupation}
					oninput={(e) => mother_occupation = asciiOnly(e.currentTarget.value)}
					placeholder="Optional"
				/>
				<p class="mt-0.5 text-[10px] text-ink/40">{ASCII_HINT}</p>
			</div>

			<!-- Number of Brothers -->
			<div>
				<BilingualLabel key="numBrothers" for="num_brothers" />
				<input
					id="num_brothers"
					type="number"
					min="0"
					max="20"
					class="input"
					bind:value={num_brothers}
					placeholder="Optional"
				/>
			</div>

			<!-- Brothers Married -->
			<div>
				<BilingualLabel key="numBrothersMarried" for="num_brothers_married" />
				<input
					id="num_brothers_married"
					type="number"
					min="0"
					max="20"
					class="input"
					bind:value={num_brothers_married}
					placeholder="Optional"
				/>
			</div>

			<!-- Number of Sisters -->
			<div>
				<BilingualLabel key="numSisters" for="num_sisters" />
				<input
					id="num_sisters"
					type="number"
					min="0"
					max="20"
					class="input"
					bind:value={num_sisters}
					placeholder="Optional"
				/>
			</div>

			<!-- Sisters Married -->
			<div>
				<BilingualLabel key="numSistersMarried" for="num_sisters_married" />
				<input
					id="num_sisters_married"
					type="number"
					min="0"
					max="20"
					class="input"
					bind:value={num_sisters_married}
					placeholder="Optional"
				/>
			</div>

			<!-- Number of family members -->
			<div>
				<BilingualLabel key="numFamilyMembers" for="num_family_members" />
				<input
					id="num_family_members"
					type="number"
					min="1"
					max="30"
					class="input"
					bind:value={num_family_members}
					placeholder="Total members in family"
				/>
			</div>

			<!-- Family Status -->
			<div>
				<BilingualLabel key="familyStatus" for="family_status" />
				<select id="family_status" class="input" bind:value={family_status}>
					<option value="">Select… (optional)</option>
					{#each FAMILY_STATUSES as fs}
						<option value={fs.value}>{fs.label}</option>
					{/each}
				</select>
			</div>

			<!-- Family Values -->
			<div>
				<BilingualLabel key="familyValues" for="family_values" />
				<select id="family_values" class="input" bind:value={family_values}>
					<option value="">Select… (optional)</option>
					{#each FAMILY_VALUES_OPTS as fv}
						<option value={fv.value}>{fv.label}</option>
					{/each}
				</select>
			</div>

			<!-- Native Place (optional) -->
			<div class="sm:col-span-2">
				<BilingualLabel key="nativePlace" for="native_place" />
				<input
					id="native_place"
					type="text"
					class="input"
					bind:value={native_place}
					oninput={(e) => native_place = asciiOnly(e.currentTarget.value)}
					placeholder="Optional — village/town of origin"
				/>
				<p class="mt-0.5 text-[10px] text-ink/40">{ASCII_HINT}</p>
			</div>
		</div>

		<!-- Family Type -->
		<fieldset class="mt-4">
			<legend class="label">
				<span class="block">{T.familyType.en}</span>
				<span class="block text-xs text-ink/60 font-normal leading-tight" lang="te">{T.familyType.te}</span>
			</legend>
			<div class="flex gap-6 mt-1 flex-wrap">
				{#each [{ value: '', label: 'Not specified' }, { value: 'nuclear', label: 'Nuclear' }, { value: 'joint', label: 'Joint' }] as opt}
					<label class="flex items-center gap-2 cursor-pointer">
						<input type="radio" name="family_type" value={opt.value} bind:group={family_type} class="accent-maroon" />
						<span>{opt.label}</span>
					</label>
				{/each}
			</div>
		</fieldset>
	</details>

	<!-- ── Section: Lifestyle ────────────────────────────────────────────────── -->
	<details open class="card">
		<summary class="cursor-pointer font-serif text-xl font-semibold text-maroon mb-1 list-none flex items-center gap-2">
			<span class="text-tangerine">▸</span>
			Lifestyle
			<span class="text-sm font-normal text-ink/50 ml-1" lang="te">జీవనశైలి</span>
		</summary>

		<div class="mt-4 space-y-4">
			<!-- Diet -->
			<fieldset>
				<legend class="label">
					<span class="block">{T.diet.en} <span class="text-vermilion">*</span></span>
					<span class="block text-xs text-ink/60 font-normal leading-tight" lang="te">{T.diet.te}</span>
				</legend>
				<div class="flex gap-4 mt-1 flex-wrap">
					{#each [{ value: 'veg', label: 'Vegetarian' }, { value: 'non-veg', label: 'Non-Vegetarian' }, { value: 'eggetarian', label: 'Eggetarian' }, { value: 'jain', label: 'Jain' }, { value: 'vegan', label: 'Vegan' }] as opt}
						<label class="flex items-center gap-2 cursor-pointer">
							<input type="radio" name="diet" value={opt.value} bind:group={diet} class="accent-maroon" />
							<span>{opt.label}</span>
						</label>
					{/each}
				</div>
			</fieldset>

			<!-- Smokes -->
			<fieldset>
				<legend class="label">
					<span class="block">{T.smokes.en}</span>
					<span class="block text-xs text-ink/60 font-normal leading-tight" lang="te">{T.smokes.te}</span>
				</legend>
				<div class="flex gap-4 mt-1 flex-wrap">
					{#each [{ value: '', label: 'Prefer not to say' }, { value: 'no', label: 'No' }, { value: 'occasionally', label: 'Occasionally' }, { value: 'yes', label: 'Yes' }] as opt}
						<label class="flex items-center gap-2 cursor-pointer">
							<input type="radio" name="smokes" value={opt.value} bind:group={smokes} class="accent-maroon" />
							<span>{opt.label}</span>
						</label>
					{/each}
				</div>
			</fieldset>

			<!-- Drinks -->
			<fieldset>
				<legend class="label">
					<span class="block">{T.drinks.en}</span>
					<span class="block text-xs text-ink/60 font-normal leading-tight" lang="te">{T.drinks.te}</span>
				</legend>
				<div class="flex gap-4 mt-1 flex-wrap">
					{#each [{ value: '', label: 'Prefer not to say' }, { value: 'no', label: 'No' }, { value: 'occasionally', label: 'Occasionally' }, { value: 'yes', label: 'Yes' }] as opt}
						<label class="flex items-center gap-2 cursor-pointer">
							<input type="radio" name="drinks" value={opt.value} bind:group={drinks} class="accent-maroon" />
							<span>{opt.label}</span>
						</label>
					{/each}
				</div>
			</fieldset>

			<!-- Hobbies (optional textarea) -->
			<div>
				<BilingualLabel key="hobbies" for="hobbies" />
				<textarea
					id="hobbies"
					class="input min-h-[80px] resize-y"
					bind:value={hobbies}
					oninput={(e) => hobbies = asciiOnly(e.currentTarget.value)}
					placeholder="Optional — e.g. Reading, Cricket, Cooking"
				></textarea>
				<p class="mt-0.5 text-[10px] text-ink/40">{ASCII_HINT}</p>
			</div>
		</div>
	</details>

	<!-- ── Section: Location ─────────────────────────────────────────────────── -->
	<details open class="card">
		<summary class="cursor-pointer font-serif text-xl font-semibold text-maroon mb-1 list-none flex items-center gap-2">
			<span class="text-tangerine">▸</span>
			Location
			<span class="text-sm font-normal text-ink/50 ml-1" lang="te">నివాస వివరాలు</span>
		</summary>

		<div class="mt-4 grid gap-4 sm:grid-cols-2">
			<!-- City -->
			<div>
				<BilingualLabel key="city" for="city" required />
				<input
					id="city"
					type="text"
					class="input"
					class:border-vermilion={errors.city}
					bind:value={city}
					oninput={(e) => city = asciiOnly(e.currentTarget.value)}
				/>
				<p class="mt-0.5 text-[10px] text-ink/40">{ASCII_HINT}</p>
				{#if errors.city}<p class="mt-1 text-xs text-vermilion">{errors.city}</p>{/if}
			</div>

			<!-- State -->
			<div>
				<BilingualLabel key="state" for="state" />
				<select id="state" class="input" bind:value={state_field}>
					{#each INDIA_STATES as s}
						<option value={s}>{s}</option>
					{/each}
				</select>
			</div>

			<!-- Pin Code (optional) -->
			<div>
				<label for="pin_code" class="label">
					<span class="block">Pin Code <span class="text-ink/50 font-normal text-xs">(optional)</span></span>
					<span class="block text-xs font-normal leading-tight" lang="te">పిన్ కోడ్</span>
				</label>
				<input
					id="pin_code"
					type="text"
					inputmode="numeric"
					maxlength="10"
					class="input"
					bind:value={pin_code}
					placeholder="e.g. 500001"
				/>
			</div>

			<!-- Country -->
			<div>
				<BilingualLabel key="country" for="country" />
				<input
					id="country"
					type="text"
					class="input"
					bind:value={country}
					oninput={(e) => country = asciiOnly(e.currentTarget.value)}
					placeholder="India"
				/>
				<p class="mt-0.5 text-[10px] text-ink/40">{ASCII_HINT}</p>
			</div>
		</div>
	</details>

	<!-- ── Section: About ───────────────────────────────────────────────────── -->
	<details open class="card">
		<summary class="cursor-pointer font-serif text-xl font-semibold text-maroon mb-1 list-none flex items-center gap-2">
			<span class="text-tangerine">▸</span>
			About &amp; Expectations
			<span class="text-sm font-normal text-ink/50 ml-1" lang="te">మీ గురించి &amp; అపేక్షలు</span>
		</summary>

		<div class="mt-4 space-y-4">
			<!-- About Yourself -->
			<div>
				<BilingualLabel key="about" for="about" />
				<textarea
					id="about"
					class="input min-h-[120px] resize-y"
					class:border-vermilion={errors.about}
					bind:value={about}
					oninput={(e) => about = asciiOnly(e.currentTarget.value)}
					maxlength={500}
					placeholder="A short description about yourself, your family, and interests…"
				></textarea>
				<div class="flex justify-between mt-1">
					{#if errors.about}
						<p class="text-xs text-vermilion">{errors.about}</p>
					{:else}
						<p class="text-[10px] text-ink/40">{ASCII_HINT}</p>
					{/if}
					<p class="text-xs text-ink/40">{about.length}/500</p>
				</div>
			</div>

			<!-- Partner Expectations -->
			<div>
				<BilingualLabel key="partnerExpectations" for="expectations" />
				<p class="text-xs text-ink/50 mb-1">
					Mention preferred age, education, location, family values, etc. The system will extract keywords from this for matching.
				</p>
				<textarea
					id="expectations"
					class="input min-h-[140px] resize-y"
					class:border-vermilion={errors.partner_expectations}
					bind:value={partner_expectations}
					oninput={(e) => partner_expectations = asciiOnly(e.currentTarget.value)}
					maxlength={800}
					placeholder="Describe what you're looking for in a partner…"
				></textarea>
				<div class="flex justify-between mt-1">
					{#if errors.partner_expectations}
						<p class="text-xs text-vermilion">{errors.partner_expectations}</p>
					{:else}
						<p class="text-[10px] text-ink/40">{ASCII_HINT}</p>
					{/if}
					<p class="text-xs text-ink/40">{partner_expectations.length}/800</p>
				</div>
			</div>
		</div>
	</details>

	<!-- ── Submit ────────────────────────────────────────────────────────────── -->
	<div class="flex justify-end gap-3 pb-8">
		<a href="/dashboard" class="btn-secondary">
			{T.cancel.en} · <span lang="te">{T.cancel.te}</span>
		</a>
		<button type="submit" class="btn-primary px-8" disabled={submitting}>
			{#if submitting}
				Saving…
			{:else}
				{T.save.en} · <span lang="te">{T.save.te}</span>
			{/if}
		</button>
	</div>
</form>
