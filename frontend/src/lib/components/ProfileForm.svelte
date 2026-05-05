<script lang="ts">
	import { untrack, onMount } from 'svelte';
	import type {
		Profile,
		ProfilePayload,
		MaritalStatus,
		BodyType,
		BloodGroup,
		FamilyType,
		FamilyStatus,
		FamilyValues,
		SmokeDrink
	} from '$lib/api';
	import { T, tx } from '$lib/i18n';
	import { langStore } from '$lib/stores/lang.svelte';
	import { asciiOnly } from '$lib/inputFilters';
	import BilingualLabel from '$lib/components/BilingualLabel.svelte';
	import PhotoUpload from '$lib/components/PhotoUpload.svelte';
	import Combobox from '$lib/components/Combobox.svelte';
	import DobInput from '$lib/components/DobInput.svelte';
	import { CASTE_OPTIONS, MARATHA_SUB_CASTES, MOTHER_TONGUES, INDIA_STATES, COUNTRIES_PRIORITY, COUNTRIES_OTHER, DIET_OPTIONS } from '$lib/profileOptions';

	const COUNTRIES = [...COUNTRIES_PRIORITY, ...COUNTRIES_OTHER];

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
		serverErrors = {},
		onSubmitForApproval = undefined,
		submittingForApproval = false,
		profileStatus = '',
		photoCount = undefined,
		autoSave = false,
		wizardMode = false,
		profileId = undefined,
		isProd = true
	}: {
		initialData?: Partial<Profile>;
		onSubmit: (data: Partial<ProfilePayload>) => void | Promise<void>;
		submitting?: boolean;
		serverErrors?: Record<string, string>;
		onSubmitForApproval?: (() => void) | undefined;
		submittingForApproval?: boolean;
		profileStatus?: string;
		photoCount?: number;
		autoSave?: boolean;
		wizardMode?: boolean;
		profileId?: string;
		isProd?: boolean;
	} = $props();

	// ── Form state — seeded once from initialData ─────────────────────────────
	// Basic Information
	let gender = $state<'bride' | 'groom'>(untrack(() => initialData.gender ?? 'bride'));
	let first_name = $state(untrack(() => initialData.first_name ?? ''));
	let last_name = $state(untrack(() => initialData.last_name ?? ''));
	let dob = $state(untrack(() => initialData.dob ?? ''));
	let marital_status = $state(untrack(() => initialData.marital_status ?? ''));
	let mother_tongue = $state(untrack(() => initialData.mother_tongue ?? 'Telugu'));
	let caste = $state(untrack(() => initialData.caste ?? 'Maratha'));
	let sub_caste = $state(untrack(() => initialData.sub_caste ?? 'Maratha'));
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
	let manglik = $state<'yes' | 'no' | 'partial' | 'unknown'>(
		untrack(() => initialData.manglik ?? 'unknown')
	);
	// 12-hour time picker state — backend stores HH:MM (24-hour)
	function parseTimeTo12h(t: string | null | undefined): { hour: string; minute: string; ampm: 'AM' | 'PM' } {
		if (!t) return { hour: '12', minute: '00', ampm: 'AM' };
		const [hStr, mStr] = t.split(':');
		let h = parseInt(hStr, 10);
		const ampm: 'AM' | 'PM' = h < 12 ? 'AM' : 'PM';
		if (h === 0) h = 12;
		else if (h > 12) h = h - 12;
		return { hour: String(h), minute: mStr?.slice(0, 2) ?? '00', ampm };
	}
	let timeEnabled = $state(untrack(() => !!initialData.time_of_birth));
	const _initTime = untrack(() => parseTimeTo12h(initialData.time_of_birth));
	let time_hour = $state(_initTime.hour);
	let time_minute = $state(_initTime.minute);
	let time_ampm = $state<'AM' | 'PM'>(_initTime.ampm);
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
	let num_brothers_married = $state<number | ''>(
		untrack(() => initialData.num_brothers_married ?? '')
	);
	let num_sisters_married = $state<number | ''>(
		untrack(() => initialData.num_sisters_married ?? '')
	);
	let family_type = $state(untrack(() => initialData.family_type ?? ''));
	let family_status = $state(untrack(() => initialData.family_status ?? ''));
	let family_values = $state(untrack(() => initialData.family_values ?? ''));
	let native_place = $state(untrack(() => initialData.native_place ?? ''));

	// Lifestyle
	let diet = $state<'veg' | 'non-veg' | 'eggetarian' | 'jain' | 'vegan'>(
		untrack(() => initialData.diet ?? 'veg')
	);
	let smokes = $state(untrack(() => initialData.smokes ?? ''));
	let drinks = $state(untrack(() => initialData.drinks ?? ''));
	let hobbies = $state(untrack(() => initialData.hobbies ?? ''));

	// Location
	let city = $state(untrack(() => initialData.city ?? ''));
	let state_field = $state(untrack(() => initialData.state ?? ''));
	let country = $state(untrack(() => initialData.country ?? 'India'));
	let pin_code = $state(untrack(() => initialData.pin_code ?? ''));

	// About
	let about = $state(untrack(() => initialData.about ?? ''));
	let partner_expectations = $state(untrack(() => initialData.partner_expectations ?? ''));

	let errors = $state<Record<string, string>>({});

	// ── Wizard state ─────────────────────────────────────────────────────────
	const SECTION_KEYS = [
		'secBasicInfo', 'secPhysical', 'secAstrology', 'secEducation',
		'secFamily', 'secLifestyle', 'secLocation', 'secAbout', 'secPhotos'
	] as const;
	// Keep a stable label for aria / locking logic
	const SECTIONS = SECTION_KEYS.map((k) => T[k]);

	// activeSection: which section is expanded. Starts at 0.
	let activeSection = $state(0);
	// completedSections: set of section indices that have been saved
	let completedSections = $state(new Set<number>());
	// wizardPhotoCount tracked internally for photo section validation
	let wizardPhotoCount = $state(0);

	function isSectionLocked(n: number): boolean {
		if (n === 0) return false;
		return !completedSections.has(n - 1);
	}

	// Per-section mandatory field check — drives Save button enabled/disabled
	function isSectionValid(n: number): boolean {
		switch (n) {
			case 0: return !!first_name.trim() && !!surname_clan.trim() && !!dob;
			case 1: return true; // height has a default
			case 2: return true; // all astrology fields are optional
			case 3: return !!education.trim() && !!occupation.trim();
			case 4: return !!father_name.trim() && !!mother_name.trim();
			case 5: return true; // diet has a default
			case 6: return !!city.trim();
			case 7: return true; // about is optional
			case 8: return wizardPhotoCount > 0;
			default: return true;
		}
	}

	function saveSection(n: number) {
		if (!isSectionValid(n)) return;
		onSubmit(buildData()); // fire-and-forget — parent creates/updates profile
		completedSections = new Set([...completedSections, n]);
		if (n < SECTIONS.length - 1) {
			activeSection = n + 1;
			setTimeout(() => {
				document.getElementById(`wsec-${n + 1}`)?.scrollIntoView({ behavior: 'smooth', block: 'start' });
			}, 80);
		}
	}

	function toggleSection(n: number) {
		if (isSectionLocked(n)) return;
		activeSection = activeSection === n ? -1 : n;
	}

	// ── Static lookup data ───────────────────────────────────────────────────
	const NAKSHATRAS = [
		'Ashwini',
		'Bharani',
		'Krittika',
		'Rohini',
		'Mrigashirsha',
		'Ardra',
		'Punarvasu',
		'Pushya',
		'Ashlesha',
		'Magha',
		'Purva Phalguni',
		'Uttara Phalguni',
		'Hasta',
		'Chitra',
		'Swati',
		'Vishakha',
		'Anuradha',
		'Jyeshtha',
		'Mula',
		'Purva Ashadha',
		'Uttara Ashadha',
		'Shravana',
		'Dhanishtha',
		'Shatabhisha',
		'Purva Bhadrapada',
		'Uttara Bhadrapada',
		'Revati'
	];

	const RASHIS = [
		'Mesha (Aries)',
		'Vrishabha (Taurus)',
		'Mithuna (Gemini)',
		'Karka (Cancer)',
		'Simha (Leo)',
		'Kanya (Virgo)',
		'Tula (Libra)',
		'Vrishchika (Scorpio)',
		'Dhanu (Sagittarius)',
		'Makara (Capricorn)',
		'Kumbha (Aquarius)',
		'Meena (Pisces)'
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

	// Blood groups as {value,label} so 'unknown' renders as 'Unknown'
	const BLOOD_GROUPS_OPTS = BLOOD_GROUPS.map(bg => ({
		value: bg,
		label: bg === 'unknown' ? 'Unknown' : bg
	}));

	const FAMILY_TYPES = [
		{ value: '', label: 'Not specified' },
		{ value: 'nuclear', label: 'Nuclear' },
		{ value: 'joint', label: 'Joint' }
	];

	const DIET_OPTS = [
		{ value: 'veg', label: 'Vegetarian' },
		{ value: 'non-veg', label: 'Non-Vegetarian' },
		{ value: 'eggetarian', label: 'Eggetarian' },
		{ value: 'jain', label: 'Jain' },
		{ value: 'vegan', label: 'Vegan' }
	];

	const SMOKE_DRINK_OPTS = [
		{ value: '', label: 'Prefer not to say' },
		{ value: 'no', label: 'No' },
		{ value: 'occasionally', label: 'Occasionally' },
		{ value: 'yes', label: 'Yes' }
	];

	const TIME_HOURS = Array.from({ length: 12 }, (_, i) => String(i + 1));
	const TIME_MINUTES = ['00', '05', '10', '15', '20', '25', '30', '35', '40', '45', '50', '55'];
	const TIME_AMPM = ['AM', 'PM'];

	// Small hint shown under every ASCII-only text field
	const ASCII_HINT = $derived(`English characters only · ${tx('hintAsciiOnly', langStore.current)}`);

	// ── Validation ───────────────────────────────────────────────────────────
	function validateSave(): boolean {
		const e: Record<string, string> = {};
		if (!first_name.trim()) e.first_name = 'Required';
		if (!surname_clan.trim()) e.surname_clan = 'Required';
		if (!dob) e.dob = 'Date of birth is required';
		else {
			const age = new Date().getFullYear() - new Date(dob).getFullYear();
			if (age < 18) e.dob = 'Must be at least 18 years old';
		}
		if (about.length > 500) e.about = 'Max 500 characters';
		if (partner_expectations.length > 800) e.partner_expectations = 'Max 800 characters';
		errors = e;
		return Object.keys(e).length === 0;
	}

	function validateSubmit(): boolean {
		const e: Record<string, string> = {};
		// Basic — always required
		if (!first_name.trim()) e.first_name = 'Required';
		if (!dob) e.dob = 'Required';
		else {
			const age = new Date().getFullYear() - new Date(dob).getFullYear();
			if (age < 18) e.dob = 'Must be at least 18 years old';
		}
		if (isProd) {
			// Full validation — production mode
			if (!marital_status) e.marital_status = 'Required';
			if (!surname_clan.trim()) e.surname_clan = 'Required';
			// Education & Career
			if (!education.trim()) e.education = 'Required';
			if (!occupation.trim()) e.occupation = 'Required';
			// Family
			if (!father_name.trim()) e.father_name = 'Required for submission';
			if (!mother_name.trim()) e.mother_name = 'Required for submission';
			if (!family_type) e.family_type = 'Required';
			if (!native_place.trim()) e.native_place = 'Required';
			// Location
			if (!city.trim()) e.city = 'Required';
			// About
			if (!about.trim()) e.about = 'Required';
		}
		if (about.length > 500) e.about = 'Max 500 characters';
		if (partner_expectations.length > 800) e.partner_expectations = 'Max 800 characters';
		// Photo — use wizardPhotoCount when in wizard mode, else photoCount prop
		if ((wizardMode ? wizardPhotoCount : (photoCount ?? 0)) === 0)
			e._photos = 'At least one photo is required before submitting';
		errors = e;
		return Object.keys(e).length === 0;
	}

	async function handleSubmitForApproval() {
		if (!validateSubmit()) {
			// Scroll to first error field
			setTimeout(() => {
				const el = document.querySelector('[data-error]') as HTMLElement | null;
				el?.scrollIntoView({ behavior: 'smooth', block: 'center' });
			}, 50);
			return;
		}
		// Persist current form state before transitioning to pending — otherwise
		// fields the user typed but never explicitly saved (e.g., wizard sections
		// they scrolled past without clicking Save & Continue) would be discarded.
		await onSubmit(buildData());
		onSubmitForApproval?.();
	}

	function buildData(): Partial<ProfilePayload> {
		return {
			gender,
			first_name: first_name.trim(),
			last_name: last_name.trim(),
			dob,
			marital_status: (marital_status || null) as MaritalStatus | null,
			mother_tongue: mother_tongue.trim(),
			caste: caste.trim() || null,
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
			time_of_birth: (() => {
				if (!timeEnabled) return null;
				let h = parseInt(time_hour, 10);
				if (time_ampm === 'AM' && h === 12) h = 0;
				else if (time_ampm === 'PM' && h !== 12) h = h + 12;
				return `${String(h).padStart(2, '0')}:${time_minute}`;
			})(),
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
	}

	function handleSubmit(e: Event) {
		e.preventDefault();
		// In wizard mode Enter-key should advance the active section, not bypass wizard logic
		if (wizardMode) {
			saveSection(activeSection);
			return;
		}
		if (!validateSave()) return;
		onSubmit(buildData());
	}

	// ── Auto-save ────────────────────────────────────────────────────────────
	let autoSaveMounted = $state(false);
	let autoSaveStatus = $state<'idle' | 'pending' | 'saving' | 'saved'>('idle');
	let autoSaveTimer: ReturnType<typeof setTimeout>;

	// prettier-ignore
	const formFingerprint = $derived(
		[
			gender, first_name, last_name, dob, marital_status, mother_tongue,
			caste, sub_caste, surname_clan, height_cm, weight_kg, complexion, body_type,
			blood_group, gotra, kuldevata, devak, nakshatram, rashi, manglik,
			time_hour, time_minute, time_ampm, timeEnabled, place_of_birth,
			education, college_university, occupation,
			employer, annual_income_inr, work_location, father_name, mother_name,
			num_family_members, father_occupation, mother_occupation, num_brothers,
			num_sisters, num_brothers_married, num_sisters_married, family_type,
			family_status, family_values, native_place, diet, smokes, drinks,
			hobbies, city, state_field, country, pin_code, about, partner_expectations
		].join('|')
	);

	$effect(() => {
		formFingerprint; // only fingerprint changes trigger auto-save
		if (untrack(() => !autoSaveMounted || !autoSave || submitting)) return;
		autoSaveStatus = 'pending';
		clearTimeout(autoSaveTimer);
		autoSaveTimer = setTimeout(() => {
			autoSaveStatus = 'saving';
			untrack(() => onSubmit(buildData()));
			setTimeout(() => {
				autoSaveStatus = 'saved';
				setTimeout(() => {
					autoSaveStatus = 'idle';
				}, 2000);
			}, 300);
		}, 2000);
	});

	onMount(() => {
		setTimeout(() => {
			autoSaveMounted = true;
		}, 100);
	});

	// Merge server errors into local errors
	$effect(() => {
		if (Object.keys(serverErrors).length > 0) {
			errors = { ...errors, ...serverErrors };
		}
	});


</script>

<form onsubmit={handleSubmit} novalidate class="space-y-6">

{#if wizardMode}
	<!-- ══════════════════════════════════════════════════════════════════════ -->
	<!-- WIZARD MODE — accordion, all sections visible, unlock sequentially   -->
	<!-- ══════════════════════════════════════════════════════════════════════ -->
<div class="space-y-3">
	{#each SECTIONS as sec, i}
		{@const locked = isSectionLocked(i)}
		{@const done = completedSections.has(i)}
		{@const open = activeSection === i && !locked}
		<div id="wsec-{i}" class="rounded-lg border {done ? 'border-gold/60 bg-saffron/5' : locked ? 'border-ink/10 bg-ink/3 opacity-60' : 'border-gold/40 bg-white'} overflow-hidden">
			<!-- Section header -->
			<button
				type="button"
				onclick={() => toggleSection(i)}
				disabled={locked}
				class="flex w-full items-center gap-3 px-4 py-3 text-left {locked ? 'cursor-not-allowed' : 'hover:bg-maroon/5'}"
			>
				<span class="inline-flex h-7 w-7 shrink-0 items-center justify-center rounded-full text-sm font-bold {done ? 'bg-maroon text-cream' : locked ? 'bg-ink/15 text-ink/40' : 'bg-maroon/10 text-maroon'}">{i + 1}</span>
				<span class="flex-1">
					<span class="font-serif font-semibold {locked ? 'text-ink/40' : 'text-maroon'}">{sec.en}</span>
					<span class="ml-2 text-xs text-ink/50" lang={langStore.current}>{tx(SECTION_KEYS[i], langStore.current)}</span>
				</span>
				{#if done}
					<span class="text-xs font-medium text-maroon">✓ Saved</span>
				{:else if locked}
					<span class="text-xs text-ink/35">Complete step {i} first</span>
				{:else if open}
					<span class="text-xs text-ink/50">▲</span>
				{:else}
					<span class="text-xs text-ink/50">▼</span>
				{/if}
			</button>

			<!-- Section content (only when open) -->
			{#if open}
				<div class="border-t border-gold/20 px-4 py-4">
					{#if i === 0}
						<!-- ── Section 0: Basic Information ────────────────────────── -->
						<div class="space-y-4">
							<!-- Gender -->
							<fieldset>
								<legend class="label">
									<span class="block">{T.gender.en} <span class="text-vermilion">*</span></span>
									<span class="block text-xs leading-tight font-normal text-ink/60" lang={langStore.current}>{tx('gender', langStore.current)}</span>
								</legend>
								<div class="mt-1 flex gap-6">
									{#each [{ value: 'bride', key: 'bride' as const }, { value: 'groom', key: 'groom' as const }] as opt}
										<label class="flex cursor-pointer items-center gap-2">
											<input type="radio" name="gender" value={opt.value} bind:group={gender} class="accent-maroon" />
											<span>{T[opt.key].en}</span>
											<span class="text-xs text-ink/60" lang={langStore.current}>{tx(opt.key, langStore.current)}</span>
										</label>
									{/each}
								</div>
							</fieldset>

							<div class="grid gap-4 sm:grid-cols-2">
								<!-- First Name -->
								<div>
									<BilingualLabel key="firstName" for="first_name" required />
									<input id="first_name" type="text" class="input" class:border-vermilion={errors.first_name} bind:value={first_name} oninput={(e) => (first_name = asciiOnly(e.currentTarget.value))} />
									<p class="mt-0.5 text-[10px] text-ink/40">{ASCII_HINT}</p>
									{#if errors.first_name}<p class="mt-1 text-xs text-vermilion" data-error="true">{errors.first_name}</p>{/if}
								</div>

								<!-- Surname / Clan (required) -->
								<div>
									<BilingualLabel key="surnameClan" for="surname_clan" required />
									<input id="surname_clan" type="text" class="input" class:border-vermilion={errors.surname_clan}
										bind:value={surname_clan}
										oninput={(e) => (surname_clan = asciiOnly(e.currentTarget.value))} />
									<p class="mt-0.5 text-xs text-ink/45">Your family/clan surname, e.g. Desai, Patil, More · <span lang={langStore.current}>{tx('hintSurnameClan', langStore.current)}</span></p>
									<p class="mt-0.5 text-[10px] text-ink/40">{ASCII_HINT}</p>
									{#if errors.surname_clan}<p class="mt-1 text-xs text-vermilion" data-error="true">{errors.surname_clan}</p>{/if}
								</div>

								<!-- Date of Birth -->
								<div>
									<BilingualLabel key="dob" for="dob" required />
									<DobInput id="dob" bind:value={dob} error={!!errors.dob} />
									{#if errors.dob}<p class="mt-1 text-xs text-vermilion" data-error="true">{errors.dob}</p>{/if}
								</div>

								<!-- Marital Status -->
								<div>
									<BilingualLabel key="maritalStatus" for="marital_status" />
									<Combobox
										id="marital_status"
										bind:value={marital_status}
										options={MARITAL_STATUSES}
										placeholder="Select…"
										class={errors.marital_status ? 'border-vermilion' : ''}
									/>
									{#if errors.marital_status}<p class="mt-1 text-xs text-vermilion" data-error="true">{errors.marital_status}</p>{/if}
								</div>

								<!-- Mother Tongue -->
								<div>
									<BilingualLabel key="motherTongue" for="mother_tongue_w" />
									<Combobox id="mother_tongue_w" bind:value={mother_tongue} options={MOTHER_TONGUES} placeholder="Select language" />
									<p class="mt-0.5 text-[10px] text-ink/40">{ASCII_HINT}</p>
								</div>

								<!-- Sub-caste (optional) -->
								<div class="sm:col-span-2">
									<BilingualLabel key="caste" for="caste" />
									<Combobox id="caste" bind:value={caste} options={CASTE_OPTIONS} allowCustom={true} placeholder="Select or type caste" />
									<p class="mt-0.5 text-xs text-ink/45">Pick from the list, or type your own if different · <span lang={langStore.current}>{tx('hintCastePickOrType', langStore.current)}</span></p>
								</div>

								<div>
									<BilingualLabel key="subCaste" for="sub_caste" />
									<Combobox id="sub_caste" bind:value={sub_caste} options={MARATHA_SUB_CASTES} allowCustom={true} placeholder="Select or type sub-caste" />
									<p class="mt-0.5 text-xs text-ink/45">Pick from the list, or type your own if different · <span lang={langStore.current}>{tx('hintCastePickOrType', langStore.current)}</span></p>
								</div>
							</div>
						</div>

					{:else if i === 1}
						<!-- ── Section 1: Physical ──────────────────────────────────── -->
						<div class="grid gap-4 sm:grid-cols-2">
							<!-- Height -->
							<div class="sm:col-span-2">
								<BilingualLabel key="height" for="height_cm" />
								<p class="mb-1 text-sm text-ink/60">{cmToFtIn(height_cm)}</p>
								<input id="height_cm" type="range" min="120" max="229" step="1" bind:value={height_cm} class="w-full accent-maroon" />
								<div class="mt-1 flex justify-between text-xs text-ink/40">
									<span>3'11"</span><span>7'6"</span>
								</div>
							</div>

							<!-- Weight (optional) -->
							<div>
								<BilingualLabel key="weight" for="weight_kg" />
								<input id="weight_kg" type="number" min="30" max="200" class="input" bind:value={weight_kg} placeholder="Optional" />
							</div>

							<!-- Complexion -->
							<div>
								<BilingualLabel key="complexion" for="complexion" />
								<Combobox id="complexion" bind:value={complexion} options={COMPLEXIONS} placeholder="Select…" />
							</div>

							<!-- Body Type (optional) -->
							<div>
								<BilingualLabel key="bodyType" for="body_type" />
								<Combobox id="body_type" bind:value={body_type} options={BODY_TYPES} placeholder="Select… (optional)" />
							</div>

							<!-- Blood Group (optional) -->
							<div>
								<BilingualLabel key="bloodGroup" for="blood_group" />
								<Combobox id="blood_group" bind:value={blood_group} options={BLOOD_GROUPS_OPTS} placeholder="Select… (optional)" />
							</div>
						</div>

					{:else if i === 2}
						<!-- ── Section 2: Astrology ─────────────────────────────────── -->
						<div class="grid gap-4 sm:grid-cols-2">
							<!-- Gotra -->
							<div>
								<BilingualLabel key="gotra" for="gotra" />
								<input id="gotra" type="text" class="input" class:border-vermilion={errors.gotra} bind:value={gotra} oninput={(e) => (gotra = asciiOnly(e.currentTarget.value))} />
								<p class="mt-0.5 text-xs text-ink/45">Ancestral lineage name, e.g. Kashyap, Bharadwaj · <span lang={langStore.current}>{tx('hintGotra', langStore.current)}</span></p>
								<p class="mt-0.5 text-[10px] text-ink/40">{ASCII_HINT}</p>
								{#if errors.gotra}<p class="mt-1 text-xs text-vermilion" data-error="true">{errors.gotra}</p>{/if}
							</div>

							<!-- Kuldevata -->
							<div>
								<BilingualLabel key="kuldevata" for="kuldevata" />
								<input id="kuldevata" type="text" class="input" class:border-vermilion={errors.kuldevata} bind:value={kuldevata} oninput={(e) => (kuldevata = asciiOnly(e.currentTarget.value))} />
								<p class="mt-0.5 text-xs text-ink/45">Your family deity, e.g. Bhavani, Khandoba · <span lang={langStore.current}>{tx('hintKuldevata', langStore.current)}</span></p>
								<p class="mt-0.5 text-[10px] text-ink/40">{ASCII_HINT}</p>
								{#if errors.kuldevata}<p class="mt-1 text-xs text-vermilion" data-error="true">{errors.kuldevata}</p>{/if}
							</div>

							<!-- Devak -->
							<div>
								<BilingualLabel key="devak" for="devak" />
								<input id="devak" type="text" class="input" class:border-vermilion={errors.devak} bind:value={devak} oninput={(e) => (devak = asciiOnly(e.currentTarget.value))} />
								<p class="mt-0.5 text-xs text-ink/45">Your family devak symbol, e.g. Neem, Audumbar · <span lang={langStore.current}>{tx('hintDevak', langStore.current)}</span></p>
								<p class="mt-0.5 text-[10px] text-ink/40">{ASCII_HINT}</p>
								{#if errors.devak}<p class="mt-1 text-xs text-vermilion" data-error="true">{errors.devak}</p>{/if}
							</div>

							<!-- Nakshatram -->
							<div>
								<BilingualLabel key="nakshatram" for="nakshatram" />
								<Combobox
									id="nakshatram"
									bind:value={nakshatram}
									options={NAKSHATRAS}
									placeholder="Select…"
									class={errors.nakshatram ? 'border-vermilion' : ''}
								/>
								{#if errors.nakshatram}<p class="mt-1 text-xs text-vermilion" data-error="true">{errors.nakshatram}</p>{/if}
							</div>

							<!-- Rashi -->
							<div>
								<BilingualLabel key="rashi" for="rashi" />
								<Combobox
									id="rashi"
									bind:value={rashi}
									options={RASHIS}
									placeholder="Select…"
									class={errors.rashi ? 'border-vermilion' : ''}
								/>
								{#if errors.rashi}<p class="mt-1 text-xs text-vermilion" data-error="true">{errors.rashi}</p>{/if}
							</div>

							<!-- Manglik -->
							<div class="sm:col-span-2">
								<fieldset>
									<legend class="label">
										<span class="block">{T.manglik.en}</span>
										<span class="block text-xs leading-tight font-normal text-ink/60" lang={langStore.current}>{tx('manglik', langStore.current)}</span>
									</legend>
									<div class="mt-1 flex flex-wrap gap-4">
										{#each [{ value: 'yes', label: 'Yes' }, { value: 'no', label: 'No' }, { value: 'partial', label: 'Partial' }, { value: 'unknown', label: "Unknown / Don't Know" }] as opt}
											<label class="flex cursor-pointer items-center gap-2">
												<input type="radio" name="manglik" value={opt.value} bind:group={manglik} class="accent-maroon" />
												<span>{opt.label}</span>
											</label>
										{/each}
									</div>
								</fieldset>
							</div>

							<!-- Time of Birth (optional) -->
							<div>
								<BilingualLabel key="timeOfBirth" for="time_enabled" />
								<div class="flex items-center gap-2">
									<input type="checkbox" id="time_enabled" bind:checked={timeEnabled} class="accent-maroon" />
									<label for="time_enabled" class="text-sm text-ink/60">Add time of birth</label>
								</div>
								{#if timeEnabled}
								<div class="mt-2 flex items-center gap-2">
									<Combobox bind:value={time_hour} options={TIME_HOURS} placeholder="H" class="w-20" />
									<span class="text-ink/60">:</span>
									<Combobox bind:value={time_minute} options={TIME_MINUTES} placeholder="MM" class="w-20" />
									<Combobox bind:value={time_ampm} options={TIME_AMPM} placeholder="AM" class="w-20" />
								</div>
								{/if}
								<p class="mt-0.5 text-xs text-ink/45">Used for kundali matching · <span lang={langStore.current}>{tx('hintTimeOfBirth', langStore.current)}</span></p>
							</div>

							<!-- Place of Birth (optional) -->
							<div>
								<BilingualLabel key="placeOfBirth" for="place_of_birth" />
								<input id="place_of_birth" type="text" class="input" bind:value={place_of_birth} oninput={(e) => (place_of_birth = asciiOnly(e.currentTarget.value))} placeholder="Optional" />
								<p class="mt-0.5 text-xs text-ink/45">City/town where you were born · <span lang={langStore.current}>{tx('hintPlaceOfBirth', langStore.current)}</span></p>
								<p class="mt-0.5 text-[10px] text-ink/40">{ASCII_HINT}</p>
							</div>
						</div>

					{:else if i === 3}
						<!-- ── Section 3: Education & Career ───────────────────────── -->
						<div class="grid gap-4 sm:grid-cols-2">
							<!-- Education -->
							<div>
								<BilingualLabel key="education" for="education" required />
								<input id="education" type="text" class="input" class:border-vermilion={errors.education} bind:value={education} oninput={(e) => (education = asciiOnly(e.currentTarget.value))} placeholder="e.g. B.Tech, M.Sc" />
								<p class="mt-0.5 text-[10px] text-ink/40">{ASCII_HINT}</p>
								{#if errors.education}<p class="mt-1 text-xs text-vermilion" data-error="true">{errors.education}</p>{/if}
							</div>

							<!-- College / University (optional) -->
							<div>
								<BilingualLabel key="collegeUniversity" for="college_university" />
								<input id="college_university" type="text" class="input" bind:value={college_university} oninput={(e) => (college_university = asciiOnly(e.currentTarget.value))} placeholder="Optional" />
								<p class="mt-0.5 text-[10px] text-ink/40">{ASCII_HINT}</p>
							</div>

							<!-- Occupation -->
							<div>
								<BilingualLabel key="occupation" for="occupation" required />
								<input id="occupation" type="text" class="input" class:border-vermilion={errors.occupation} bind:value={occupation} oninput={(e) => (occupation = asciiOnly(e.currentTarget.value))} placeholder="e.g. Software Engineer" />
								<p class="mt-0.5 text-[10px] text-ink/40">{ASCII_HINT}</p>
								{#if errors.occupation}<p class="mt-1 text-xs text-vermilion" data-error="true">{errors.occupation}</p>{/if}
							</div>

							<!-- Employer (optional) -->
							<div>
								<BilingualLabel key="employer" for="employer" />
								<input id="employer" type="text" class="input" bind:value={employer} oninput={(e) => (employer = asciiOnly(e.currentTarget.value))} placeholder="Optional" />
								<p class="mt-0.5 text-[10px] text-ink/40">{ASCII_HINT}</p>
							</div>

							<!-- Annual Income (optional) -->
							<div>
								<BilingualLabel key="income" for="annual_income" />
								<input id="annual_income" type="number" min="0" step="10000" class="input" bind:value={annual_income_inr} placeholder="Optional, e.g. 800000" />
								<p class="mt-0.5 text-xs text-ink/45">Annual income in Indian Rupees (numbers only) · <span lang={langStore.current}>{tx('hintAnnualIncome', langStore.current)}</span></p>
							</div>

							<!-- Work Location (optional) -->
							<div>
								<BilingualLabel key="workLocation" for="work_location" />
								<input id="work_location" type="text" class="input" bind:value={work_location} oninput={(e) => (work_location = asciiOnly(e.currentTarget.value))} placeholder="Optional" />
								<p class="mt-0.5 text-[10px] text-ink/40">{ASCII_HINT}</p>
							</div>
						</div>

					{:else if i === 4}
						<!-- ── Section 4: Family ────────────────────────────────────── -->
						<div class="grid gap-4 sm:grid-cols-2">
							<!-- Father Name -->
							<div>
								<BilingualLabel key="fatherName" for="father_name" />
								<input id="father_name" type="text" maxlength="100" class="input" class:border-vermilion={errors.father_name} bind:value={father_name} oninput={(e) => (father_name = e.currentTarget.value)} placeholder="Father's full name" />
								{#if errors.father_name}<p class="mt-1 text-xs text-vermilion" data-error="true">{errors.father_name}</p>{/if}
							</div>

							<!-- Mother Name -->
							<div>
								<BilingualLabel key="motherName" for="mother_name" />
								<input id="mother_name" type="text" maxlength="100" class="input" class:border-vermilion={errors.mother_name} bind:value={mother_name} oninput={(e) => (mother_name = e.currentTarget.value)} placeholder="Mother's full name" />
								{#if errors.mother_name}<p class="mt-1 text-xs text-vermilion" data-error="true">{errors.mother_name}</p>{/if}
							</div>

							<!-- Father's Occupation -->
							<div>
								<BilingualLabel key="fatherOccupation" for="father_occupation" />
								<input id="father_occupation" type="text" class="input" bind:value={father_occupation} oninput={(e) => (father_occupation = asciiOnly(e.currentTarget.value))} placeholder="Optional" />
								<p class="mt-0.5 text-[10px] text-ink/40">{ASCII_HINT}</p>
							</div>

							<!-- Mother's Occupation -->
							<div>
								<BilingualLabel key="motherOccupation" for="mother_occupation" />
								<input id="mother_occupation" type="text" class="input" bind:value={mother_occupation} oninput={(e) => (mother_occupation = asciiOnly(e.currentTarget.value))} placeholder="Optional" />
								<p class="mt-0.5 text-[10px] text-ink/40">{ASCII_HINT}</p>
							</div>

							<!-- Number of family members -->
							<div>
								<BilingualLabel key="numFamilyMembers" for="num_family_members" />
								<input id="num_family_members" type="number" min="1" max="30" class="input" bind:value={num_family_members} placeholder="Total members in family" />
							</div>

							<!-- Number of Brothers -->
							<div>
								<BilingualLabel key="numBrothers" for="num_brothers" />
								<input id="num_brothers" type="number" min="0" max="20" class="input" bind:value={num_brothers} placeholder="Optional" />
							</div>

							<!-- Brothers Married -->
							<div>
								<BilingualLabel key="numBrothersMarried" for="num_brothers_married" />
								<input id="num_brothers_married" type="number" min="0" max="20" class="input" bind:value={num_brothers_married} placeholder="Optional" />
							</div>

							<!-- Number of Sisters -->
							<div>
								<BilingualLabel key="numSisters" for="num_sisters" />
								<input id="num_sisters" type="number" min="0" max="20" class="input" bind:value={num_sisters} placeholder="Optional" />
							</div>

							<!-- Sisters Married -->
							<div>
								<BilingualLabel key="numSistersMarried" for="num_sisters_married" />
								<input id="num_sisters_married" type="number" min="0" max="20" class="input" bind:value={num_sisters_married} placeholder="Optional" />
							</div>

							<!-- Family Type -->
							<div>
								<BilingualLabel key="familyType" for="family_type_sel_w" />
								<Combobox id="family_type_sel_w" bind:value={family_type} options={FAMILY_TYPES} placeholder="Not specified" />
								{#if errors.family_type}<p class="mt-1 text-xs text-vermilion" data-error="true">{errors.family_type}</p>{/if}
							</div>

							<!-- Family Status -->
							<div>
								<BilingualLabel key="familyStatus" for="family_status" />
								<Combobox id="family_status" bind:value={family_status} options={FAMILY_STATUSES} placeholder="Select… (optional)" />
							</div>

							<!-- Family Values -->
							<div>
								<BilingualLabel key="familyValues" for="family_values" />
								<Combobox id="family_values" bind:value={family_values} options={FAMILY_VALUES_OPTS} placeholder="Select… (optional)" />
							</div>

							<!-- Native Place -->
							<div class="sm:col-span-2">
								<BilingualLabel key="nativePlace" for="native_place" />
								<input id="native_place" type="text" class="input" class:border-vermilion={errors.native_place} bind:value={native_place} oninput={(e) => (native_place = asciiOnly(e.currentTarget.value))} placeholder="Optional — village/town of origin" />
								<p class="mt-0.5 text-xs text-ink/45">Village or town your family originally belongs to · <span lang={langStore.current}>{tx('hintNativePlace', langStore.current)}</span></p>
								<p class="mt-0.5 text-[10px] text-ink/40">{ASCII_HINT}</p>
								{#if errors.native_place}<p class="mt-1 text-xs text-vermilion" data-error="true">{errors.native_place}</p>{/if}
							</div>
						</div>

					{:else if i === 5}
						<!-- ── Section 5: Lifestyle ─────────────────────────────────── -->
						<div class="space-y-4">
							<div class="grid gap-4 sm:grid-cols-3">
								<!-- Diet -->
								<div>
									<BilingualLabel key="diet" for="diet_sel_w" />
									<Combobox id="diet_sel_w" bind:value={diet} options={DIET_OPTS} placeholder="Select…" />
								</div>

								<!-- Smokes -->
								<div>
									<BilingualLabel key="smokes" for="smokes_sel_w" />
									<Combobox id="smokes_sel_w" bind:value={smokes} options={SMOKE_DRINK_OPTS} placeholder="Prefer not to say" />
								</div>

								<!-- Drinks -->
								<div>
									<BilingualLabel key="drinks" for="drinks_sel_w" />
									<Combobox id="drinks_sel_w" bind:value={drinks} options={SMOKE_DRINK_OPTS} placeholder="Prefer not to say" />
								</div>
							</div>

							<!-- Hobbies (optional textarea) -->
							<div>
								<BilingualLabel key="hobbies" for="hobbies" />
								<textarea id="hobbies" class="input min-h-[80px] resize-y" bind:value={hobbies} oninput={(e) => (hobbies = asciiOnly(e.currentTarget.value))} placeholder="Optional — e.g. Reading, Cricket, Cooking"></textarea>
								<p class="mt-0.5 text-[10px] text-ink/40">{ASCII_HINT}</p>
							</div>
						</div>

					{:else if i === 6}
						<!-- ── Section 6: Location ──────────────────────────────────── -->
						<div class="grid gap-4 sm:grid-cols-2">
							<!-- City -->
							<div>
								<BilingualLabel key="city" for="city" required />
								<input id="city" type="text" class="input" class:border-vermilion={errors.city} bind:value={city} oninput={(e) => (city = asciiOnly(e.currentTarget.value))} />
								<p class="mt-0.5 text-[10px] text-ink/40">{ASCII_HINT}</p>
								{#if errors.city}<p class="mt-1 text-xs text-vermilion" data-error="true">{errors.city}</p>{/if}
							</div>

							<!-- State -->
							<div>
								<BilingualLabel key="state" for="state_w" />
								<Combobox id="state_w" bind:value={state_field} options={INDIA_STATES} allowCustom={true} placeholder="Select state" />
							</div>

							<!-- Country -->
							<div>
								<BilingualLabel key="country" for="country_w" />
								<Combobox id="country_w" bind:value={country} options={COUNTRIES} placeholder="Select country" />
							</div>

							<!-- Pin Code (optional) -->
							<div>
								<label for="pin_code" class="label">
									<span class="block">Pin Code <span class="text-xs font-normal text-ink/50">(optional)</span></span>
									<span class="block text-xs leading-tight font-normal" lang={langStore.current}>{tx('pinCode', langStore.current)}</span>
								</label>
								<input id="pin_code" type="text" inputmode="numeric" maxlength="10" class="input" bind:value={pin_code} placeholder="e.g. 500001" />
							</div>
						</div>

					{:else if i === 7}
						<!-- ── Section 7: About & Expectations ─────────────────────── -->
						<div class="space-y-4">
							<!-- About Yourself -->
							<div>
								<BilingualLabel key="about" for="about" />
								<p class="mt-0.5 text-xs text-ink/45">Tell prospective families about yourself — your values, personality, lifestyle · <span lang={langStore.current}>{tx('hintAbout', langStore.current)}</span></p>
								<textarea id="about" class="input mt-1 min-h-[120px] resize-y" class:border-vermilion={errors.about} bind:value={about} oninput={(e) => (about = asciiOnly(e.currentTarget.value))} maxlength={500} placeholder="A short description about yourself, your family, and interests…"></textarea>
								<div class="mt-1 flex justify-between">
									{#if errors.about}
										<p class="text-xs text-vermilion" data-error="true">{errors.about}</p>
									{:else}
										<p class="text-[10px] text-ink/40">{ASCII_HINT}</p>
									{/if}
									<p class="text-xs text-ink/40">{about.length}/500</p>
								</div>
							</div>

							<!-- Partner Expectations -->
							<div>
								<BilingualLabel key="partnerExpectations" for="expectations" />
								<p class="mt-0.5 text-xs text-ink/45">Describe the qualities you're looking for in a partner · <span lang={langStore.current}>{tx('hintPartnerExpectations', langStore.current)}</span></p>
								<textarea id="expectations" class="input mt-1 min-h-[140px] resize-y" class:border-vermilion={errors.partner_expectations} bind:value={partner_expectations} oninput={(e) => (partner_expectations = asciiOnly(e.currentTarget.value))} maxlength={800} placeholder="Describe what you're looking for in a partner…"></textarea>
								<div class="mt-1 flex justify-between">
									{#if errors.partner_expectations}
										<p class="text-xs text-vermilion" data-error="true">{errors.partner_expectations}</p>
									{:else}
										<p class="text-[10px] text-ink/40">{ASCII_HINT}</p>
									{/if}
									<p class="text-xs text-ink/40">{partner_expectations.length}/800</p>
								</div>
							</div>
						</div>

					{:else if i === 8}
						<!-- ── Section 8: Photos ────────────────────────────────────── -->
						{#if errors._photos}
							<p class="mb-3 text-sm text-vermilion" data-error="true">{errors._photos}</p>
						{/if}
						{#if profileId}
							<PhotoUpload {profileId} initialPhotos={[]} isOwner={true} onCountChange={(n) => (wizardPhotoCount = n)} />
						{:else}
							<p class="py-4 text-center text-sm text-ink/60">Save the first section to enable photo upload.</p>
						{/if}
					{/if}

					<!-- Section footer: equal-width Cancel / Save / Submit row.
					     English on top, active indic-language underneath (no delimiter). -->
					<div class="mt-4 flex items-stretch gap-2 border-t border-gold/30 pt-4">
						<a
							href="/dashboard"
							class="btn-secondary flex flex-1 flex-col items-center justify-center text-center leading-tight px-2 py-2 min-h-[56px] whitespace-normal"
						>
							<span class="text-xs sm:text-sm">{T.cancel.en}</span>
							<span lang={langStore.current} class="text-[10px] sm:text-xs opacity-90">{tx('cancel', langStore.current)}</span>
						</a>
						{#if i === 8}
							<!-- Last step: Save Draft + Submit for Approval -->
							<button
								type="button"
								onclick={() => saveSection(i)}
								class="btn-secondary flex flex-1 flex-col items-center justify-center text-center leading-tight px-2 py-2 min-h-[56px] whitespace-normal"
								disabled={submitting}
							>
								{#if submitting && activeSection === i}
									<span class="text-xs sm:text-sm">Saving…</span>
								{:else}
									<span class="text-xs sm:text-sm">{T.save.en}</span>
									<span lang={langStore.current} class="text-[10px] sm:text-xs opacity-90">{tx('save', langStore.current)}</span>
								{/if}
							</button>
							{#if onSubmitForApproval && (profileStatus === 'draft' || profileStatus === 'rejected')}
								<button
									type="button"
									onclick={handleSubmitForApproval}
									class="btn-primary flex flex-1 flex-col items-center justify-center text-center leading-tight px-2 py-2 min-h-[56px] whitespace-normal"
									disabled={!isSectionValid(8) || submittingForApproval}
								>
									{#if submittingForApproval}
										<span class="text-xs sm:text-sm">Submitting…</span>
									{:else}
										<span class="text-xs sm:text-sm">Submit for Approval</span>
										<span lang={langStore.current} class="text-[10px] sm:text-xs opacity-90">{tx('submitForApproval', langStore.current)}</span>
									{/if}
								</button>
							{/if}
						{:else}
							<!-- Intermediate steps: Save & Continue -->
							<button
								type="button"
								onclick={() => saveSection(i)}
								class="btn-primary flex flex-1 flex-col items-center justify-center text-center leading-tight px-2 py-2 min-h-[56px] whitespace-normal"
								disabled={!isSectionValid(i) || submitting}
							>
								{#if submitting && activeSection === i}
									<span class="text-xs sm:text-sm">Saving…</span>
								{:else}
									<span class="text-xs sm:text-sm">Save & Continue →</span>
								{/if}
							</button>
						{/if}
					</div>
				</div>
			{/if}
		</div>
	{/each}
</div>

{#if onSubmitForApproval && (profileStatus === 'draft' || profileStatus === 'rejected')}
	{@const allDone = SECTIONS.every((_, i) => completedSections.has(i) || i === SECTIONS.length - 1)}
	{#if allDone || completedSections.size >= SECTIONS.length - 1}
		<div class="mt-8 rounded-lg border border-gold/30 bg-white p-6 text-center shadow-sm">
			<h3 class="mb-1 font-serif text-xl font-semibold text-maroon">Ready to Submit?</h3>
			<p class="mb-4 text-sm text-ink/60">Once submitted, your profile goes to admin for review. Only approved profiles appear in search results.</p>
			<button
				type="button"
				onclick={() => onSubmitForApproval?.()}
				class="btn-primary flex flex-col items-center justify-center text-center leading-tight px-10 py-2 min-h-[56px] whitespace-normal"
				disabled={submittingForApproval}
			>
				<span class="text-base">{submittingForApproval ? 'Submitting…' : 'Submit for Approval'}</span>
				{#if !submittingForApproval}<span lang={langStore.current} class="text-xs opacity-90">{tx('submitForApproval', langStore.current)}</span>{/if}
			</button>
		</div>
	{/if}
{/if}

{:else}
	<!-- ══════════════════════════════════════════════════════════════════════ -->
	<!-- NORMAL MODE (edit page — all sections open)                          -->
	<!-- ══════════════════════════════════════════════════════════════════════ -->

	<!-- ── Section: Basic Information ──────────────────────────────────────── -->
	<details open class="card">
		<summary
			class="mb-1 flex cursor-pointer list-none items-center gap-2 font-serif text-xl font-semibold text-maroon"
		>
			<span class="text-tangerine">▸</span>
			<span
				class="mr-1 inline-flex h-6 w-6 items-center justify-center rounded-full bg-maroon/10 text-sm font-bold text-maroon"
			>1</span>
			Basic Information
			<span class="ml-1 text-sm font-normal text-ink/50" lang={langStore.current}>{tx('secBasicInfo', langStore.current)}</span>
		</summary>

		<div class="mt-4 space-y-4">
			<!-- Gender -->
			<fieldset>
				<legend class="label">
					<span class="block">{T.gender.en} <span class="text-vermilion">*</span></span>
					<span class="block text-xs leading-tight font-normal text-ink/60" lang={langStore.current}
						>{tx('gender', langStore.current)}</span
					>
				</legend>
				<div class="mt-1 flex gap-6">
					{#each [{ value: 'bride', key: 'bride' as const }, { value: 'groom', key: 'groom' as const }] as opt}
						<label class="flex cursor-pointer items-center gap-2">
							<input
								type="radio"
								name="gender"
								value={opt.value}
								bind:group={gender}
								class="accent-maroon"
							/>
							<span>{T[opt.key].en}</span>
							<span class="text-xs text-ink/60" lang={langStore.current}>{tx(opt.key, langStore.current)}</span>
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
						oninput={(e) => (first_name = asciiOnly(e.currentTarget.value))}
					/>
					<p class="mt-0.5 text-[10px] text-ink/40">{ASCII_HINT}</p>
					{#if errors.first_name}<p class="mt-1 text-xs text-vermilion" data-error="true">
							{errors.first_name}
						</p>{/if}
				</div>

				<!-- Surname / Clan -->
				<div>
					<BilingualLabel key="surnameClan" for="surname_clan" />
					<input
						id="surname_clan"
						type="text"
						class="input"
						class:border-vermilion={errors.surname_clan}
						bind:value={surname_clan}
						oninput={(e) => (surname_clan = asciiOnly(e.currentTarget.value))}
					/>
					<p class="mt-0.5 text-xs text-ink/45">Your family/clan surname, e.g. Desai, Patil, More · <span lang={langStore.current}>{tx('hintSurnameClan', langStore.current)}</span></p>
					<p class="mt-0.5 text-[10px] text-ink/40">{ASCII_HINT}</p>
					{#if errors.surname_clan}<p class="mt-1 text-xs text-vermilion" data-error="true">
							{errors.surname_clan}
						</p>{/if}
				</div>

				<!-- Date of Birth -->
				<div>
					<BilingualLabel key="dob" for="dob_edit" required />
					<DobInput id="dob_edit" bind:value={dob} error={!!errors.dob} />
					{#if errors.dob}<p class="mt-1 text-xs text-vermilion" data-error="true">
							{errors.dob}
						</p>{/if}
				</div>

				<!-- Marital Status -->
				<div>
					<BilingualLabel key="maritalStatus" for="marital_status" />
					<Combobox
						id="marital_status"
						bind:value={marital_status}
						options={MARITAL_STATUSES}
						placeholder="Select…"
						class={errors.marital_status ? 'border-vermilion' : ''}
					/>
					{#if errors.marital_status}<p class="mt-1 text-xs text-vermilion" data-error="true">
							{errors.marital_status}
						</p>{/if}
				</div>

				<!-- Mother Tongue -->
				<div>
					<BilingualLabel key="motherTongue" for="mother_tongue_e" />
					<Combobox id="mother_tongue_e" bind:value={mother_tongue} options={MOTHER_TONGUES} placeholder="Select language" />
					<p class="mt-0.5 text-[10px] text-ink/40">{ASCII_HINT}</p>
				</div>

				<!-- Sub-caste (optional) -->
				<div class="sm:col-span-2">
					<BilingualLabel key="caste" for="caste_edit" />
					<Combobox id="caste_edit" bind:value={caste} options={CASTE_OPTIONS} allowCustom={true} placeholder="Select or type caste" />
					<p class="mt-0.5 text-xs text-ink/45">Pick from the list, or type your own if different · <span lang={langStore.current}>{tx('hintCastePickOrType', langStore.current)}</span></p>
				</div>

				<div>
					<BilingualLabel key="subCaste" for="sub_caste_edit" />
					<Combobox id="sub_caste_edit" bind:value={sub_caste} options={MARATHA_SUB_CASTES} allowCustom={true} placeholder="Select or type sub-caste" />
					<p class="mt-0.5 text-xs text-ink/45">Pick from the list, or type your own if different · <span lang={langStore.current}>{tx('hintCastePickOrType', langStore.current)}</span></p>
				</div>
			</div>
		</div>
	</details>

	<!-- ── Section: Physical ─────────────────────────────────────────────────── -->
	<details open class="card">
		<summary
			class="mb-1 flex cursor-pointer list-none items-center gap-2 font-serif text-xl font-semibold text-maroon"
		>
			<span class="text-tangerine">▸</span>
			<span
				class="mr-1 inline-flex h-6 w-6 items-center justify-center rounded-full bg-maroon/10 text-sm font-bold text-maroon"
			>2</span>
			Physical
			<span class="ml-1 text-sm font-normal text-ink/50" lang={langStore.current}>{tx('secPhysical', langStore.current)}</span>
		</summary>

		<div class="mt-4 grid gap-4 sm:grid-cols-2">
			<!-- Height -->
			<div class="sm:col-span-2">
				<BilingualLabel key="height" for="height_cm" />
				<p class="mb-1 text-sm text-ink/60">{cmToFtIn(height_cm)}</p>
				<input
					id="height_cm"
					type="range"
					min="120"
					max="229"
					step="1"
					bind:value={height_cm}
					class="w-full accent-maroon"
				/>
				<div class="mt-1 flex justify-between text-xs text-ink/40">
					<span>3'11"</span><span>7'6"</span>
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
				<Combobox id="complexion" bind:value={complexion} options={COMPLEXIONS} placeholder="Select…" />
			</div>

			<!-- Body Type (optional) -->
			<div>
				<BilingualLabel key="bodyType" for="body_type" />
				<Combobox id="body_type" bind:value={body_type} options={BODY_TYPES} placeholder="Select… (optional)" />
			</div>

			<!-- Blood Group (optional) -->
			<div>
				<BilingualLabel key="bloodGroup" for="blood_group" />
				<Combobox id="blood_group" bind:value={blood_group} options={BLOOD_GROUPS_OPTS} placeholder="Select… (optional)" />
			</div>
		</div>
	</details>

	<!-- ── Section: Astrology ────────────────────────────────────────────────── -->
	<details open class="card">
		<summary
			class="mb-1 flex cursor-pointer list-none items-center gap-2 font-serif text-xl font-semibold text-maroon"
		>
			<span class="text-tangerine">▸</span>
			<span
				class="mr-1 inline-flex h-6 w-6 items-center justify-center rounded-full bg-maroon/10 text-sm font-bold text-maroon"
			>3</span>
			Astrology
			<span class="ml-1 text-sm font-normal text-ink/50" lang={langStore.current}>{tx('secAstrology', langStore.current)}</span>
		</summary>

		<div class="mt-4 grid gap-4 sm:grid-cols-2">
			<!-- Gotra -->
			<div>
				<BilingualLabel key="gotra" for="gotra" />
				<input
					id="gotra"
					type="text"
					class="input"
					class:border-vermilion={errors.gotra}
					bind:value={gotra}
					oninput={(e) => (gotra = asciiOnly(e.currentTarget.value))}
				/>
				<p class="mt-0.5 text-xs text-ink/45">
					Ancestral lineage name, e.g. Kashyap, Bharadwaj · <span lang={langStore.current}>{tx('hintGotra', langStore.current)}</span>
				</p>
				<p class="mt-0.5 text-[10px] text-ink/40">{ASCII_HINT}</p>
				{#if errors.gotra}<p class="mt-1 text-xs text-vermilion" data-error="true">
						{errors.gotra}
					</p>{/if}
			</div>

			<!-- Kuldevata -->
			<div>
				<BilingualLabel key="kuldevata" for="kuldevata" />
				<input
					id="kuldevata"
					type="text"
					class="input"
					class:border-vermilion={errors.kuldevata}
					bind:value={kuldevata}
					oninput={(e) => (kuldevata = asciiOnly(e.currentTarget.value))}
				/>
				<p class="mt-0.5 text-xs text-ink/45">
					Your family deity, e.g. Bhavani, Khandoba · <span lang={langStore.current}>{tx('hintKuldevata', langStore.current)}</span>
				</p>
				<p class="mt-0.5 text-[10px] text-ink/40">{ASCII_HINT}</p>
				{#if errors.kuldevata}<p class="mt-1 text-xs text-vermilion" data-error="true">
						{errors.kuldevata}
					</p>{/if}
			</div>

			<!-- Devak -->
			<div>
				<BilingualLabel key="devak" for="devak" />
				<input
					id="devak"
					type="text"
					class="input"
					class:border-vermilion={errors.devak}
					bind:value={devak}
					oninput={(e) => (devak = asciiOnly(e.currentTarget.value))}
				/>
				<p class="mt-0.5 text-xs text-ink/45">
					Your family devak symbol, e.g. Neem, Audumbar · <span lang={langStore.current}>{tx('hintDevak', langStore.current)}</span>
				</p>
				<p class="mt-0.5 text-[10px] text-ink/40">{ASCII_HINT}</p>
				{#if errors.devak}<p class="mt-1 text-xs text-vermilion" data-error="true">
						{errors.devak}
					</p>{/if}
			</div>

			<!-- Nakshatram -->
			<div>
				<BilingualLabel key="nakshatram" for="nakshatram" />
				<Combobox
					id="nakshatram"
					bind:value={nakshatram}
					options={NAKSHATRAS}
					placeholder="Select…"
					class={errors.nakshatram ? 'border-vermilion' : ''}
				/>
				{#if errors.nakshatram}<p class="mt-1 text-xs text-vermilion" data-error="true">
						{errors.nakshatram}
					</p>{/if}
			</div>

			<!-- Rashi -->
			<div>
				<BilingualLabel key="rashi" for="rashi" />
				<Combobox
					id="rashi"
					bind:value={rashi}
					options={RASHIS}
					placeholder="Select…"
					class={errors.rashi ? 'border-vermilion' : ''}
				/>
				{#if errors.rashi}<p class="mt-1 text-xs text-vermilion" data-error="true">
						{errors.rashi}
					</p>{/if}
			</div>

			<!-- Manglik -->
			<div class="sm:col-span-2">
				<fieldset>
					<legend class="label">
						<span class="block">{T.manglik.en}</span>
						<span class="block text-xs leading-tight font-normal text-ink/60" lang={langStore.current}
							>{tx('manglik', langStore.current)}</span
						>
					</legend>
					<div class="mt-1 flex flex-wrap gap-4">
						{#each [{ value: 'yes', label: 'Yes' }, { value: 'no', label: 'No' }, { value: 'partial', label: 'Partial' }, { value: 'unknown', label: "Unknown / Don't Know" }] as opt}
							<label class="flex cursor-pointer items-center gap-2">
								<input
									type="radio"
									name="manglik"
									value={opt.value}
									bind:group={manglik}
									class="accent-maroon"
								/>
								<span>{opt.label}</span>
							</label>
						{/each}
					</div>
				</fieldset>
			</div>

			<!-- Time of Birth (optional) -->
			<div>
				<BilingualLabel key="timeOfBirth" for="time_enabled_n" />
				<div class="flex items-center gap-2">
					<input type="checkbox" id="time_enabled_n" bind:checked={timeEnabled} class="accent-maroon" />
					<label for="time_enabled_n" class="text-sm text-ink/60">Add time of birth</label>
				</div>
				{#if timeEnabled}
				<div class="mt-2 flex items-center gap-2">
					<Combobox bind:value={time_hour} options={TIME_HOURS} placeholder="H" class="w-20" />
					<span class="text-ink/60">:</span>
					<Combobox bind:value={time_minute} options={TIME_MINUTES} placeholder="MM" class="w-20" />
					<Combobox bind:value={time_ampm} options={TIME_AMPM} placeholder="AM" class="w-20" />
				</div>
				{/if}
				<p class="mt-0.5 text-xs text-ink/45">Used for kundali matching · <span lang={langStore.current}>{tx('hintTimeOfBirth', langStore.current)}</span></p>
			</div>

			<!-- Place of Birth (optional) -->
			<div>
				<BilingualLabel key="placeOfBirth" for="place_of_birth" />
				<input
					id="place_of_birth"
					type="text"
					class="input"
					bind:value={place_of_birth}
					oninput={(e) => (place_of_birth = asciiOnly(e.currentTarget.value))}
					placeholder="Optional"
				/>
				<p class="mt-0.5 text-xs text-ink/45">City/town where you were born · <span lang={langStore.current}>{tx('hintPlaceOfBirth', langStore.current)}</span></p>
				<p class="mt-0.5 text-[10px] text-ink/40">{ASCII_HINT}</p>
			</div>
		</div>
	</details>

	<!-- ── Section: Education & Career ──────────────────────────────────────── -->
	<details open class="card">
		<summary
			class="mb-1 flex cursor-pointer list-none items-center gap-2 font-serif text-xl font-semibold text-maroon"
		>
			<span class="text-tangerine">▸</span>
			<span
				class="mr-1 inline-flex h-6 w-6 items-center justify-center rounded-full bg-maroon/10 text-sm font-bold text-maroon"
			>4</span>
			Education &amp; Career
			<span class="ml-1 text-sm font-normal text-ink/50" lang={langStore.current}>{tx('secEducation', langStore.current)}</span>
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
					oninput={(e) => (education = asciiOnly(e.currentTarget.value))}
					placeholder="e.g. B.Tech, M.Sc"
				/>
				<p class="mt-0.5 text-[10px] text-ink/40">{ASCII_HINT}</p>
				{#if errors.education}<p class="mt-1 text-xs text-vermilion" data-error="true">
						{errors.education}
					</p>{/if}
			</div>

			<!-- College / University (optional) -->
			<div>
				<BilingualLabel key="collegeUniversity" for="college_university" />
				<input
					id="college_university"
					type="text"
					class="input"
					bind:value={college_university}
					oninput={(e) => (college_university = asciiOnly(e.currentTarget.value))}
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
					oninput={(e) => (occupation = asciiOnly(e.currentTarget.value))}
					placeholder="e.g. Software Engineer"
				/>
				<p class="mt-0.5 text-[10px] text-ink/40">{ASCII_HINT}</p>
				{#if errors.occupation}<p class="mt-1 text-xs text-vermilion" data-error="true">
						{errors.occupation}
					</p>{/if}
			</div>

			<!-- Employer (optional) -->
			<div>
				<BilingualLabel key="employer" for="employer" />
				<input
					id="employer"
					type="text"
					class="input"
					bind:value={employer}
					oninput={(e) => (employer = asciiOnly(e.currentTarget.value))}
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
				<p class="mt-0.5 text-xs text-ink/45">
					Annual income in Indian Rupees (numbers only) · <span lang={langStore.current}>{tx('hintAnnualIncome', langStore.current)}</span>
				</p>
			</div>

			<!-- Work Location (optional) -->
			<div>
				<BilingualLabel key="workLocation" for="work_location" />
				<input
					id="work_location"
					type="text"
					class="input"
					bind:value={work_location}
					oninput={(e) => (work_location = asciiOnly(e.currentTarget.value))}
					placeholder="Optional"
				/>
				<p class="mt-0.5 text-[10px] text-ink/40">{ASCII_HINT}</p>
			</div>
		</div>
	</details>

	<!-- ── Section: Family ───────────────────────────────────────────────────── -->
	<details open class="card">
		<summary
			class="mb-1 flex cursor-pointer list-none items-center gap-2 font-serif text-xl font-semibold text-maroon"
		>
			<span class="text-tangerine">▸</span>
			<span
				class="mr-1 inline-flex h-6 w-6 items-center justify-center rounded-full bg-maroon/10 text-sm font-bold text-maroon"
			>5</span>
			Family
			<span class="ml-1 text-sm font-normal text-ink/50" lang={langStore.current}>{tx('secFamily', langStore.current)}</span>
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
					class:border-vermilion={errors.father_name}
					bind:value={father_name}
					oninput={(e) => (father_name = e.currentTarget.value)}
					placeholder="Father's full name"
				/>
				{#if errors.father_name}<p class="mt-1 text-xs text-vermilion" data-error="true">
						{errors.father_name}
					</p>{/if}
			</div>

			<!-- Mother Name -->
			<div>
				<BilingualLabel key="motherName" for="mother_name" />
				<input
					id="mother_name"
					type="text"
					maxlength="100"
					class="input"
					class:border-vermilion={errors.mother_name}
					bind:value={mother_name}
					oninput={(e) => (mother_name = e.currentTarget.value)}
					placeholder="Mother's full name"
				/>
				{#if errors.mother_name}<p class="mt-1 text-xs text-vermilion" data-error="true">
						{errors.mother_name}
					</p>{/if}
			</div>

			<!-- Father's Occupation -->
			<div>
				<BilingualLabel key="fatherOccupation" for="father_occupation" />
				<input
					id="father_occupation"
					type="text"
					class="input"
					bind:value={father_occupation}
					oninput={(e) => (father_occupation = asciiOnly(e.currentTarget.value))}
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
					oninput={(e) => (mother_occupation = asciiOnly(e.currentTarget.value))}
					placeholder="Optional"
				/>
				<p class="mt-0.5 text-[10px] text-ink/40">{ASCII_HINT}</p>
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

			<!-- Family Type -->
			<div>
				<BilingualLabel key="familyType" for="family_type_sel_n" />
				<Combobox id="family_type_sel_n" bind:value={family_type} options={FAMILY_TYPES} placeholder="Not specified" />
				{#if errors.family_type}<p class="mt-1 text-xs text-vermilion" data-error="true">
						{errors.family_type}
					</p>{/if}
			</div>

			<!-- Family Status -->
			<div>
				<BilingualLabel key="familyStatus" for="family_status" />
				<Combobox id="family_status" bind:value={family_status} options={FAMILY_STATUSES} placeholder="Select… (optional)" />
			</div>

			<!-- Family Values -->
			<div>
				<BilingualLabel key="familyValues" for="family_values" />
				<Combobox id="family_values" bind:value={family_values} options={FAMILY_VALUES_OPTS} placeholder="Select… (optional)" />
			</div>

			<!-- Native Place (optional) -->
			<div class="sm:col-span-2">
				<BilingualLabel key="nativePlace" for="native_place" />
				<input
					id="native_place"
					type="text"
					class="input"
					class:border-vermilion={errors.native_place}
					bind:value={native_place}
					oninput={(e) => (native_place = asciiOnly(e.currentTarget.value))}
					placeholder="Optional — village/town of origin"
				/>
				<p class="mt-0.5 text-xs text-ink/45">
					Village or town your family originally belongs to · <span lang={langStore.current}>{tx('hintNativePlace', langStore.current)}</span>
				</p>
				<p class="mt-0.5 text-[10px] text-ink/40">{ASCII_HINT}</p>
				{#if errors.native_place}<p class="mt-1 text-xs text-vermilion" data-error="true">
						{errors.native_place}
					</p>{/if}
			</div>
		</div>
	</details>

	<!-- ── Section: Lifestyle ────────────────────────────────────────────────── -->
	<details open class="card">
		<summary
			class="mb-1 flex cursor-pointer list-none items-center gap-2 font-serif text-xl font-semibold text-maroon"
		>
			<span class="text-tangerine">▸</span>
			<span
				class="mr-1 inline-flex h-6 w-6 items-center justify-center rounded-full bg-maroon/10 text-sm font-bold text-maroon"
			>6</span>
			Lifestyle
			<span class="ml-1 text-sm font-normal text-ink/50" lang={langStore.current}>{tx('secLifestyle', langStore.current)}</span>
		</summary>

		<div class="mt-4 space-y-4">
			<div class="grid gap-4 sm:grid-cols-3">
				<!-- Diet -->
				<div>
					<BilingualLabel key="diet" for="diet_sel_n" />
					<Combobox id="diet_sel_n" bind:value={diet} options={DIET_OPTS} placeholder="Select…" />
				</div>

				<!-- Smokes -->
				<div>
					<BilingualLabel key="smokes" for="smokes_sel_n" />
					<Combobox id="smokes_sel_n" bind:value={smokes} options={SMOKE_DRINK_OPTS} placeholder="Prefer not to say" />
				</div>

				<!-- Drinks -->
				<div>
					<BilingualLabel key="drinks" for="drinks_sel_n" />
					<Combobox id="drinks_sel_n" bind:value={drinks} options={SMOKE_DRINK_OPTS} placeholder="Prefer not to say" />
				</div>
			</div>

			<!-- Hobbies (optional textarea) -->
			<div>
				<BilingualLabel key="hobbies" for="hobbies" />
				<textarea
					id="hobbies"
					class="input min-h-[80px] resize-y"
					bind:value={hobbies}
					oninput={(e) => (hobbies = asciiOnly(e.currentTarget.value))}
					placeholder="Optional — e.g. Reading, Cricket, Cooking"
				></textarea>
				<p class="mt-0.5 text-[10px] text-ink/40">{ASCII_HINT}</p>
			</div>
		</div>
	</details>

	<!-- ── Section: Location ─────────────────────────────────────────────────── -->
	<details open class="card">
		<summary
			class="mb-1 flex cursor-pointer list-none items-center gap-2 font-serif text-xl font-semibold text-maroon"
		>
			<span class="text-tangerine">▸</span>
			<span
				class="mr-1 inline-flex h-6 w-6 items-center justify-center rounded-full bg-maroon/10 text-sm font-bold text-maroon"
			>7</span>
			Location
			<span class="ml-1 text-sm font-normal text-ink/50" lang={langStore.current}>{tx('secLocation', langStore.current)}</span>
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
					oninput={(e) => (city = asciiOnly(e.currentTarget.value))}
				/>
				<p class="mt-0.5 text-[10px] text-ink/40">{ASCII_HINT}</p>
				{#if errors.city}<p class="mt-1 text-xs text-vermilion" data-error="true">
						{errors.city}
					</p>{/if}
			</div>

			<!-- State -->
			<div>
				<BilingualLabel key="state" for="state_n" />
				<Combobox id="state_n" bind:value={state_field} options={INDIA_STATES} allowCustom={true} placeholder="Select state" />
			</div>

			<!-- Country -->
			<div>
				<BilingualLabel key="country" for="country_n" />
				<Combobox id="country_n" bind:value={country} options={COUNTRIES} placeholder="Select country" />
			</div>

			<!-- Pin Code (optional) -->
			<div>
				<label for="pin_code" class="label">
					<span class="block"
						>Pin Code <span class="text-xs font-normal text-ink/50">(optional)</span></span
					>
					<span class="block text-xs leading-tight font-normal" lang={langStore.current}>{tx('pinCode', langStore.current)}</span>
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
		</div>
	</details>

	<!-- ── Section: About ───────────────────────────────────────────────────── -->
	<details open class="card">
		<summary
			class="mb-1 flex cursor-pointer list-none items-center gap-2 font-serif text-xl font-semibold text-maroon"
		>
			<span class="text-tangerine">▸</span>
			<span
				class="mr-1 inline-flex h-6 w-6 items-center justify-center rounded-full bg-maroon/10 text-sm font-bold text-maroon"
			>8</span>
			About &amp; Expectations
			<span class="ml-1 text-sm font-normal text-ink/50" lang={langStore.current}>{tx('secAbout', langStore.current)}</span>
		</summary>

		<div class="mt-4 space-y-4">
			<!-- About Yourself -->
			<div>
				<BilingualLabel key="about" for="about" />
				<p class="mt-0.5 text-xs text-ink/45">Tell prospective families about yourself — your values, personality, lifestyle · <span lang={langStore.current}>{tx('hintAbout', langStore.current)}</span></p>
				<textarea
					id="about"
					class="input mt-1 min-h-[120px] resize-y"
					class:border-vermilion={errors.about}
					bind:value={about}
					oninput={(e) => (about = asciiOnly(e.currentTarget.value))}
					maxlength={500}
					placeholder="A short description about yourself, your family, and interests…"
				></textarea>
				<div class="mt-1 flex justify-between">
					{#if errors.about}
						<p class="text-xs text-vermilion" data-error="true">{errors.about}</p>
					{:else}
						<p class="text-[10px] text-ink/40">{ASCII_HINT}</p>
					{/if}
					<p class="text-xs text-ink/40">{about.length}/500</p>
				</div>
			</div>

			<!-- Partner Expectations -->
			<div>
				<BilingualLabel key="partnerExpectations" for="expectations" />
				<p class="mt-0.5 text-xs text-ink/45">Describe the qualities you're looking for in a partner · <span lang={langStore.current}>{tx('hintPartnerExpectations', langStore.current)}</span></p>
				<textarea
					id="expectations"
					class="input mt-1 min-h-[140px] resize-y"
					class:border-vermilion={errors.partner_expectations}
					bind:value={partner_expectations}
					oninput={(e) => (partner_expectations = asciiOnly(e.currentTarget.value))}
					maxlength={800}
					placeholder="Describe what you're looking for in a partner…"
				></textarea>
				<div class="mt-1 flex justify-between">
					{#if errors.partner_expectations}
						<p class="text-xs text-vermilion" data-error="true">{errors.partner_expectations}</p>
					{:else}
						<p class="text-[10px] text-ink/40">{ASCII_HINT}</p>
					{/if}
					<p class="text-xs text-ink/40">{partner_expectations.length}/800</p>
				</div>
			</div>
		</div>
	</details>

	<!-- ── Actions ──────────────────────────────────────────────────────────────
	     Equal-width row: each button gets flex-1. Min height 56px so labels
	     can wrap to two lines if narrow. Text scales sm→xs on small screens. -->
	<div class="border-t border-gold/30 pt-4 pb-8">
		{#if errors._photos}
			<p class="mb-2 w-full text-sm text-vermilion" data-error="true">{errors._photos}</p>
		{/if}
		{#if autoSave && autoSaveStatus !== 'idle'}
			<p class="mb-2 text-right text-xs text-ink/50">
				{#if autoSaveStatus === 'pending' || autoSaveStatus === 'saving'}Saving…{:else}Saved ✓{/if}
			</p>
		{/if}
		<div class="flex items-stretch gap-2">
			<a
				href="/dashboard"
				class="btn-secondary flex flex-1 flex-col items-center justify-center text-center leading-tight px-2 py-2 min-h-[56px] whitespace-normal"
			>
				<span class="text-xs sm:text-sm">{T.cancel.en}</span>
				<span lang={langStore.current} class="text-[10px] sm:text-xs opacity-90">{tx('cancel', langStore.current)}</span>
			</a>
			<button
				type="submit"
				class="btn-secondary flex flex-1 flex-col items-center justify-center text-center leading-tight px-2 py-2 min-h-[56px] whitespace-normal"
				disabled={submitting}
			>
				{#if submitting}
					<span class="text-xs sm:text-sm">Saving…</span>
				{:else}
					<span class="text-xs sm:text-sm">{T.save.en}</span>
					<span lang={langStore.current} class="text-[10px] sm:text-xs opacity-90">{tx('save', langStore.current)}</span>
				{/if}
			</button>
			{#if onSubmitForApproval && (profileStatus === 'draft' || profileStatus === 'rejected')}
				<button
					type="button"
					onclick={handleSubmitForApproval}
					class="btn-primary flex flex-1 flex-col items-center justify-center text-center leading-tight px-2 py-2 min-h-[56px] whitespace-normal"
					disabled={submittingForApproval}
				>
					{#if submittingForApproval}
						<span class="text-xs sm:text-sm">Submitting…</span>
					{:else}
						<span class="text-xs sm:text-sm">Submit for Approval</span>
						<span lang={langStore.current} class="text-[10px] sm:text-xs opacity-90">{tx('submitForApproval', langStore.current)}</span>
					{/if}
				</button>
			{/if}
		</div>
	</div>

{/if}
</form>
