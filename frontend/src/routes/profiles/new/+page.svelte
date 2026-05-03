<script lang="ts">
	import { profiles as profilesApi, type ProfilePayload } from '$lib/api';
	import { toastStore } from '$lib/stores/toast.svelte';
	import { ApiError } from '$lib/api';
	import { goto } from '$app/navigation';
	import ProfileForm from '$lib/components/ProfileForm.svelte';

	let submitting = $state(false);
	let serverErrors = $state<Record<string, string>>({});

	async function handleSubmit(data: Partial<ProfilePayload>) {
		submitting = true;
		serverErrors = {};
		try {
			const profile = await profilesApi.create(data);
			toastStore.success('Profile saved!');
			goto(`/profiles/${profile.id}/edit`);
		} catch (err) {
			if (err instanceof ApiError) {
				if (err.status === 401) {
					goto('/login');
					return;
				}
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
</script>

<svelte:head>
	<title>New Profile — Maratha Kalyanam</title>
</svelte:head>

<div class="mx-auto max-w-5xl px-4 py-10">
	<h1 class="font-serif text-3xl font-bold text-maroon">Create New Profile</h1>
	<p class="mt-1 text-sm text-ink/60">Fill in the details to create your matrimonial profile.</p>


	<div class="mt-6">
		<ProfileForm {submitting} {serverErrors} onSubmit={handleSubmit} />
	</div>
</div>
