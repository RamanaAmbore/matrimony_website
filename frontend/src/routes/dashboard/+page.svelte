<script lang="ts">
	import { onMount } from 'svelte';
	import { profiles as profilesApi, type Profile } from '$lib/api';
	import { toastStore } from '$lib/stores/toast.svelte';
	import { ApiError } from '$lib/api';
	import { Plus, User, Edit, Loader, SendHorizonal } from 'lucide-svelte';
	import { goto } from '$app/navigation';
	import { T } from '$lib/i18n';

	let { data } = $props();

	let profileList = $state<Profile[]>([]);
	let loading = $state(true);
	let error = $state('');
	let submitting = $state<Record<string, boolean>>({});

	onMount(async () => {
		try {
			profileList = await profilesApi.list();
		} catch (err) {
			if (err instanceof ApiError && err.status === 401) {
				goto('/login');
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

	async function submitProfile(id: string) {
		submitting[id] = true;
		try {
			const updated = await profilesApi.submit(id);
			profileList = profileList.map(p => p.id === id ? updated : p);
			toastStore.success('Profile submitted for review!');
		} catch (err) {
			if (err instanceof ApiError) {
				toastStore.error(err.message.slice(0, 80));
			} else {
				toastStore.error('Submission failed. Try again.');
			}
		} finally {
			submitting[id] = false;
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
				<span class="ml-2" lang="te">{T.myProfiles.te}</span>
			</h1>
			<p class="mt-1 text-sm text-ink/60">Manage your matrimonial profiles</p>
		</div>
		{#if !data.user || data.user.is_approved}
			<a href="/profiles/new" class="btn-primary flex items-center gap-2">
				<Plus size={18} />
				New Profile
			</a>
		{:else}
			<button class="btn-primary flex items-center gap-2 opacity-50 cursor-not-allowed" disabled title="Account pending admin approval">
				<Plus size={18} />
				New Profile
			</button>
		{/if}
	</div>

	{#if data.user && data.user.email_verified && !data.user.is_approved}
		<div class="mt-4 flex items-start gap-3 rounded-lg border border-saffron/40 bg-saffron/10 px-5 py-4">
			<span class="mt-0.5 shrink-0 text-saffron" aria-hidden="true">
				<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
			</span>
			<p class="text-sm text-ink/80">
				<span class="font-semibold text-saffron">Account under review.</span>
				Your account is pending admin approval. You will be notified once approved and can create profiles.
			</p>
		</div>
	{/if}

	{#if data.user}
		<div class="mt-4 rounded-lg border border-gold/30 bg-white px-5 py-4 text-sm">
			<p class="font-medium text-maroon font-serif text-base mb-2">Account Details
				<span class="ml-1" lang="te">ఖాతా వివరాలు</span>
			</p>
			<div class="grid grid-cols-2 gap-x-6 gap-y-1 sm:grid-cols-4 text-ink/70">
				<div><span class="text-xs text-ink/50 block">Name</span>{data.user.full_name || '—'}</div>
				<div><span class="text-xs text-ink/50 block">User ID</span><span class="font-mono">{data.user.user_handle}</span></div>
				<div><span class="text-xs text-ink/50 block">Email</span>{data.user.email}</div>
				<div><span class="text-xs text-ink/50 block">Phone</span>{data.user.phone_number}</div>
			</div>
		</div>
	{/if}

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
			{#if !data.user || data.user.is_approved}
				<a href="/profiles/new" class="btn-primary mt-6 inline-flex items-center gap-2">
					<Plus size={18} />
					New Profile
				</a>
			{:else}
				<p class="mt-4 text-sm text-saffron font-medium">Your account is pending admin approval before you can create profiles.</p>
			{/if}
		</div>
	{:else}
		<div class="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
			{#each profileList as profile (profile.id)}
				<div
					class="card flex flex-col gap-3 cursor-pointer"
					role="link"
					tabindex="0"
					onclick={(e) => { if ((e.target as HTMLElement).closest('button, a')) return; goto(`/profiles/${profile.id}`); }}
					onkeydown={(e) => { if (e.key === 'Enter') goto(`/profiles/${profile.id}`); }}
				>
					<div class="flex items-start justify-between">
						<div>
							<h2 class="font-serif text-lg font-semibold text-maroon">
								{profile.first_name}{profile.surname_clan ? ` ${profile.surname_clan}` : ''}
							</h2>
							<p class="text-sm text-ink/60 capitalize">
								{profile.gender} · {calcAge(profile.dob)} yrs
							</p>
							<span class="font-mono text-[0.65rem] text-maroon/60">{profile.profile_number ?? '—'}</span>
						</div>
						{#if data.user?.is_admin}
							<a
								href="/admin/profiles?status={profile.status}"
								class="{statusClass(profile.status)} hover:opacity-80 transition-opacity"
								title="View in admin"
							>
								{statusLabel(profile.status)}
							</a>
						{:else}
							<span class={statusClass(profile.status)}>
								{statusLabel(profile.status)}
							</span>
						{/if}
					</div>

					<div class="text-sm text-ink/70 space-y-0.5">
						<p>{profile.occupation}</p>
						<p>{profile.city}, {profile.state}</p>
					</div>

					<p class="text-xs text-ink/50">
						{#if profile.status === 'draft'}
							Not yet submitted — complete your profile and submit for review.
						{:else if profile.status === 'pending'}
							Under admin review — you will be notified once approved.
						{:else if profile.status === 'approved'}
							Live in search results.
						{:else if profile.status === 'rejected'}
							Not approved — edit and resubmit, or contact admin.
						{/if}
					</p>

					<div class="flex flex-wrap gap-2 mt-auto pt-2 border-t border-gold/20">
						<a href="/profiles/{profile.id}" class="btn-secondary flex-1 text-center text-sm py-1.5">
							View
						</a>
						<a href="/profiles/{profile.id}/edit" class="btn-primary flex items-center justify-center gap-1 flex-1 text-sm py-1.5">
							<Edit size={14} />
							Edit
						</a>
						{#if profile.status === 'draft'}
							<button
								onclick={() => submitProfile(profile.id)}
								disabled={submitting[profile.id]}
								class="btn-secondary flex w-full items-center justify-center gap-1 text-sm py-1.5 border-saffron text-saffron hover:bg-saffron/10 disabled:opacity-50"
							>
								<SendHorizonal size={14} />
								{submitting[profile.id] ? 'Submitting…' : 'Submit'}
							</button>
						{/if}
					</div>
				</div>
			{/each}
		</div>
	{/if}
</div>
