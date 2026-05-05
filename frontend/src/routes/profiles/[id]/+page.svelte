<script lang="ts">
	import { onMount, untrack } from 'svelte';
	import { profiles as profilesApi, type Profile, type Photo } from '$lib/api';
	import { ApiError } from '$lib/api';
	import { toastStore } from '$lib/stores/toast.svelte';
	import { goto } from '$app/navigation';
	import { Loader, Edit, Send, SendHorizonal, User, ZoomIn, ZoomOut, Maximize2, Eye, EyeOff, Ruler, Sparkles, GraduationCap, Users, Coffee, MapPin, MessageCircle, FileEdit, Clock, CheckCircle, XCircle } from 'lucide-svelte';

	const SECTION_ICONS = {
		basicInfo:  User,
		physical:   Ruler,
		astrology:  Sparkles,
		education:  GraduationCap,
		family:     Users,
		lifestyle:  Coffee,
		location:   MapPin,
		about:      MessageCircle
	};

	const STATUS_ICON = {
		draft:    FileEdit,
		pending:  Clock,
		approved: CheckCircle,
		rejected: XCircle
	};
	import Logo from '$lib/components/Logo.svelte';
	import { tx } from '$lib/i18n';
	import { langStore } from '$lib/stores/lang.svelte';

	let { data } = $props();
	// id is fixed for the lifetime of this page — route params don't change without navigation
	const profileId: string = untrack(() => data.id);

	let profile = $state<Profile | null>(null);
	let photos = $state<Photo[]>([]);
	let loading = $state(true);
	let submitting = $state(false);
	let requesting = $state(false);
	let requestMessage = $state('');
	let showRequestForm = $state(false);
	let isOwner = $state(false);
	let isAdmin = $state(false);

	// Bug 2: local state for the currently-displayed photo
	let displayedPhoto = $state<Photo | null>(null);
	// Admins can toggle between blurred (public-view) and clear (admin/owner)
	// to verify the privacy-blur looks right and the photo is appropriate.
	let adminPreviewBlurred = $state(false);
	let zoom = $state(1);
	const ZOOM_MIN = 1;
	const ZOOM_MAX = 4;
	const ZOOM_STEP = 0.5;
	function zoomIn() { zoom = Math.min(ZOOM_MAX, +(zoom + ZOOM_STEP).toFixed(2)); }
	function zoomOut() { zoom = Math.max(ZOOM_MIN, +(zoom - ZOOM_STEP).toFixed(2)); }
	function zoomReset() { zoom = 1; }

	onMount(async () => {
		try {
			const result = await profilesApi.get(profileId);
			profile = result.profile;
			photos = result.photos;
			// Determine ownership from layout user data
			isOwner = data.user?.user_id === profile.owner_user_id;
			isAdmin = data.user?.is_admin === true;
		} catch (err) {
			if (err instanceof ApiError) {
				if (err.status === 404) {
					toastStore.error('Profile not found');
				} else {
					toastStore.error('Failed to load profile');
				}
			}
			goto('/search');
		} finally {
			loading = false;
		}
	});

	function calcAge(dob: string): number {
		const birth = new Date(dob);
		const now = new Date();
		let age = now.getFullYear() - birth.getFullYear();
		if (
			now.getMonth() < birth.getMonth() ||
			(now.getMonth() === birth.getMonth() && now.getDate() < birth.getDate())
		) {
			age--;
		}
		return age;
	}

	function cmToFtIn(cm: number): string {
		const totalInches = cm / 2.54;
		const ft = Math.floor(totalInches / 12);
		const inches = Math.round(totalInches % 12);
		return `${ft}′${inches}″`;
	}

	// ── Enum → human-readable label ───────────────────────────────────────────

	function fmtMaritalStatus(v: string | null | undefined): string | null {
		if (!v) return null;
		const map: Record<string, string> = {
			never_married: 'Never Married',
			divorced: 'Divorced',
			widowed: 'Widowed',
			awaiting_divorce: 'Awaiting Divorce'
		};
		return map[v] ?? cap(v);
	}

	function fmtDiet(v: string | null | undefined): string | null {
		if (!v) return null;
		const map: Record<string, string> = {
			veg: 'Vegetarian',
			'non-veg': 'Non-Vegetarian',
			eggetarian: 'Eggetarian',
			jain: 'Jain',
			vegan: 'Vegan'
		};
		return map[v] ?? cap(v);
	}

	function fmtManglik(v: string | null | undefined): string | null {
		if (!v) return null;
		const map: Record<string, string> = {
			yes: 'Yes',
			no: 'No',
			partial: 'Partial',
			unknown: 'Unknown / Not checked'
		};
		return map[v] ?? cap(v);
	}

	function fmtBodyType(v: string | null | undefined): string | null {
		if (!v) return null;
		const map: Record<string, string> = {
			slim: 'Slim',
			average: 'Average',
			athletic: 'Athletic',
			heavy: 'Heavy'
		};
		return map[v] ?? cap(v);
	}

	function fmtComplexion(v: string | null | undefined): string | null {
		if (!v) return null;
		const map: Record<string, string> = {
			very_fair: 'Very Fair',
			fair: 'Fair',
			wheatish: 'Wheatish',
			dusky: 'Dusky',
			dark: 'Dark'
		};
		return map[v] ?? cap(v);
	}

	function fmtFamilyType(v: string | null | undefined): string | null {
		if (!v) return null;
		const map: Record<string, string> = {
			nuclear: 'Nuclear',
			joint: 'Joint'
		};
		return map[v] ?? cap(v);
	}

	function fmtFamilyStatus(v: string | null | undefined): string | null {
		if (!v) return null;
		const map: Record<string, string> = {
			middle_class: 'Middle Class',
			upper_middle: 'Upper Middle Class',
			affluent: 'Affluent',
			rich: 'Rich'
		};
		return map[v] ?? cap(v);
	}

	function fmtFamilyValues(v: string | null | undefined): string | null {
		if (!v) return null;
		const map: Record<string, string> = {
			orthodox: 'Orthodox',
			traditional: 'Traditional',
			moderate: 'Moderate',
			liberal: 'Liberal'
		};
		return map[v] ?? cap(v);
	}

	function fmtSmokeDrink(v: string | null | undefined): string | null {
		if (!v) return null;
		const map: Record<string, string> = {
			no: 'No',
			occasionally: 'Occasionally',
			yes: 'Yes'
		};
		return map[v] ?? cap(v);
	}

	function fmtIncome(v: number | null | undefined): string | null {
		if (v == null) return null;
		return `₹${v.toLocaleString('en-IN')}`;
	}

	/** Capitalise first letter, replace underscores with spaces. */
	function cap(v: string): string {
		return v.replace(/_/g, ' ').replace(/^\w/, (c) => c.toUpperCase());
	}

	/** Return null if value is null/undefined/empty-string, else the value itself. */
	function present<T>(v: T | null | undefined): T | null {
		if (v === null || v === undefined) return null;
		if (typeof v === 'string' && v.trim() === '') return null;
		return v;
	}

	async function submitProfile() {
		if (!profile) return;
		submitting = true;
		try {
			profile = await profilesApi.submit(profileId);
			toastStore.success('Profile submitted for review!');
		} catch (err) {
			if (err instanceof ApiError) {
				toastStore.error(err.message.slice(0, 80));
			} else {
				toastStore.error('Submission failed. Try again.');
			}
		} finally {
			submitting = false;
		}
	}

	async function sendRequest() {
		if (!profile) return;
		requesting = true;
		try {
			await profilesApi.requestDetails(profileId, requestMessage.trim() || undefined);
			toastStore.success('Request sent! Admin will review shortly.');
			showRequestForm = false;
		} catch (err) {
			if (err instanceof ApiError) {
				toastStore.error(err.message.slice(0, 60));
			} else {
				toastStore.error('Request failed. Try again.');
			}
		} finally {
			requesting = false;
		}
	}

	const primaryPhoto = $derived(photos.find((p) => p.is_primary) ?? photos[0] ?? null);

	// Whether the viewer should see the full data (owner or admin)
	const canSeeFull = $derived(isOwner || isAdmin);

	// Bug 2: keep displayedPhoto in sync with primaryPhoto on first load;
	// user clicks on a thumbnail to override it.
	$effect(() => {
		displayedPhoto = primaryPhoto;
	});

	// Effective "should we show the clear version" — admin can choose to
	// preview the blurred version even though they're allowed the clear one.
	const showClear = $derived(canSeeFull && !(isAdmin && adminPreviewBlurred));

	/** URL to show for a given photo depending on viewer permissions. */
	function photoSrc(p: Photo): string {
		return showClear && p.passport_url ? p.passport_url : p.blurred_url;
	}
