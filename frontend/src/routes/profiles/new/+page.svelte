<script lang="ts">
	import { profiles as profilesApi, type Profile, type Photo, type ProfilePayload } from '$lib/api';
	import { toastStore } from '$lib/stores/toast.svelte';
	import { ApiError } from '$lib/api';
	import { goto } from '$app/navigation';
	import ProfileForm from '$lib/components/ProfileForm.svelte';
	import PhotoUpload from '$lib/components/PhotoUpload.svelte';
	import { Send } from 'lucide-svelte';

	let submitting = $state(false);
	let submittingForApproval = $state(false);
	let serverErrors = $state<Record<string, string>>({});

	// Set after first save — reveals photo upload inline
	let savedProfile = $state<Profile | null>(null);
	let photos = $state<Photo[]>([]);
	let photoCount = $state(0);

	async function handleSubmit(data: Partial<ProfilePayload>) {
		submitting = true;
		serverErrors = {};
		try {
			if (savedProfile) {
				// Already created — just update
				savedProfile = await profilesApi.update(savedProfile.id, data);
				toastStore.success('Profile updated!');
			} else {
				// First save — create and reveal photo upload
				savedProfile = await profilesApi.create(data);
				toastStore.success('Profile saved! Now upload your photos below.');
				// Scroll to photo section
				setTimeout(() => document.getElementById('photo-section')?.scrollIntoView({ behavior: 'smooth', block: 'start' }), 100);
			}
		} catch (err) {
			if (err instanceof ApiError) {
				if (err.status === 401) { goto('/login'); return; }
				if (err.status === 422) {
					toastStore.error('Please fix the errors below');
				} else {
					toastStore.error(err.message.slice(0, 60));
				}
			} else {
				toastStore.error('Save failed. Please try again.');
			}
		} finally {
			submitting = false;
		}
	}

	async function submitForApproval() {
		if (!savedProfile) return;
		submittingForApproval = true;
		try {
			savedProfile = await profilesApi.submit(savedProfile.id);
			toastStore.success('Profile submitted for review!');
			goto('/dashboard');
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
	<title>New Profile — Maratha Kalyanam</title>
</svelte:head>

<div class="mx-auto max-w-5xl px-4 py-10">
	<h1 class="font-serif text-3xl font-bold text-maroon">Create New Profile</h1>
	<p class="mt-1 text-sm text-ink/60">Fill in the details, upload photos, then submit for approval.</p>

	<!-- Profile ID + photo upload — appears after first save -->
	{#if savedProfile}
		<div class="mt-4 mb-2 rounded-lg border border-green-200 bg-green-50 px-4 py-3 text-sm text-green-800">
			Profile saved! &nbsp;ID: <span class="font-mono text-xs bg-green-100 px-1.5 py-0.5 rounded select-all">{savedProfile.id}</span>
			&nbsp;— Upload at least one photo below, then click <strong>Submit for Approval</strong>.
			<span class="block mt-0.5 text-xs text-green-700" lang="te">ప్రొఫైల్ సేవ్ అయింది! ఫోటో అప్‌లోడ్ చేసి సమర్పించండి.</span>
		</div>
		<div id="photo-section" class="mt-4">
			<PhotoUpload profileId={savedProfile.id} initialPhotos={photos} isOwner={true} onCountChange={(n) => photoCount = n} />
		</div>
	{/if}

	<div class="mt-6">
		<ProfileForm
			initialData={savedProfile ?? undefined}
			{submitting}
			{serverErrors}
			onSubmit={handleSubmit}
			onSubmitForApproval={savedProfile ? submitForApproval : undefined}
			{submittingForApproval}
			profileStatus={savedProfile?.status ?? 'draft'}
			{photoCount}
			autoSave={!!savedProfile}
		/>
	</div>
</div>
