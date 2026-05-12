<script lang="ts">
	import { admin as adminApi, type AuditLogEntry, type AuditLogResponse, type User } from '$lib/api';
	import { toastStore } from '$lib/stores/toast.svelte';
	import { goto } from '$app/navigation';
	import { onMount } from 'svelte';
	import { T, tx } from '$lib/i18n';
	import { langStore } from '$lib/stores/lang.svelte';
	import { Loader, ChevronLeft, ChevronRight } from 'lucide-svelte';

	let { data } = $props();
	let loggedInUser = $derived<User | null>(data.user ?? null);

	// ── Filter state ─────────────────────────────────────────────────────────────
	let filterActorId = $state('');
	let filterTargetId = $state('');
	let filterAction = $state('');
	let currentPage = $state(1);
	const PER_PAGE = 50;

	// ── Data state ───────────────────────────────────────────────────────────────
	// Initialised from SSR load data; updated client-side on filter/page changes
	// eslint-disable-next-line svelte/reactivity
	let result = $state<AuditLogResponse>(data.auditLog);
	let loading = $state(false);

	// Track which rows have expanded metadata
	let expandedRows = $state<Set<string>>(new Set());

	function toggleExpand(id: string) {
		const next = new Set(expandedRows);
		if (next.has(id)) next.delete(id);
		else next.add(id);
		expandedRows = next;
	}

	async function fetchPage(page: number) {
		loading = true;
		try {
			const params: Record<string, string | number> = { page, per_page: PER_PAGE };
			if (filterActorId.trim()) params.actor_id = filterActorId.trim();
			if (filterTargetId.trim()) params.target_id = filterTargetId.trim();
			if (filterAction) params.action = filterAction;
			result = await adminApi.auditLog(params);
			currentPage = page;
			expandedRows = new Set();
		} catch (err) {
			toastStore.error('Failed to load audit log');
		} finally {
			loading = false;
		}
	}

	function applyFilters() {
		fetchPage(1);
	}

	function clearFilters() {
		filterActorId = '';
		filterTargetId = '';
		filterAction = '';
		fetchPage(1);
	}

	// Redirect non-super users
	onMount(() => {
		if (!loggedInUser?.is_super) {
			goto('/admin');
		}
	});

	// Total pages
	let totalPages = $derived(Math.max(1, Math.ceil(result.total / PER_PAGE)));

	function actionBadgeClass(action: string): string {
		if (action === 'impersonate_start') return 'bg-amber-100 text-amber-800 border border-amber-300';
		if (action === 'impersonate_stop') return 'bg-gray-100 text-gray-700 border border-gray-300';
		if (action === 'password_reset_admin') return 'bg-maroon/10 text-maroon border border-maroon/30';
		return 'bg-cream text-ink/70 border border-gold/30';
	}

	function formatDate(iso: string): string {
		try {
			// Convert to IST (UTC+5:30)
			const d = new Date(iso);
			return d.toLocaleString('en-IN', {
				timeZone: 'Asia/Kolkata',
				year: 'numeric',
				month: 'short',
				day: 'numeric',
				hour: '2-digit',
				minute: '2-digit',
				hour12: true
			}) + ' IST';
		} catch {
			return iso;
		}
	}

	const ACTION_OPTIONS = [
		{ value: '', label: 'All actions' },
		{ value: 'impersonate_start', label: 'Impersonate start' },
		{ value: 'impersonate_stop', label: 'Impersonate stop' },
		{ value: 'password_reset_admin', label: 'Password reset (admin)' }
	];
</script>

<svelte:head>
	<title>Audit Log — Maratha Kalyanam Admin</title>
</svelte:head>