</script>

<svelte:head>
	<title>{profile ? `${profile.first_name} ${profile.last_name}` : 'Profile'} — Maratha Kalyanam</title>
</svelte:head>

<div class="mx-auto max-w-4xl px-4 py-10">
	{#if loading}
		<div class="flex items-center justify-center py-24">
			<Loader size={40} class="animate-spin text-saffron" />
		</div>
	{:else if profile}
		<div class="grid gap-8 lg:grid-cols-[280px,1fr]">
			<!-- Left: photo + quick actions -->
			<div class="space-y-4">
				<!-- Main photo viewer — scrollable container with zoom -->
				<div class="relative aspect-[3/4] overflow-auto rounded-xl border border-gold/20 shadow-sm bg-cream">
					{#if displayedPhoto}
						<img
							src={photoSrc(displayedPhoto)}
							alt="{profile.first_name}'s photo"
							class="h-full w-full object-cover {!showClear ? 'blur-sm' : ''}"
							style="transform: scale({zoom}); transform-origin: top left; min-width: 100%; min-height: 100%;"
							loading="lazy"
							decoding="async"
						/>
					{:else}
						<div class="flex h-full items-center justify-center text-gold/40">
							<User size={64} />
						</div>
					{/if}
				</div>

				<!-- Zoom + (admin-only) blur-preview controls -->
				{#if displayedPhoto}
					<div class="flex items-center justify-center gap-1.5">
						<button type="button" onclick={zoomOut} disabled={zoom <= ZOOM_MIN}
							class="rounded border border-gold/40 bg-white p-1.5 text-maroon hover:border-saffron disabled:opacity-40 disabled:cursor-not-allowed"
							aria-label="Zoom out">
							<ZoomOut size={14} />
						</button>
						<button type="button" onclick={zoomReset}
							class="rounded border border-gold/40 bg-white px-2 py-1 text-xs font-mono text-maroon hover:border-saffron min-w-[52px]"
							aria-label="Reset zoom">{Math.round(zoom * 100)}%</button>
						<button type="button" onclick={zoomIn} disabled={zoom >= ZOOM_MAX}
							class="rounded border border-gold/40 bg-white p-1.5 text-maroon hover:border-saffron disabled:opacity-40 disabled:cursor-not-allowed"
							aria-label="Zoom in">
							<ZoomIn size={14} />
						</button>
						{#if isAdmin && !isOwner}
							<button type="button" onclick={() => (adminPreviewBlurred = !adminPreviewBlurred)}
								class="ml-1 rounded border border-gold/40 bg-white p-1.5 text-maroon hover:border-saffron"
								aria-label={adminPreviewBlurred ? 'Show clear photo' : 'Preview blurred (public) view'}
								title={adminPreviewBlurred ? 'Showing public blurred view — click for clear' : 'Showing clear photo — click to preview public blurred view'}>
								{#if adminPreviewBlurred}
									<EyeOff size={14} />
								{:else}
									<Eye size={14} />
								{/if}
							</button>
						{/if}
					</div>
					{#if isAdmin && adminPreviewBlurred}
						<p class="text-center text-xs text-saffron font-medium">Public (blurred) preview</p>
					{/if}
				{/if}

				<!-- Thumbnail strip — only when there are multiple photos -->
				{#if photos.length > 1}
					<div class="flex gap-1.5 mt-2 overflow-x-auto pb-1">
						{#each photos as p (p.id)}
							<button
								type="button"
								onclick={() => (displayedPhoto = p)}
								class="shrink-0 h-14 w-11 overflow-hidden rounded border-2 transition-all
									{displayedPhoto?.id === p.id
										? 'border-saffron'
										: 'border-gold/20 hover:border-gold/50'}"
								aria-label="View photo"
							>
								<img
									src={p.thumb_url ?? photoSrc(p)}
									alt=""
									class="h-full w-full object-cover {!showClear ? 'blur-sm' : ''}"
									loading="lazy"
									decoding="async"
								/>
							</button>
						{/each}
					</div>
				{/if}

				<!-- Actions -->
				{#if isOwner}
					<a href="/profiles/{profileId}/edit" class="btn-primary flex flex-col w-full items-center justify-center text-center leading-tight py-2 min-h-[52px] whitespace-normal">
						<span class="flex items-center gap-1.5 text-sm"><Edit size={15} />Edit Profile</span>
						<span lang={langStore.current} class="text-[10px] opacity-90">{tx('editProfile', langStore.current)}</span>
					</a>
					{#if profile.status === 'draft'}
						<button
							onclick={submitProfile}
							disabled={submitting}
							class="btn-secondary flex flex-col w-full items-center justify-center text-center leading-tight py-2 min-h-[52px] whitespace-normal disabled:opacity-50"
						>
							<span class="flex items-center gap-1.5 text-sm"><SendHorizonal size={15} />{submitting ? 'Submitting…' : 'Submit for Approval'}</span>
							<span lang={langStore.current} class="text-[10px] opacity-90">{tx('submitForApproval', langStore.current)}</span>
						</button>
					{:else if profile.status === 'pending'}
						<p class="text-center text-sm text-saffron font-medium">Under admin review</p>
					{/if}
				{:else if profile.status === 'approved'}
					{#if !showRequestForm}
						<button
							onclick={() => (showRequestForm = true)}
							class="btn-primary flex flex-col w-full items-center justify-center text-center leading-tight py-2 min-h-[52px] whitespace-normal"
						>
							<span class="flex items-center gap-1.5 text-sm"><Logo size="sm" />Request Full Details</span>
							<span lang={langStore.current} class="text-[10px] opacity-90">{tx('requestDetails', langStore.current)}</span>
						</button>
					{:else}
						<div class="card space-y-3">
							<p class="text-sm font-medium text-maroon">Send a message (optional)</p>
							<textarea
								bind:value={requestMessage}
								class="input resize-none"
								rows="3"
								maxlength="300"
								placeholder="Introduce yourself briefly…"
							></textarea>
							<div class="flex gap-2">
								<button
									onclick={() => (showRequestForm = false)}
									class="btn-secondary flex flex-col flex-1 items-center justify-center text-center leading-tight py-2 min-h-[44px] whitespace-normal"
								>
									<span class="text-sm">Cancel</span>
									<span lang={langStore.current} class="text-[10px] opacity-90">{tx('cancel', langStore.current)}</span>
								</button>
								<button
									onclick={sendRequest}
									disabled={requesting}
									class="btn-primary flex flex-col flex-1 items-center justify-center text-center leading-tight py-2 min-h-[44px] whitespace-normal"
								>
									<span class="flex items-center gap-1 text-sm"><Send size={13} />{requesting ? 'Sending…' : 'Send'}</span>
									<span lang={langStore.current} class="text-[10px] opacity-90">{tx('send', langStore.current)}</span>
								</button>
							</div>
						</div>
					{/if}
				{/if}

				<!-- Non-owner, non-admin blur notice -->
				{#if !canSeeFull}
					<p class="mt-1 text-center text-xs text-ink/50">
						Photo is blurred for privacy. Full details shared via email after admin approval.
					</p>
				{/if}
			</div>

			<!-- Right: profile details -->
			<div class="space-y-6">
				<!-- Header -->
				<div class="flex flex-wrap items-start justify-between gap-2">
					<div>
						<h1 class="font-serif text-3xl font-bold text-maroon">
							{profile.first_name} {profile.last_name}
						</h1>
						<p class="mt-1 text-ink/60">
							{calcAge(profile.dob)} yrs · {profile.height_cm} cm ({cmToFtIn(profile.height_cm)}) ·
							<span class="capitalize">{profile.gender}</span>
						</p>
						{#if profile.profile_number}
							<p class="mt-0.5 font-mono text-xs text-ink/40">#{profile.profile_number}</p>
						{/if}
					</div>
					<span
						class="badge inline-flex items-center gap-1 capitalize {profile.status === 'approved'
							? 'badge-approved'
							: profile.status === 'pending'
								? 'badge-pending'
								: profile.status === 'rejected'
									? 'badge-rejected'
									: 'badge-draft'}"
					>
						{#if profile.status === 'draft'}
							<FileEdit size={12} class="-mt-0.5 inline-block" />
						{:else if profile.status === 'pending'}
							<Clock size={12} class="-mt-0.5 inline-block" />
						{:else if profile.status === 'approved'}
							<CheckCircle size={12} class="-mt-0.5 inline-block" />
						{:else if profile.status === 'rejected'}
							<XCircle size={12} class="-mt-0.5 inline-block" />
						{/if}
						{profile.status}
					</span>
				</div>

				<!-- ── Basic Information ─────────────────────────────────────────── -->
				<section class="rounded-xl border border-gold/30 bg-white p-5 shadow-sm">
					<h2 class="font-serif text-xl font-semibold text-maroon mb-3 flex items-center gap-2"><SECTION_ICONS.basicInfo size={18} />Basic Information</h2>
					<dl class="space-y-2 text-sm">
						{#each [
							{ label: 'Marital Status', value: fmtMaritalStatus(profile.marital_status) },
							{ label: 'Mother Tongue', value: present(profile.mother_tongue) },
							{ label: 'Surname / Clan', value: present(profile.surname_clan) },
							{ label: 'Caste', value: present(profile.caste) },
							{ label: 'Sub Caste', value: present(profile.sub_caste) },
						].filter(item => item.value !== null) as item}
							<div class="flex items-baseline gap-3 border-b border-gold/10 pb-1.5">
								<dt class="w-40 shrink-0 font-medium text-ink/50">{item.label}</dt>
								<dd class="flex-1 text-ink">{item.value}</dd>
							</div>
						{/each}
					</dl>
				</section>

				<!-- ── Physical ────────────────────────────────────────────────────── -->
				<section class="rounded-xl border border-gold/30 bg-white p-5 shadow-sm">
					<h2 class="font-serif text-xl font-semibold text-maroon mb-3 flex items-center gap-2"><SECTION_ICONS.physical size={18} />Physical</h2>
					<dl class="space-y-2 text-sm">
						{#each [
							{ label: 'Height', value: profile.height_cm ? `${profile.height_cm} cm (${cmToFtIn(profile.height_cm)})` : null },
							{ label: 'Weight', value: profile.weight_kg ? `${profile.weight_kg} kg` : null },
							{ label: 'Complexion', value: fmtComplexion(profile.complexion) },
							{ label: 'Body Type', value: fmtBodyType(profile.body_type) },
							{ label: 'Blood Group', value: present(profile.blood_group) },
						].filter(item => item.value !== null) as item}
							<div class="flex items-baseline gap-3 border-b border-gold/10 pb-1.5">
								<dt class="w-40 shrink-0 font-medium text-ink/50">{item.label}</dt>
								<dd class="flex-1 text-ink">{item.value}</dd>
							</div>
						{/each}
					</dl>
				</section>

				<!-- ── Astrology ───────────────────────────────────────────────────── -->
				<section class="rounded-xl border border-gold/30 bg-white p-5 shadow-sm">
					<h2 class="font-serif text-xl font-semibold text-maroon mb-3 flex items-center gap-2"><SECTION_ICONS.astrology size={18} />Astrology</h2>
					<dl class="space-y-2 text-sm">
						{#each [
							{ label: 'Gotra', value: present(profile.gotra) },
							{ label: 'Kuldevata', value: present(profile.kuldevata) },
							{ label: 'Devak', value: present(profile.devak) },
							{ label: 'Nakshatram', value: present(profile.nakshatram) },
							{ label: 'Rashi', value: present(profile.rashi) },
							{ label: 'Manglik', value: fmtManglik(profile.manglik) },
							{ label: 'Time of Birth', value: present(profile.time_of_birth) },
							{ label: 'Place of Birth', value: present(profile.place_of_birth) },
						].filter(item => item.value !== null) as item}
							<div class="flex items-baseline gap-3 border-b border-gold/10 pb-1.5">
								<dt class="w-40 shrink-0 font-medium text-ink/50">{item.label}</dt>
								<dd class="flex-1 text-ink">{item.value}</dd>
							</div>
						{/each}
					</dl>
				</section>

				<!-- ── Education & Career ──────────────────────────────────────────── -->
				<section class="rounded-xl border border-gold/30 bg-white p-5 shadow-sm">
					<h2 class="font-serif text-xl font-semibold text-maroon mb-3 flex items-center gap-2"><SECTION_ICONS.education size={18} />Education &amp; Career</h2>
					<dl class="space-y-2 text-sm">
						{#each [
							{ label: 'Education', value: present(profile.education) },
							{ label: 'College / University', value: present(profile.college_university) },
							{ label: 'Occupation', value: present(profile.occupation) },
							{ label: 'Employer', value: present(profile.employer) },
							{ label: 'Work Location', value: present(profile.work_location) },
							{ label: 'Annual Income', value: fmtIncome(profile.annual_income_inr) },
						].filter(item => item.value !== null) as item}
							<div class="flex items-baseline gap-3 border-b border-gold/10 pb-1.5">
								<dt class="w-40 shrink-0 font-medium text-ink/50">{item.label}</dt>
								<dd class="flex-1 text-ink tabular-nums">{item.value}</dd>
							</div>
						{/each}
					</dl>
				</section>

				<!-- ── Location ────────────────────────────────────────────────────── -->
				<section class="rounded-xl border border-gold/30 bg-white p-5 shadow-sm">
					<h2 class="font-serif text-xl font-semibold text-maroon mb-3 flex items-center gap-2"><SECTION_ICONS.location size={18} />Location</h2>
					<dl class="space-y-2 text-sm">
						{#each [
							{ label: 'City', value: present(profile.city) },
							{ label: 'State', value: present(profile.state) },
							{ label: 'Country', value: present(profile.country) },
							{ label: 'PIN Code', value: present(profile.pin_code) },
						].filter(item => item.value !== null) as item}
							<div class="flex items-baseline gap-3 border-b border-gold/10 pb-1.5">
								<dt class="w-40 shrink-0 font-medium text-ink/50">{item.label}</dt>
								<dd class="flex-1 text-ink">{item.value}</dd>
							</div>
						{/each}
					</dl>
				</section>

				<!-- ── Family ──────────────────────────────────────────────────────── -->
				{#if canSeeFull}
					<section class="rounded-xl border border-gold/30 bg-white p-5 shadow-sm">
						<h2 class="font-serif text-xl font-semibold text-maroon mb-3 flex items-center gap-2"><SECTION_ICONS.family size={18} />Family</h2>
						<dl class="space-y-2 text-sm">
							{#each [
								{ label: "Father's Name", value: present(profile.father_name) },
								{ label: "Father's Occupation", value: present(profile.father_occupation) },
								{ label: "Mother's Name", value: present(profile.mother_name) },
								{ label: "Mother's Occupation", value: present(profile.mother_occupation) },
								{ label: 'Family Type', value: fmtFamilyType(profile.family_type) },
								{ label: 'Family Status', value: fmtFamilyStatus(profile.family_status) },
								{ label: 'Family Values', value: fmtFamilyValues(profile.family_values) },
								{ label: 'Native Place', value: present(profile.native_place) },
								{ label: 'No. of Family Members', value: profile.num_family_members != null ? String(profile.num_family_members) : null },
								{ label: 'Brothers', value: profile.num_brothers != null ? String(profile.num_brothers) : null },
								{ label: 'Brothers Married', value: profile.num_brothers_married != null ? String(profile.num_brothers_married) : null },
								{ label: 'Sisters', value: profile.num_sisters != null ? String(profile.num_sisters) : null },
								{ label: 'Sisters Married', value: profile.num_sisters_married != null ? String(profile.num_sisters_married) : null },
							].filter(item => item.value !== null) as item}
								<div class="flex items-baseline gap-3 border-b border-gold/10 pb-1.5">
									<dt class="w-40 shrink-0 font-medium text-ink/50">{item.label}</dt>
									<dd class="flex-1 text-ink">{item.value}</dd>
								</div>
							{/each}
						</dl>
					</section>
				{/if}

				<!-- ── Lifestyle ───────────────────────────────────────────────────── -->
				<section class="rounded-xl border border-gold/30 bg-white p-5 shadow-sm">
					<h2 class="font-serif text-xl font-semibold text-maroon mb-3 flex items-center gap-2"><SECTION_ICONS.lifestyle size={18} />Lifestyle</h2>
					<dl class="space-y-2 text-sm">
						{#each [
							{ label: 'Diet', value: fmtDiet(profile.diet) },
							{ label: 'Smokes', value: fmtSmokeDrink(profile.smokes) },
							{ label: 'Drinks', value: fmtSmokeDrink(profile.drinks) },
							{ label: 'Hobbies', value: present(profile.hobbies) },
						].filter(item => item.value !== null) as item}
							<div class="flex items-baseline gap-3 border-b border-gold/10 pb-1.5">
								<dt class="w-40 shrink-0 font-medium text-ink/50">{item.label}</dt>
								<dd class="flex-1 text-ink">{item.value}</dd>
							</div>
						{/each}
					</dl>
				</section>

				<!-- ── About ───────────────────────────────────────────────────────── -->
				{#if profile.about}
					<section class="rounded-xl border border-gold/30 bg-white p-5 shadow-sm">
						<h2 class="font-serif text-xl font-semibold text-maroon mb-2 flex items-center gap-2"><SECTION_ICONS.about size={18} />About</h2>
						<p class="leading-relaxed text-ink/80 text-sm">{profile.about}</p>
					</section>
				{/if}

				<!-- ── Partner Expectations (owner-only) ──────────────────────────── -->
				{#if canSeeFull && profile.partner_expectations}
					<section class="rounded-xl border border-gold/30 bg-white p-5 shadow-sm">
						<h2 class="font-serif text-xl font-semibold text-maroon mb-2 flex items-center gap-2"><SECTION_ICONS.about size={18} />Partner Expectations</h2>
						<p class="leading-relaxed text-ink/80 text-sm">{profile.partner_expectations}</p>
					</section>
				{/if}
			</div>
		</div>
	{/if}
</div>
