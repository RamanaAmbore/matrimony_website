<script lang="ts">
	import { onMount } from 'svelte';
	import { admin as adminApi, type DetailRequest } from '$lib/api';
	import { ApiError } from '$lib/api';
	import { toastStore } from '$lib/stores/toast.svelte';
	import { goto } from '$app/navigation';
	import { Loader, CheckCircle, XCircle, Clock, RotateCcw, Trash2 } from 'lucide-svelte';
	import { tx } from '$lib/i18n';
	import { langStore } from '$lib/stores/lang.svelte';
	import ConfirmDelete from '$lib/components/ConfirmDelete.svelte';

	let statusFilter = $state('pending');
	let requestList = $state<DetailRequest[]>([]);
	let loading = $state(true);
	let processingId = $state<string | null>(null);

	// ConfirmDelete modal state (delete only — reject is now one-click)
	let deleteOpen = $state(false);
	let pendingDelete = $state<{ id: string; label: string } | null>(null);

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
		} catch (err) {
			toastStore.error(err instanceof ApiError ? err.message.slice(0, 35) : 'Approval failed');
		} finally {
			processingId = null;
		}
	}

	async function reject(id: string) {
		processingId = id;
		try {
			const updated = await adminApi.requests.reject(id);
			if (statusFilter === 'revoked') {
				requestList = requestList.map((r) => r.id === id ? updated : r);
			} else {
				requestList = requestList.filter((r) => r.id !== id);
			}
			toastStore.success('Request revoked');
		} catch (err) {
			toastStore.error(err instanceof ApiError ? err.message.slice(0, 35) : 'Revoke failed');
		} finally {
			processingId = null;
		}
	}

	async function reinstate(id: string) {
		processingId = id;
		try {
			const updated = await adminApi.requests.reinstate(id);
			if (statusFilter === 'approved') {
				requestList = requestList.map((r) => r.id === id ? updated : r);
			} else {
				requestList = requestList.filter((r) => r.id !== id);
			}
			toastStore.success('Request reinstated');
		} catch (err) {
			toastStore.error(err instanceof ApiError ? err.message.slice(0, 35) : 'Reinstate failed');
		} finally {
			processingId = null;
		}
	}

	function startDelete(req: DetailRequest) {
		const profileName = req.profile_first_name
			? `${req.profile_first_name} ${req.profile_last_name ?? ''}`.trim()
			: req.profile_id;
		pendingDelete = {
			id: req.id,
			label: `request for ${profileName}`
		};
		deleteOpen = true;
	}

	async function doDelete() {
		if (!pendingDelete) return;
		processingId = pendingDelete.id;
		try {
			await adminApi.requests.delete(pendingDelete.id);
			requestList = requestList.filter((r) => r.id !== pendingDelete!.id);
			toastStore.success('Request deleted');
		} catch (err) {
			toastStore.error(err instanceof ApiError ? err.message.slice(0, 35) : 'Delete failed');
		} finally {
			processingId = null;
			pendingDelete = null;
		}
	}

	function formatDate(iso: string): string {
		return new Date(iso).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' });
	}

	function badgeClass(status: string): string {
		if (status === 'approved') return 'badge-approved';
		if (status === 'revoked' || status === 'rejected') return 'badge-revoked';
		return 'badge-pending';
	}
</script>

<svelte:head>
	<title>Admin: Requests — Maratha Kalyanam</title>
</svelte:head>

<ConfirmDelete
	bind:open={deleteOpen}
	title="Delete request?"
	description={`Permanently remove the ${pendingDelete?.label ?? 'this request'}. Cannot be undone.`}
	onConfirm={doDelete}
/>

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
		{#each ['pending', 'approved', 'revoked'] as s}
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
								<span class="badge {badgeClass(req.status)} inline-flex items-center gap-1 capitalize">
									{#if req.status === 'pending'}<Clock size={12} class="-mt-0.5 inline-block" />
									{:else if req.status === 'approved'}<CheckCircle size={12} class="-mt-0.5 inline-block" />
									{:else if req.status === 'revoked' || req.status === 'rejected'}<XCircle size={12} class="-mt-0.5 inline-block" />
									{/if}
									{req.status === 'rejected' ? 'Revoked' : req.status}
								</span>
							</div>
							<p class="mt-0.5 text-sm text-ink/60">Sent {formatDate(req.created_at)}</p>
							{#if req.message}
								<p class="mt-1 text-sm italic text-ink/70">"{req.message}"</p>
							{/if}
						</div>

						<div class="flex flex-wrap gap-2">
							{#if req.status === 'pending'}
								<button
									onclick={() => approve(req.id)}
									disabled={processingId === req.id}
									class="flex flex-col items-center justify-center text-center leading-tight rounded bg-green-600 px-3 py-1.5 min-h-[44px] text-sm text-white hover:bg-green-700 focus-visible:outline-2 focus-visible:outline-saffron disabled:opacity-60 whitespace-normal"
								>
									<span class="flex items-center gap-1"><CheckCircle size={13} />Approve</span>
									<span lang={langStore.current} class="text-[10px] opacity-90">{tx('approve', langStore.current)}</span>
								</button>
								<button
									onclick={() => reject(req.id)}
									disabled={processingId === req.id}
									class="flex flex-col items-center justify-center text-center leading-tight rounded bg-vermilion px-3 py-1.5 min-h-[44px] text-sm text-white hover:bg-vermilion/80 focus-visible:outline-2 focus-visible:outline-saffron disabled:opacity-60 whitespace-normal"
								>
									<span class="flex items-center gap-1"><XCircle size={13} />Revoke</span>
									<span lang={langStore.current} class="text-[10px] opacity-90">{tx('reject', langStore.current)}</span>
								</button>
							{/if}

							{#if req.status === 'revoked' || req.status === 'rejected'}
								<button
									onclick={() => reinstate(req.id)}
									disabled={processingId === req.id}
									class="flex flex-col items-center justify-center text-center leading-tight rounded border border-green-600 bg-white px-3 py-1.5 min-h-[44px] text-sm text-green-700 hover:bg-green-50 focus-visible:outline-2 focus-visible:outline-saffron disabled:opacity-60 whitespace-normal"
								>
									<span class="flex items-center gap-1"><RotateCcw size={13} />Reinstate</span>
									<span lang={langStore.current} class="text-[10px] opacity-90">{tx('approve', langStore.current)}</span>
								</button>
							{/if}

							<!-- Delete: always available with double-confirm -->
							<button
								onclick={() => startDelete(req)}
								disabled={processingId === req.id}
								class="flex flex-col items-center justify-center text-center leading-tight rounded bg-vermilion px-3 py-1.5 min-h-[44px] text-sm text-white hover:bg-vermilion/80 focus-visible:outline-2 focus-visible:outline-saffron disabled:opacity-60 whitespace-normal"
							>
								<span class="flex items-center gap-1"><Trash2 size={13} />Delete</span>
								<span lang={langStore.current} class="text-[10px] opacity-90">{tx('delete', langStore.current)}</span>
							</button>
						</div>
					</div>
				</div>
			{/each}
		</div>
	{/if}
</div>
