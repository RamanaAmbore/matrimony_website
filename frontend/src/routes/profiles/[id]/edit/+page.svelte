<script lang="ts">
	import { onMount, untrack } from 'svelte';
	import { profiles as profilesApi, type Profile, type Photo, type ProfilePayload } from '$lib/api';
	import { ApiError } from '$lib/api';
	import { toastStore } from '$lib/stores/toast.svelte';
	import { goto } from '$app/navigation';
	import ProfileForm from '$lib/components/ProfileForm.svelte';
	import PhotoUpload from '$lib/components/PhotoUpload.svelte';
	import { Loader } from 'lucide-svelte';
	import { tx } from '$lib/i18n';
	import { langStore } from '$lib/stores/lang.svelte';

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

	// Admin/super are allowed to edit any profile, but the UX context is
	// different: their saves don't change the profile status, and the
	// "Submit for approval" button is meaningless to them. Compute these
	// once we have the profile loaded.
	let currentUser = $derived(data.user);
	let isOwner = $derived(profile && currentUser ? profile.owner_user_id === currentUser.uuid : false);
	let isAdminEditor = $derived(!isOwner && !!currentUser?.is_admin);

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
			// Non-owner non-admin viewers shouldn't even reach this route, but
			// if they do, send them somewhere sensible.
			goto(currentUser?.is_admin ? '/admin' : '/dashboard');
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
				Profile ID: <span class="font-mono text-xs bg-ink/5 px-1.5 py-0.5 rounded select-all">{profile.profile_number ?? profile.id.slice(0, 8)}</span>
				&nbsp;·&nbsp;Status:
				<span class="font-medium capitalize {profile.status === 'approved' ? 'text-green-600' : profile.status === 'revoked' ? 'text-vermilion' : 'text-saffron'}">
					{profile.status}
				</span>
			</p>
		</div>

		{#if isAdminEditor}
			<!-- Admin / super editing someone else's profile. The save behaviour
			     is intentionally different from owner saves: status is preserved
			     so the admin can fix typos, photos, etc. without un-approving
			     their own correction. -->
			<div class="mb-4 flex items-start gap-3 rounded-lg border border-maroon/40 bg-maroon/5 px-5 py-3">
				<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="mt-0.5 shrink-0 text-maroon" aria-hidden="true"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
				<div class="text-sm text-ink/80">
					<p class="font-semibold text-maroon">Editing as admin</p>
					<p>You are editing this profile on behalf of <span class="font-medium">{profile.first_name}</span>. Status and rejection state are preserved — your edits won't drop the profile back to pending.</p>
				</div>
			</div>
		{/if}

		<!-- Photos section — shown first so user sees it immediately. Admin can
		     also upload/delete; backend preserves status on admin-initiated CRUD. -->
		<PhotoUpload {profileId} initialPhotos={photos} isOwner={true} onCountChange={(n) => photoCount = n} />

		<p class="mt-4 mb-2 text-sm text-ink/60">
			{#if isAdminEditor}
				Upload, replace or delete photos as needed. Status will not change.
			{:else}
				Upload at least one photo before submitting for approval. Photos are blurred in public search results — clear version shared only after admin approves a contact request.
				<span class="block mt-0.5 text-xs" lang={langStore.current}>{tx('editPhotoPrivacyNote', langStore.current)}</span>
			{/if}
		</p>

		<div class="mt-6">
			<ProfileForm
				initialData={profile}
				{submitting}
				{serverErrors}
				onSubmit={handleSave}
				onSubmitForApproval={isAdminEditor ? undefined : submitForApproval}
				{submittingForApproval}
				profileStatus={profile.status}
				{photoCount}
				autoSave={false}
				isProd={data.siteInfo?.is_prod ?? true}
			/>
		</div>
	{/if}
</div>
