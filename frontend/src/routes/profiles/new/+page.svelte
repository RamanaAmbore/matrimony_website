<script lang="ts">
	import { profiles as profilesApi, type Profile, type ProfilePayload } from '$lib/api';
	import { toastStore } from '$lib/stores/toast.svelte';
	import { ApiError } from '$lib/api';
	import { goto } from '$app/navigation';
	import ProfileForm from '$lib/components/ProfileForm.svelte';

	let submitting = $state(false);
	let submittingForApproval = $state(false);
	let serverErrors = $state<Record<string, string>>({});

	// Set after first save — enables photo upload inside the wizard's step 9
	let savedProfile = $state<Profile | null>(null);

	async function handleSubmit(data: Partial<ProfilePayload>) {
		submitting = true;
		serverErrors = {};
		try {
			if (savedProfile) {
				// Already created — just update
				savedProfile = await profilesApi.update(savedProfile.id, data);
				toastStore.success('Profile updated!');
			} else {
				// First save — create and advance wizard to next step
				savedProfile = await profilesApi.create(data);
				toastStore.success('Profile saved! Continue to next step.');
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

	<!-- Profile ID — appears after first save -->
	{#if savedProfile}
		<p class="mt-1 text-sm text-ink/50">
			Profile ID: <span class="font-mono text-xs bg-ink/5 px-1.5 py-0.5 rounded select-all">{savedProfile.id}</span>
		</p>
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
			wizardMode={true}
			profileId={savedProfile?.id ?? ''}
			autoSave={false}
		/>
	</div>
</div>
