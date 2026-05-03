<script lang="ts">
	import { onMount, untrack } from 'svelte';
	import { profiles as profilesApi, type Profile, type Photo, type ProfilePayload } from '$lib/api';
	import { ApiError } from '$lib/api';
	import { toastStore } from '$lib/stores/toast.svelte';
	import { goto } from '$app/navigation';
	import ProfileForm from '$lib/components/ProfileForm.svelte';
	import PhotoUpload from '$lib/components/PhotoUpload.svelte';
	import { Loader } from 'lucide-svelte';

	let { data } = $props();
	// id is fixed for the lifetime of this page — route params don't change without navigation
	const profileId: string = untrack(() => data.id);

	let profile = $state<Profile | null>(null);
	let photos = $state<Photo[]>([]);
	let photoCount = $state(0);
	let loading = $state(true);
	let submitting = $state(false);
	let submittingForApproval = $state(false);
	let serverErrors = $state<Record<string, string>>({});

	onMount(async () => {
		try {
			const result = await profilesApi.get(profileId);
			profile = result.profile;
			photos = result.photos;
		} catch (err) {
			if (err instanceof ApiError && err.status === 401) {
				goto('/login');
				return;
			}
			toastStore.error('Failed to load profile');
			goto('/dashboard');
		} finally {
			loading = false;
		}
	});

	async function handleSave(formData: Partial<ProfilePayload>) {
		if (!profile) return;
		submitting = true;
		serverErrors = {};
		try {
			profile = await profilesApi.update(profileId, formData);
			toastStore.success('Profile updated!');
		} catch (err) {
			if (err instanceof ApiError) {
				if (err.status === 422) {
					toastStore.error('Please fix the errors below');
				} else {
					toastStore.error(err.message.slice(0, 60));
				}
			} else {
				toastStore.error('Update failed. Try again.');
			}
		} finally {
			submitting = false;
		}
	}

	async function submitForApproval() {
		if (!profile) return;
		submittingForApproval = true;
		try {
			profile = await profilesApi.submit(profileId);
			toastStore.success('Profile submitted for review!');
		} catch (err) {
			if (err instanceof ApiError) {
				toastStore.error(err.message.slice(0, 60));
			} else {
				toastStore.error('Submission failed. Try again.');
			}
		} finally {
			submittingForApproval = false;
		}
	}
</script>

<svelte:head>
	<title>Edit Profile — Maratha Kalyanam</title>
</svelte:head>

<div class="mx-auto max-w-5xl px-4 py-10">
	{#if loading}
		<div class="flex items-center justify-center py-24">
			<Loader size={40} class="animate-spin text-saffron" />
		</div>
	{:else if profile}
		<div class="mb-4">
			<h1 class="font-serif text-3xl font-bold text-maroon">
				Edit Profile — {profile.first_name}{profile.surname_clan ? ` ${profile.surname_clan}` : ''}
			</h1>
			<p class="mt-1 text-sm text-ink/60">
				Profile ID: <span class="font-mono text-xs bg-ink/5 px-1.5 py-0.5 rounded select-all">{profile.id}</span>
				&nbsp;·&nbsp;Status:
				<span class="font-medium capitalize {profile.status === 'approved' ? 'text-green-600' : profile.status === 'rejected' ? 'text-vermilion' : 'text-saffron'}">
					{profile.status}
				</span>
			</p>
		</div>

		<!-- Photos section — shown first so user sees it immediately -->
		<PhotoUpload {profileId} initialPhotos={photos} isOwner={true} onCountChange={(n) => photoCount = n} />

		<p class="mt-4 mb-2 text-sm text-ink/60">
			Upload at least one photo before submitting for approval. Photos are blurred in public search results — clear version shared only after admin approves a contact request.
			<span class="block mt-0.5 text-xs" lang="te">అనుమతి తర్వాతే స్పష్టమైన ఫోటో అందుతుంది.</span>
		</p>

		<div class="mt-6">
			<ProfileForm
				initialData={profile}
				{submitting}
				{serverErrors}
				onSubmit={handleSave}
				onSubmitForApproval={submitForApproval}
				{submittingForApproval}
				profileStatus={profile.status}
				{photoCount}
				autoSave={true}
			/>
		</div>
	{/if}
</div>
