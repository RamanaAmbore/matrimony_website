<script lang="ts">
	import { onMount, untrack } from 'svelte';
	import { profiles as profilesApi, type Profile, type Photo } from '$lib/api';
	import { ApiError } from '$lib/api';
	import { toastStore } from '$lib/stores/toast.svelte';
	import { goto } from '$app/navigation';
	import { Loader, Edit, Send, SendHorizonal, User } from 'lucide-svelte';
	import Logo from '$lib/components/Logo.svelte';

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

	onMount(async () => {
		try {
			const result = await profilesApi.get(profileId);
			profile = result.profile;
			photos = result.photos;
			// Determine ownership from layout user data
			isOwner = data.user?.user_id === profile.owner_user_id;
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
				<!-- Photo -->
				<div class="aspect-[3/4] overflow-hidden rounded-xl border border-gold/20 shadow-sm bg-cream">
					{#if primaryPhoto}
						<img
							src={isOwner && primaryPhoto.passport_url ? primaryPhoto.passport_url : primaryPhoto.blurred_url}
							alt="{profile.first_name}'s photo"
							class="h-full w-full object-cover {!isOwner ? 'blur-sm' : ''}"
						/>
					{:else}
						<div class="flex h-full items-center justify-center text-gold/40">
							<User size={64} />
						</div>
					{/if}
				</div>

				<!-- Actions -->
				{#if isOwner}
					<a href="/profiles/{profileId}/edit" class="btn-primary flex w-full items-center justify-center gap-2">
						<Edit size={16} />
						Edit Profile
					</a>
					{#if profile.status === 'draft'}
						<button
							onclick={submitProfile}
							disabled={submitting}
							class="btn-secondary flex w-full items-center justify-center gap-2 disabled:opacity-50"
						>
							<SendHorizonal size={16} />
							{submitting ? 'Submitting…' : 'Submit for Approval'}
						</button>
					{:else if profile.status === 'pending'}
						<p class="text-center text-sm text-saffron font-medium">Under admin review</p>
					{/if}
				{:else if profile.status === 'approved'}
					{#if !showRequestForm}
						<button
							onclick={() => (showRequestForm = true)}
							class="btn-primary flex w-full items-center justify-center gap-2"
						>
							<Logo size="sm" />
							Request Full Details
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
									class="btn-secondary flex-1 py-2 text-sm"
								>
									Cancel
								</button>
								<button
									onclick={sendRequest}
									disabled={requesting}
									class="btn-primary flex flex-1 items-center justify-center gap-1 py-2 text-sm"
								>
									<Send size={14} />
									{requesting ? 'Sending…' : 'Send'}
								</button>
							</div>
						</div>
					{/if}
				{/if}

				<!-- Non-owner blur notice -->
				{#if !isOwner}
					<p class="mt-1 text-center text-xs text-ink/50">
						Photo is blurred for privacy. Full details shared via email after admin approval.
					</p>
				{/if}
			</div>

			<!-- Right: profile details -->
			<div>
				<div class="flex flex-wrap items-start justify-between gap-2">
					<div>
						<h1 class="font-serif text-3xl font-bold text-maroon">
							{profile.first_name} {profile.last_name}
						</h1>
						<p class="mt-1 text-ink/60">
							{calcAge(profile.dob)} years · {profile.height_cm} cm ·
							<span class="capitalize">{profile.gender}</span>
						</p>
					</div>
					<span
						class="badge capitalize {profile.status === 'approved'
							? 'badge-approved'
							: profile.status === 'pending'
								? 'badge-pending'
								: 'badge-draft'}"
					>
						{profile.status}
					</span>
				</div>


				<!-- Details grid -->
				<dl class="mt-4 grid grid-cols-2 gap-x-6 gap-y-4 text-sm sm:grid-cols-3">
					{#each [
						{ label: 'Education', value: profile.education },
						{ label: 'Occupation', value: profile.occupation },
						{ label: 'City', value: profile.city },
						{ label: 'State', value: profile.state },
						{ label: 'Country', value: profile.country },
						{ label: 'Nakshatram', value: profile.nakshatram },
						{ label: 'Rashi', value: profile.rashi },
						{ label: 'Gotra', value: profile.gotra },
						{ label: 'Kuldevata', value: profile.kuldevata },
						{ label: 'Devak', value: profile.devak },
						{ label: 'Manglik', value: profile.manglik },
						{ label: 'Diet', value: profile.diet },
						{ label: 'Mother Tongue', value: profile.mother_tongue },
						...(profile.annual_income_inr
							? [{ label: 'Annual Income', value: `₹${profile.annual_income_inr.toLocaleString('en-IN')}` }]
							: [])
					] as item}
						<div>
							<dt class="font-medium text-ink/50">{item.label}</dt>
							<dd class="mt-0.5 capitalize text-ink">{item.value ?? '—'}</dd>
						</div>
					{/each}
				</dl>

				{#if profile.about}
					<div class="mt-6">
						<h3 class="font-serif text-lg font-semibold text-maroon">About</h3>
						<p class="mt-2 leading-relaxed text-ink/80">{profile.about}</p>
					</div>
				{/if}

				{#if isOwner && profile.partner_expectations}
					<div class="mt-4">
						<h3 class="font-serif text-lg font-semibold text-maroon">Partner Expectations</h3>
						<p class="mt-2 leading-relaxed text-ink/80">{profile.partner_expectations}</p>
					</div>
				{/if}
			</div>
		</div>
	{/if}
</div>
