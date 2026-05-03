<script lang="ts">
	import { onMount } from 'svelte';
	import { profiles as profilesApi, type Profile } from '$lib/api';
	import { toastStore } from '$lib/stores/toast.svelte';
	import { ApiError } from '$lib/api';
	import { Plus, User, Edit, Loader } from 'lucide-svelte';
	import { T } from '$lib/i18n';

	let profileList = $state<Profile[]>([]);
	let loading = $state(true);
	let error = $state('');

	onMount(async () => {
		try {
			profileList = await profilesApi.list();
		} catch (err) {
			if (err instanceof ApiError && err.status === 401) {
				window.location.href = '/login';
				return;
			}
			error = 'Failed to load profiles.';
		} finally {
			loading = false;
		}
	});

	function statusClass(status: Profile['status']) {
		switch (status) {
			case 'approved': return 'badge-approved';
			case 'pending': return 'badge-pending';
			case 'rejected': return 'badge-rejected';
			default: return 'badge-draft';
		}
	}

	function statusLabel(status: Profile['status']) {
		switch (status) {
			case 'approved': return 'Approved';
			case 'pending': return 'Under Review';
			case 'rejected': return 'Rejected';
			default: return 'Draft';
		}
	}

	function calcAge(dob: string): number {
		const birth = new Date(dob);
		const now = new Date();
		let age = now.getFullYear() - birth.getFullYear();
		if (now.getMonth() < birth.getMonth() || (now.getMonth() === birth.getMonth() && now.getDate() < birth.getDate())) {
			age--;
		}
		return age;
	}
</script>

<svelte:head>
	<title>My Profiles — Maratha Kalyanam</title>
</svelte:head>

<div class="mx-auto max-w-5xl px-4 py-10">
	<div class="flex items-center justify-between">
		<div>
			<h1 class="font-serif text-3xl font-bold text-maroon">
				{T.myProfiles.en}
				<span class="ml-2 text-xl font-normal" lang="te">{T.myProfiles.te}</span>
			</h1>
			<p class="mt-1 text-sm text-ink/60">Manage your matrimonial profiles</p>
		</div>
		<a href="/profiles/new" class="btn-primary flex items-center gap-2">
			<Plus size={18} />
			New Profile
		</a>
	</div>


	{#if loading}
		<div class="flex items-center justify-center py-20">
			<Loader size={36} class="animate-spin text-tangerine" />
		</div>
	{:else if error}
		<div class="rounded-lg border border-vermilion/30 bg-vermilion/5 p-4 text-vermilion">
			{error}
		</div>
	{:else if profileList.length === 0}
		<div class="py-16 text-center">
			<!-- Decorative empty-state kalasha-ish circle -->
			<div class="mx-auto mb-4 flex h-20 w-20 items-center justify-center rounded-full bg-cream/60 border-2 border-gold/30">
				<User size={40} class="text-gold/50" />
			</div>
			<h2 class="mt-2 font-serif text-xl font-semibold text-maroon">No profiles yet</h2>
			<p class="mt-2 text-ink/60">Create your first profile to start appearing in search results.</p>
			<a href="/profiles/new" class="btn-primary mt-6 inline-flex items-center gap-2">
				<Plus size={18} />
				New Profile
			</a>
		</div>
	{:else}
		<div class="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
			{#each profileList as profile (profile.id)}
				<div class="card flex flex-col gap-3">
					<div class="flex items-start justify-between">
						<div>
							<h2 class="font-serif text-lg font-semibold text-maroon">
								{profile.first_name} {profile.last_name}
							</h2>
							<p class="text-sm text-ink/60 capitalize">
								{profile.gender} · {calcAge(profile.dob)} yrs
							</p>
							<span class="font-mono text-[0.65rem] text-maroon/60">MC-{profile.id.replace(/-/g, '').slice(0, 5).toUpperCase()}</span>
						</div>
						<span class={statusClass(profile.status)}>
							{statusLabel(profile.status)}
						</span>
					</div>

					<div class="text-sm text-ink/70 space-y-0.5">
						<p>{profile.occupation}</p>
						<p>{profile.city}, {profile.state}</p>
						{#if profile.status === 'rejected'}
							<p class="mt-1 text-vermilion text-xs">
								Reason may be in the rejection notes — contact admin.
							</p>
						{/if}
					</div>

					<div class="flex gap-2 mt-auto pt-2 border-t border-gold/20">
						<a href="/profiles/{profile.id}" class="btn-secondary flex-1 text-center text-sm py-1.5">
							View
						</a>
						<a href="/profiles/{profile.id}/edit" class="btn-primary flex items-center justify-center gap-1 flex-1 text-sm py-1.5">
							<Edit size={14} />
							Edit
						</a>
					</div>
				</div>
			{/each}
		</div>
	{/if}
</div>