<div class="mx-auto max-w-5xl px-4 py-8 space-y-6">
	<!-- Header row -->
	<div class="flex flex-wrap items-center justify-between gap-3">
		<h1 class="font-serif text-3xl font-bold text-maroon">
			{T.auditLog.en}
			<span class="ml-2 font-normal text-xl text-ink/50" lang={langStore.current}>{tx('auditLog', langStore.current)}</span>
		</h1>
		<a href="/admin" class="btn-secondary text-sm px-3 py-1.5 flex items-center gap-1">
			← {T.dashboard.en}
		</a>
	</div>

	<!-- Filters -->
	<div class="rounded-xl border border-gold/30 bg-white p-4 shadow-sm">
		<div class="flex flex-wrap gap-3 items-end">
			<div class="flex-1 min-w-[160px]">
				<label for="al-actor" class="label text-xs mb-1 block">Actor UUID</label>
				<input
					id="al-actor"
					type="text"
					class="input font-mono text-xs"
					placeholder="UUID of actor…"
					bind:value={filterActorId}
				/>
			</div>
			<div class="flex-1 min-w-[160px]">
				<label for="al-target" class="label text-xs mb-1 block">Target UUID</label>
				<input
					id="al-target"
					type="text"
					class="input font-mono text-xs"
					placeholder="UUID of target…"
					bind:value={filterTargetId}
				/>
			</div>
			<div class="flex-1 min-w-[180px]">
				<label for="al-action" class="label text-xs mb-1 block">
					{T.action.en} · <span lang={langStore.current}>{tx('action', langStore.current)}</span>
				</label>
				<select id="al-action" class="input text-sm" bind:value={filterAction}>
					{#each ACTION_OPTIONS as opt}
						<option value={opt.value}>{opt.label}</option>
					{/each}
				</select>
			</div>
			<div class="flex gap-2">
				<button
					type="button"
					onclick={applyFilters}
					class="btn-primary px-4 py-2 text-sm min-h-[40px]"
					disabled={loading}
				>
					{loading ? 'Loading…' : 'Filter'}
				</button>
				<button
					type="button"
					onclick={clearFilters}
					class="btn-secondary px-4 py-2 text-sm min-h-[40px]"
				>
					Clear
				</button>
			</div>
		</div>
	</div>

	<!-- Results summary -->
	<p class="text-sm text-ink/60">
		{result.total} total entries · page {currentPage} of {totalPages}
	</p>

	{#if loading}
		<div class="flex justify-center py-16">
			<Loader size={36} class="animate-spin text-saffron" />
		</div>
	{:else if result.items.length === 0}
		<div class="rounded-xl border border-gold/30 bg-white p-10 text-center text-ink/50 shadow-sm">
			<p>No audit log entries found.</p>
		</div>
	{:else}
		<div class="rounded-xl border border-gold/30 bg-white shadow-sm overflow-hidden">
			<table class="w-full text-sm">
				<thead>
					<tr class="border-b border-gold/20 bg-cream/60">
						<th class="text-left px-4 py-3 font-semibold text-ink/70 text-xs uppercase tracking-wide">When</th>
						<th class="text-left px-4 py-3 font-semibold text-ink/70 text-xs uppercase tracking-wide">
							{T.actor.en} · <span lang={langStore.current}>{tx('actor', langStore.current)}</span>
						</th>
						<th class="text-left px-4 py-3 font-semibold text-ink/70 text-xs uppercase tracking-wide">
							{T.action.en}
						</th>
						<th class="text-left px-4 py-3 font-semibold text-ink/70 text-xs uppercase tracking-wide">
							{T.target.en} · <span lang={langStore.current}>{tx('target', langStore.current)}</span>
						</th>
						<th class="text-left px-4 py-3 font-semibold text-ink/70 text-xs uppercase tracking-wide">
							{T.metadata.en}
						</th>
					</tr>
				</thead>
				<tbody class="divide-y divide-gold/10">
					{#each result.items as entry (entry.id)}
						<tr class="hover:bg-cream/40 transition-colors">
							<td class="px-4 py-3 text-xs text-ink/60 tabular-nums whitespace-nowrap">
								{formatDate(entry.created_at)}
							</td>
							<td class="px-4 py-3">
								{#if entry.actor}
									<span class="font-medium text-ink">{entry.actor.full_name}</span>
									<span class="ml-1 text-xs font-mono text-ink/50">@{entry.actor.user_handle}</span>
								{:else}
									<span class="text-ink/40">—</span>
								{/if}
							</td>
							<td class="px-4 py-3">
								<span class="inline-flex items-center rounded px-2 py-0.5 text-xs font-semibold {actionBadgeClass(entry.action)}">
									{entry.action}
								</span>
							</td>
							<td class="px-4 py-3">
								{#if entry.target}
									<span class="font-medium text-ink">{entry.target.full_name}</span>
									<span class="ml-1 text-xs font-mono text-ink/50">@{entry.target.user_handle}</span>
								{:else}
									<span class="text-ink/40">—</span>
								{/if}
							</td>
							<td class="px-4 py-3">
								{#if entry.metadata && Object.keys(entry.metadata).length > 0}
									<button
										type="button"
										onclick={() => toggleExpand(entry.id)}
										class="text-xs text-saffron hover:underline"
									>
										{expandedRows.has(entry.id) ? 'Hide' : 'Show'}
									</button>
									{#if expandedRows.has(entry.id)}
										<pre class="mt-1 rounded bg-cream p-2 text-xs text-ink/80 overflow-x-auto max-w-xs">{JSON.stringify(entry.metadata, null, 2)}</pre>
									{/if}
								{:else}
									<span class="text-ink/30 text-xs">—</span>
								{/if}
							</td>
						</tr>
					{/each}
				</tbody>
			</table>
		</div>

		<!-- Pagination -->
		{#if totalPages > 1}
			<div class="flex items-center justify-center gap-3 pt-2">
				<button
					type="button"
					onclick={() => fetchPage(currentPage - 1)}
					disabled={currentPage <= 1 || loading}
					class="flex items-center gap-1 rounded border border-gold/40 px-3 py-1.5 text-sm text-maroon hover:bg-maroon/5 disabled:opacity-40"
				>
					<ChevronLeft size={14} /> Prev
				</button>
				<span class="text-sm text-ink/70">Page {currentPage} of {totalPages}</span>
				<button
					type="button"
					onclick={() => fetchPage(currentPage + 1)}
					disabled={currentPage >= totalPages || loading}
					class="flex items-center gap-1 rounded border border-gold/40 px-3 py-1.5 text-sm text-maroon hover:bg-maroon/5 disabled:opacity-40"
				>
					Next <ChevronRight size={14} />
				</button>
			</div>
		{/if}
	{/if}
</div>
