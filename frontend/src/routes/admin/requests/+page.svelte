<script lang="ts">
	import { onMount } from 'svelte';
	import { admin as adminApi, type DetailRequest } from '$lib/api';
	import { ApiError } from '$lib/api';
	import { toastStore } from '$lib/stores/toast.svelte';
	import { goto } from '$app/navigation';
	import { Loader, CheckCircle, XCircle, Clock } from 'lucide-svelte';
	import { tx } from '$lib/i18n';
	import { langStore } from '$lib/stores/lang.svelte';

	let statusFilter = $state('pending');
	let requestList = $state<DetailRequest[]>([]);
	let loading = $state(true);
	let processingId = $state<string | null>(null);
	let rejectNotes = $state<Record<string, string>>({});
	let showRejectForm = $state<Record<string, boolean>>({});

	async function load() {
		loading = true;
		try {
			requestList = await adminApi.requests.list(statusFilter);
		} catch (err) {
			if (err instanceof ApiError) {
				if (err.status === 401) { goto('/login'); return; }
				if (err.status === 403) { goto('/'); return; }
			}
			toastStore.error('Failed to load requests');
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
			await adminApi.requests.approve(id);
			requestList = requestList.filter((r) => r.id !== id);
			toastStore.success('Request approved — details emailed to requester');
		} catch {
			toastStore.error('Approval failed');
		} finally {
			processingId = null;
		}
	}

	async function reject(id: string) {
		const notes = rejectNotes[id];
		if (!notes?.trim()) {
			toastStore.error('Rejection reason is required');
			return;
		}
		processingId = id;
		try {
			await adminApi.requests.reject(id, notes.trim());
			requestList = requestList.filter((r) => r.id !== id);
			toastStore.success('Request rejected');
			showRejectForm = { ...showRejectForm, [id]: false };
		} catch {
			toastStore.error('Rejection failed');
		} finally {
			processingId = null;
		}
	}

	function formatDate(iso: string): string {
		return new Date(iso).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' });
	}
</script>

<svelte:head>
	<title>Admin: Requests — Maratha Kalyanam</title>
</svelte:head>

<div class="mx-auto max-w-5xl px-4 py-10">
	<div class="flex flex-wrap items-center justify-between gap-3 mb-2">
		<h1 class="font-serif text-3xl font-bold text-maroon">Detail Requests</h1>
		<a href="/admin" class="btn-secondary flex flex-col items-center justify-center text-center leading-tight text-sm px-3 py-1.5 min-h-[44px] whitespace-normal">
			<span>← Dashboard</span>
			<span lang={langStore.current} class="text-[10px] opacity-90">{tx('dashboardBack', langStore.current)}</span>
		</a>
	</div>

	<!-- Status filter tabs -->
	<div class="mt-4 flex gap-2 border-b border-gold/20 -mb-px">
		{#each ['pending', 'approved', 'rejected'] as s}
			<button
				onclick={() => (statusFilter = s)}
				class="px-4 py-2 text-sm font-medium border-b-2 transition-colors duration-150
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
	{:else if requestList.length === 0}
		<div class="py-16 text-center text-ink/60">No {statusFilter} requests.</div>
	{:else}
		<div class="space-y-4 mt-4">
			{#each requestList as req (req.id)}
				<div class="card">
					<div class="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
						<div class="flex-1">
							<div class="flex flex-wrap items-center gap-2">
								<a href="/profiles/{req.profile_id}" class="font-serif text-lg font-semibold text-maroon hover:underline">
									Profile: {req.profile?.first_name ?? req.profile_id} {req.profile?.last_name ?? ''}
								</a>
								<span class="badge {req.status === 'approved' ? 'badge-approved' : req.status === 'rejected' ? 'badge-rejected' : 'badge-pending'} inline-flex items-center gap-1 capitalize">
									{#if req.status === 'pending'}<Clock size={12} class="-mt-0.5 inline-block" />
									{:else if req.status === 'approved'}<CheckCircle size={12} class="-mt-0.5 inline-block" />
									{:else if req.status === 'rejected'}<XCircle size={12} class="-mt-0.5 inline-block" />
									{/if}
									{req.status}
								</span>
							</div>
							<p class="mt-0.5 text-sm text-ink/60">Sent {formatDate(req.created_at)}</p>
							{#if req.message}
								<p class="mt-1 text-sm italic text-ink/70">"{req.message}"</p>
							{/if}
						</div>

						{#if req.status === 'pending'}
							<div class="flex flex-wrap gap-2">
								<button
									onclick={() => approve(req.id)}
									disabled={processingId === req.id}
									class="flex flex-col items-center justify-center text-center leading-tight rounded bg-green-600 px-3 py-1.5 min-h-[44px] text-sm text-white hover:bg-green-700 focus-visible:outline-2 focus-visible:outline-saffron disabled:opacity-60 whitespace-normal"
								>
									<span class="flex items-center gap-1"><CheckCircle size={13} />Approve</span>
									<span lang={langStore.current} class="text-[10px] opacity-90">{tx('approve', langStore.current)}</span>
								</button>
								<button
									onclick={() => (showRejectForm = { ...showRejectForm, [req.id]: !showRejectForm[req.id] })}
									disabled={processingId === req.id}
									class="flex flex-col items-center justify-center text-center leading-tight rounded bg-vermilion px-3 py-1.5 min-h-[44px] text-sm text-white hover:bg-vermilion/80 focus-visible:outline-2 focus-visible:outline-saffron disabled:opacity-60 whitespace-normal"
								>
									<span class="flex items-center gap-1"><XCircle size={13} />Reject</span>
									<span lang={langStore.current} class="text-[10px] opacity-90">{tx('reject', langStore.current)}</span>
								</button>
							</div>
						{/if}
					</div>

					{#if showRejectForm[req.id]}
						<div class="mt-4 border-t border-gold/20 pt-4 flex flex-col gap-2">
							<label class="label" for="reject-req-{req.id}">Rejection reason (required)</label>
							<textarea
								id="reject-req-{req.id}"
								class="input resize-none"
								rows="2"
								bind:value={rejectNotes[req.id]}
								placeholder="Explain the reason…"
							></textarea>
							<div class="flex gap-2">
								<button
									onclick={() => (showRejectForm = { ...showRejectForm, [req.id]: false })}
									class="btn-secondary flex flex-col items-center justify-center text-center leading-tight text-sm py-1.5 px-3 min-h-[44px] whitespace-normal"
								>
									<span class="text-xs">Cancel</span>
									<span lang={langStore.current} class="text-[10px] opacity-90">{tx('cancel', langStore.current)}</span>
								</button>
								<button
									onclick={() => reject(req.id)}
									disabled={processingId === req.id}
									class="btn-danger flex flex-col items-center justify-center text-center leading-tight text-sm py-1.5 px-3 min-h-[44px] whitespace-normal"
								>
									<span class="text-xs">{processingId === req.id ? 'Rejecting…' : 'Confirm Reject'}</span>
									<span lang={langStore.current} class="text-[10px] opacity-90">{tx('confirmReject', langStore.current)}</span>
								</button>
							</div>
						</div>
					{/if}
				</div>
			{/each}
		</div>
	{/if}
</div>
