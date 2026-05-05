<script lang="ts">
	import { onMount } from 'svelte';
	import { requests as requestsApi, type DetailRequest } from '$lib/api';
	import { ApiError } from '$lib/api';
	import { goto } from '$app/navigation';
	import { Loader, Inbox } from 'lucide-svelte';
	import { T, tx } from '$lib/i18n';
	import { langStore } from '$lib/stores/lang.svelte';

	let requestList = $state<DetailRequest[]>([]);
	let loading = $state(true);
	let error = $state('');

	onMount(async () => {
		try {
			requestList = await requestsApi.mine();
		} catch (err) {
			if (err instanceof ApiError && err.status === 401) {
				goto('/login');
				return;
			}
			error = 'Failed to load requests.';
		} finally {
			loading = false;
		}
	});

	function statusClass(status: DetailRequest['status']) {
		switch (status) {
			case 'approved': return 'badge-approved';
			case 'rejected': return 'badge-rejected';
			default: return 'badge-pending';
		}
	}

	function statusLabel(status: DetailRequest['status']) {
		switch (status) {
			case 'approved': return 'Approved — details sent via email';
			case 'rejected': return 'Rejected';
			default: return 'Pending admin review';
		}
	}

	function formatDate(iso: string): string {
		return new Date(iso).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' });
	}
</script>

<svelte:head>
	<title>My Requests — Maratha Kalyanam</title>
</svelte:head>

<div class="mx-auto max-w-3xl px-4 py-10">
	<h1 class="font-serif text-3xl font-bold text-maroon">
		{T.requests.en}
		<span class="ml-2" lang={langStore.current}>{tx('requests', langStore.current)}</span>
	</h1>
	<p class="mt-1 text-sm text-ink/60">Outbound detail requests you have sent</p>


	{#if loading}
		<div class="flex items-center justify-center py-20">
			<Loader size={36} class="animate-spin text-saffron" />
		</div>
	{:else if error}
		<div class="rounded-lg border border-vermilion/30 bg-vermilion/5 p-4 text-vermilion">
			{error}
		</div>
	{:else if requestList.length === 0}
		<div class="py-16 text-center">
			<Inbox size={56} class="mx-auto text-gold/40" />
			<h2 class="mt-4 font-serif text-xl font-semibold text-maroon">No requests yet</h2>
			<p class="mt-2 text-ink/60">
				Browse profiles and click "Request Full Details" to send a request.
			</p>
			<a href="/search" class="btn-primary mt-6 inline-flex flex-col items-center justify-center text-center leading-tight px-4 py-2 min-h-[52px] whitespace-normal">
				<span>Search Profiles</span>
				<span lang={langStore.current} class="text-[10px] opacity-90">{tx('searchProfiles', langStore.current)}</span>
			</a>
		</div>
	{:else}
		<ul class="mt-6 space-y-4">
			{#each requestList as req (req.id)}
				<li class="card flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
					<div class="flex-1">
						<a
							href="/profiles/{req.profile_id}"
							class="font-serif text-lg font-semibold text-maroon hover:underline"
						>
							{req.profile?.first_name ?? 'Profile'} {req.profile?.last_name ?? ''}
						</a>
						<p class="mt-0.5 text-sm text-ink/60">Sent: {formatDate(req.created_at)}</p>
						{#if req.message}
							<p class="mt-1 text-sm text-ink/70 italic">"{req.message}"</p>
						{/if}
						{#if req.admin_notes && req.status === 'rejected'}
							<p class="mt-1 text-sm text-vermilion">Note: {req.admin_notes}</p>
						{/if}
					</div>
					<span class={statusClass(req.status)}>{statusLabel(req.status)}</span>
				</li>
			{/each}
		</ul>
	{/if}
</div>
