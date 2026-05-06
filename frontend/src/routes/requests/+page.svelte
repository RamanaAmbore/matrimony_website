<script lang="ts">
	import { onMount, onDestroy } from 'svelte';
	import { createGrid, ModuleRegistry, AllCommunityModule, type GridApi } from 'ag-grid-community';
	import 'ag-grid-community/styles/ag-grid.css';
	import 'ag-grid-community/styles/ag-theme-quartz.css';

	ModuleRegistry.registerModules([AllCommunityModule]);

	import {
		requests as requestsApi,
		type EnrichedRequest,
		ApiError
	} from '$lib/api';
	import { toastStore } from '$lib/stores/toast.svelte';
	import { goto } from '$app/navigation';
	import { Loader, Inbox, User } from 'lucide-svelte';
	import { T, tx } from '$lib/i18n';
	import { langStore } from '$lib/stores/lang.svelte';
	import ConfirmDelete from '$lib/components/ConfirmDelete.svelte';

	let requestList = $state<EnrichedRequest[]>([]);
	let loading = $state(true);
	let error = $state('');

	// Delete modal
	let deleteModalOpen = $state(false);
	let pendingDelete = $state<EnrichedRequest | null>(null);

	// ag-Grid
	let gridApi: GridApi | undefined;

	onMount(async () => {
		try {
			requestList = await requestsApi.listMine();
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

	onDestroy(() => {
		gridApi?.destroy();
		gridApi = undefined;
	});

	function openDeleteModal(req: EnrichedRequest) {
		pendingDelete = req;
		deleteModalOpen = true;
	}

	async function confirmDelete() {
		if (!pendingDelete) return;
		try {
			await requestsApi.delete(pendingDelete.id);
			requestList = requestList.filter(r => r.id !== pendingDelete!.id);
			gridApi?.setGridOption('rowData', [...requestList]);
			toastStore.success('Request deleted');
		} catch (err) {
			toastStore.error(err instanceof ApiError ? err.message.slice(0, 35) : 'Delete failed');
		} finally {
			pendingDelete = null;
		}
	}

	function requestStatusPill(status: string): string {
		const styles: Record<string, string> = {
			approved: 'background:#dcfce7;color:#16a34a',
			pending:  'background:#fef3c7;color:#92400e',
			rejected: 'background:#fee2e2;color:#dc2626',
			revoked:  'background:#fee2e2;color:#dc2626'
		};
		const labels: Record<string, string> = {
			approved: 'Approved',
			pending:  'Pending',
			rejected: 'Revoked',
			revoked:  'Revoked'
		};
		return `<span style="display:inline-block;padding:1px 8px;border-radius:9999px;font-size:11px;font-weight:600;${styles[status] ?? ''}">${labels[status] ?? status}</span>`;
	}

	/** Render a 36×48 blurred thumbnail or a User placeholder icon if URL is null. */
	function thumbRenderer(url: string | null): string {
		if (url) {
			return `<div style="display:flex;align-items:center;height:100%;padding:2px 0">
				<img src="${url}" alt="" loading="lazy" decoding="async"
					style="width:36px;height:48px;object-fit:cover;border-radius:4px;border:1px solid #e8dcc8;filter:blur(3px);" />
			</div>`;
		}
		// Fallback: User silhouette SVG in a muted box
		return `<div style="display:flex;align-items:center;height:100%;padding:2px 0">
			<div style="width:36px;height:48px;border-radius:4px;border:1px solid #e8dcc8;background:#f3f4f6;display:flex;align-items:center;justify-content:center;">
				<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#9ca3af" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
			</div>
		</div>`;
	}

	function requestsGridAction(node: HTMLDivElement, rows: EnrichedRequest[]) {
		const make = (data: EnrichedRequest[]) => {
			gridApi?.destroy();
			const colDefs = [
				{
					headerName: 'Photo',
					width: 70,
					sortable: false,
					filter: false,
					headerClass: 'mk-header',
					cellRenderer: (p: { data: EnrichedRequest }) => thumbRenderer(p.data.profile_blurred_url ?? null)
				},
				{
					field: 'request_number',
					headerName: 'Request ID',
					width: 150,
					sortable: true,
					filter: true,
					headerClass: 'mk-header',
					cellStyle: { fontFamily: 'monospace', fontSize: '12px', color: '#6b7280', fontVariantNumeric: 'tabular-nums' }
				},
				{
					headerName: 'Profile Name',
					width: 190,
					sortable: true,
					filter: true,
					headerClass: 'mk-header',
					valueGetter: (p: { data: EnrichedRequest }) =>
						`${p.data.profile_first_name ?? ''} ${p.data.profile_last_name ?? ''}`.trim() || '—'
				},
				{
					headerName: 'Location',
					width: 180,
					filter: true,
					headerClass: 'mk-header',
					valueGetter: (p: { data: EnrichedRequest }) =>
						[p.data.profile_city, p.data.profile_state].filter(Boolean).join(', ') || '—'
				},
				{
					field: 'status',
					headerName: 'Status',
					width: 120,
					sortable: true,
					filter: true,
					headerClass: 'mk-header',
					cellRenderer: (p: { value: string }) => requestStatusPill(p.value)
				},
				{
					headerName: '',
					width: 90,
					sortable: false,
					filter: false,
					pinned: 'right' as const,
					headerClass: 'mk-header',
					cellRenderer: (p: { data: EnrichedRequest }) => {
						return `<div style="display:flex;gap:6px;align-items:center;justify-content:flex-end;height:100%">
							<button data-action="view" data-id="${p.data.profile_id}" title="View profile" style="background:none;border:1px solid #c9a227;border-radius:4px;padding:3px 5px;cursor:pointer;color:#6b0f1a;">
								<svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M2 12s3-7 10-7 10 7 10 7-3 7-10 7-10-7-10-7Z"/><circle cx="12" cy="12" r="3"/></svg>
							</button>
							<button data-action="delete" data-id="${p.data.id}" title="Delete request" style="background:#e63946;border:none;border-radius:4px;padding:3px 5px;cursor:pointer;color:#fff;">
								<svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6"/><path d="M10 11v6"/><path d="M14 11v6"/><path d="M9 6V4h6v2"/></svg>
							</button>
						</div>`;
					},
					onCellClicked: (e: { event: Event; data: EnrichedRequest }) => {
						const target = (e.event.target as HTMLElement).closest('[data-action]') as HTMLElement | null;
						if (!target) return;
						const action = target.dataset.action;
						if (action === 'view') {
							goto(`/profiles/${e.data.profile_id}`);
						} else if (action === 'delete') {
							openDeleteModal(e.data);
						}
					}
				}
			];

			gridApi = createGrid(node, {
				columnDefs: colDefs as any[],
				rowData: [...data],
				rowSelection: { mode: 'singleRow', checkboxes: false, enableClickSelection: true },
				rowHeight: 56,
				onRowClicked: (e) => {
					const target = e.event?.target as HTMLElement | null;
					if (target?.closest('[data-action]')) return;
					if (e.data) goto(`/profiles/${(e.data as EnrichedRequest).profile_id}`);
				},
				defaultColDef: { resizable: true, floatingFilter: true, filter: true },
				pagination: true,
				paginationPageSize: 20,
				theme: 'legacy'
			});
		};

		make(rows);
		return { destroy: () => { gridApi?.destroy(); gridApi = undefined; } };
	}

	const AG_STYLE = [
		'--ag-header-background-color: #6b0f1a',
		'--ag-header-foreground-color: #fff8e7',
		'--ag-header-column-separator-display: block',
		'--ag-header-column-separator-color: #a01428',
		'--ag-header-column-separator-width: 1px',
		'--ag-cell-horizontal-border: solid #e8dcc8',
		'--ag-row-border-color: #e8dcc8',
		'--ag-row-border-width: 1px',
		'--ag-selected-row-background-color: #fdf3e7',
		'--ag-row-hover-color: #fdf8f0',
		'--ag-font-size: 13px',
		'--ag-grid-size: 6px',
		'--ag-list-item-height: 36px',
		'--ag-header-height: 42px'
	].join('; ');
</script>

<svelte:head>
	<title>My Requests — Maratha Kalyanam</title>
</svelte:head>

<div class="mx-auto max-w-5xl px-4 py-10">
	<h1 class="font-serif text-3xl font-bold text-maroon">
		{T.requests.en}
		<span class="ml-2" lang={langStore.current}>{tx('requests', langStore.current)}</span>
	</h1>
	<p class="mt-1 text-sm text-ink/60">Detail requests you have sent. Click a row to view that profile.</p>

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
		<div class="mt-6">
			<!-- ag-Grid -->
			{#key requestList.length}
			<div
				use:requestsGridAction={requestList}
				class="ag-theme-quartz w-full rounded-lg overflow-hidden border border-[#c8a96e] shadow-sm"
				style="height: 440px; {AG_STYLE}"
			></div>
			{/key}
		</div>
	{/if}
</div>

<!-- Double-confirm delete modal -->
<ConfirmDelete
	bind:open={deleteModalOpen}
	title="Delete request?"
	description={pendingDelete
		? `This will permanently delete your detail request for ${[pendingDelete.profile_first_name, pendingDelete.profile_last_name].filter(Boolean).join(' ') || 'this profile'}. This cannot be undone.`
		: 'This will permanently delete the request. This cannot be undone.'}
	onConfirm={confirmDelete}
/>

<style>
	:global(.mk-header) {
		font-weight: 700 !important;
		font-size: 12px !important;
		letter-spacing: 0.06em !important;
		text-transform: uppercase !important;
	}
	:global(.mk-header .ag-header-cell-text) {
		color: #fff8e7 !important;
	}
	:global(.mk-header .ag-icon) {
		color: #ffb627 !important;
	}
	:global(.ag-theme-quartz .ag-floating-filter) {
		background: #fdf8f0 !important;
		border-bottom: 1px solid #e8dcc8 !important;
	}
	:global(.ag-theme-quartz .ag-floating-filter-input input) {
		font-size: 12px !important;
		border: 1px solid #e8dcc8 !important;
		border-radius: 4px !important;
		padding: 2px 6px !important;
	}
	:global(.ag-theme-quartz .ag-floating-filter-input input:focus) {
		border-color: #6b0f1a !important;
		outline: none !important;
	}
	:global(.ag-theme-quartz .ag-paging-panel) {
		flex-wrap: wrap !important;
		row-gap: 4px !important;
		column-gap: 8px !important;
		padding: 6px 10px !important;
		justify-content: center !important;
	}
	@media (max-width: 640px) {
		:global(.ag-theme-quartz .ag-paging-page-size),
		:global(.ag-theme-quartz .ag-paging-row-summary-panel) {
			display: none !important;
		}
		:global(.ag-theme-quartz .ag-paging-panel) {
			font-size: 12px !important;
			gap: 4px !important;
		}
	}
</style>
