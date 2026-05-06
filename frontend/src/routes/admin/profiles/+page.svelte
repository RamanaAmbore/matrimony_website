<script lang="ts">
	import { onMount } from 'svelte';
	import { admin as adminApi, type Profile } from '$lib/api';
	import { ApiError } from '$lib/api';
	import { toastStore } from '$lib/stores/toast.svelte';
	import { goto } from '$app/navigation';
	import { Loader, CheckCircle, XCircle, Eye, FileEdit, Clock } from 'lucide-svelte';
	import { page } from '$app/stores';
	import { tx } from '$lib/i18n';
	import { langStore } from '$lib/stores/lang.svelte';
	import ConfirmDelete from '$lib/components/ConfirmDelete.svelte';

	const validStatuses = ['pending', 'approved', 'rejected', 'draft'];
	const urlStatus = $page.url.searchParams.get('status') ?? '';
	let statusFilter = $state(validStatuses.includes(urlStatus) ? urlStatus : 'pending');
	let profileList = $state<Profile[]>([]);
	let loading = $state(true);
	let processingId = $state<string | null>(null);

	// ConfirmDelete modal state
	let deleteOpen = $state(false);
	let pendingDelete = $state<{ id: string; label: string } | null>(null);

	async function load() {
		loading = true;
		try {
			profileList = await adminApi.profiles.list(statusFilter);
		} catch (err) {
			if (err instanceof ApiError) {
				if (err.status === 401) { goto('/login'); return; }
				if (err.status === 403) { goto('/'); return; }
			}
			toastStore.error('Failed to load profiles');
		} finally {
			loading = false;
		}
	}

	onMount(load);

	$effect(() => {
		void statusFilter;
		load();
	});

	async function approve(id: string) {
		processingId = id;
		try {
			await adminApi.profiles.approve(id);
			profileList = profileList.filter((p) => p.id !== id);
			toastStore.success('Profile approved');
		} catch (err) {
			toastStore.error('Approval failed');
		} finally {
			processingId = null;
		}
	}

	function startReject(profile: Profile) {
		pendingDelete = {
			id: profile.id,
			label: `${profile.first_name} ${profile.last_name}`
		};
		deleteOpen = true;
	}

	async function doDelete() {
		if (!pendingDelete) return;
		processingId = pendingDelete.id;
		try {
			await adminApi.profiles.delete(pendingDelete.id);
			profileList = profileList.filter((p) => p.id !== pendingDelete!.id);
			toastStore.success('Profile rejected and removed');
		} catch {
			toastStore.error('Delete failed');
		} finally {
			processingId = null;
			pendingDelete = null;
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
	<title>Admin: Profiles — Maratha Kalyanam</title>
</svelte:head>

<ConfirmDelete
	bind:open={deleteOpen}
	title="Reject + delete profile?"
	description={`Reject and permanently remove ${pendingDelete?.label ?? 'this profile'} and all photos. Cannot be undone.`}
	onConfirm={doDelete}
/>

<div class="mx-auto max-w-6xl px-4 py-10">
	<div class="flex flex-wrap items-center justify-between gap-3 mb-2">
		<h1 class="font-serif text-3xl font-bold text-maroon">Profile Queue</h1>
		<a href="/admin" class="btn-secondary flex flex-col items-center justify-center text-center leading-tight text-sm px-3 py-1.5 min-h-[44px] whitespace-normal">
			<span>← Dashboard</span>
			<span lang={langStore.current} class="text-[10px] opacity-90">{tx('dashboardBack', langStore.current)}</span>
		</a>
	</div>

	<!-- Status filter tabs -->
	<div class="mt-4 flex gap-2 border-b border-gold/20 pb-0">
		{#each ['pending', 'approved', 'rejected', 'draft'] as s}
			<button
				onclick={() => (statusFilter = s)}
				class="px-4 py-2 text-sm font-medium border-b-2 transition-colors duration-150 -mb-px
					{statusFilter === s ? 'border-maroon text-maroon' : 'border-transparent text-ink/50 hover:text-ink'}"
			>
				{s.charAt(0).toUpperCase() + s.slice(1)}
			</button>
		{/each}
	</div>


	{#if loading}
		<div class="flex items-center justify-center py-20">
			<Loader size={36} class="animate-spin text-saffron" />
		</div>
	{:else if profileList.length === 0}
		<div class="py-16 text-center text-ink/60">No {statusFilter} profiles.</div>
	{:else}
		<div class="space-y-4 mt-4">
			{#each profileList as profile (profile.id)}
				<div class="card">
					<div class="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
						<div class="flex-1">
							<div class="flex flex-wrap items-center gap-2">
								<a
									href="/profiles/{profile.id}"
									class="font-serif text-xl font-semibold text-maroon hover:underline"
								>
									{profile.first_name} {profile.last_name}
								</a>
								<span class="badge badge-{profile.status === 'approved' ? 'approved' : profile.status === 'pending' ? 'pending' : profile.status === 'rejected' ? 'rejected' : 'draft'} inline-flex items-center gap-1 capitalize">
									{#if profile.status === 'draft'}<FileEdit size={12} class="-mt-0.5 inline-block" />
									{:else if profile.status === 'pending'}<Clock size={12} class="-mt-0.5 inline-block" />
									{:else if profile.status === 'approved'}<CheckCircle size={12} class="-mt-0.5 inline-block" />
									{:else if profile.status === 'rejected'}<XCircle size={12} class="-mt-0.5 inline-block" />
									{/if}
									{profile.status}
								</span>
							</div>
							<p class="mt-1 text-sm text-ink/60 capitalize">
								{profile.gender} · {calcAge(profile.dob)} yrs · {profile.city}, {profile.state}
							</p>
							<p class="text-sm text-ink/70">{profile.education} · {profile.occupation}</p>
							<p class="text-sm text-ink/60">
								Gotra: {profile.gotra} · Nakshatram: {profile.nakshatram} · Manglik: {profile.manglik}
							</p>
						</div>

						<div class="flex flex-wrap gap-2">
							<a
								href="/profiles/{profile.id}"
								class="btn-secondary flex flex-col items-center justify-center text-center leading-tight text-sm py-1.5 px-3 min-h-[44px] whitespace-normal"
							>
								<span class="flex items-center gap-1"><Eye size={13} />View</span>
								<span lang={langStore.current} class="text-[10px] opacity-90">{tx('view', langStore.current)}</span>
							</a>

							{#if profile.status === 'pending'}
								<button
									onclick={() => approve(profile.id)}
									disabled={processingId === profile.id}
									class="flex flex-col items-center justify-center text-center leading-tight rounded bg-green-600 px-3 py-1.5 min-h-[44px] text-sm text-white hover:bg-green-700 focus-visible:outline-2 focus-visible:outline-saffron disabled:opacity-60 whitespace-normal"
								>
									<span class="flex items-center gap-1"><CheckCircle size={13} />Approve</span>
									<span lang={langStore.current} class="text-[10px] opacity-90">{tx('approve', langStore.current)}</span>
								</button>
								<button
									onclick={() => startReject(profile)}
									disabled={processingId === profile.id}
									class="flex flex-col items-center justify-center text-center leading-tight rounded bg-vermilion px-3 py-1.5 min-h-[44px] text-sm text-white hover:bg-vermilion/80 focus-visible:outline-2 focus-visible:outline-saffron disabled:opacity-60 whitespace-normal"
								>
									<span class="flex items-center gap-1"><XCircle size={13} />Reject</span>
									<span lang={langStore.current} class="text-[10px] opacity-90">{tx('reject', langStore.current)}</span>
								</button>
							{/if}
						</div>
					</div>
				</div>
			{/each}
		</div>
	{/if}
</div>
