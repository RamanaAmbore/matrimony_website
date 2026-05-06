<script lang="ts">
	import { onMount, onDestroy } from 'svelte';
	import { createGrid, ModuleRegistry, AllCommunityModule, type GridApi } from 'ag-grid-community';
	import 'ag-grid-community/styles/ag-grid.css';
	import 'ag-grid-community/styles/ag-theme-quartz.css';

	ModuleRegistry.registerModules([AllCommunityModule]);

	import {
		profiles as profilesApi,
		type Profile,
		ApiError
	} from '$lib/api';
	import { toastStore } from '$lib/stores/toast.svelte';
	import { goto } from '$app/navigation';
	import { Plus, User, Edit, Loader, SendHorizonal, Settings, Eye, Trash2 } from 'lucide-svelte';
	import { T, tx } from '$lib/i18n';
	import { langStore } from '$lib/stores/lang.svelte';
	import ConfirmDelete from '$lib/components/ConfirmDelete.svelte';
	import { userStatus } from '$lib/userStatus';

	let { data } = $props();

	let profileList = $state<Profile[]>([]);
	let loading = $state(true);
	let error = $state('');
	let submitting = $state<Record<string, boolean>>({});

	// Delete modal state
	let deleteModalOpen = $state(false);
	let pendingDelete = $state<Profile | null>(null);
	let deleting = $state(false);

	// ag-Grid
	let gridApi: GridApi | undefined;

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

	onDestroy(() => {
		gridApi?.destroy();
		gridApi = undefined;
	});

	async function submitProfile(id: string) {
		submitting[id] = true;
		try {
			const updated = await profilesApi.submit(id);
			profileList = profileList.map(p => p.id === id ? updated : p);
			gridApi?.setGridOption('rowData', [...profileList]);
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

	function openDeleteModal(profile: Profile) {
		pendingDelete = profile;
		deleteModalOpen = true;
	}

	async function confirmDelete() {
		if (!pendingDelete) return;
		deleting = true;
		try {
			await profilesApi.delete(pendingDelete.id);
			profileList = profileList.filter(p => p.id !== pendingDelete!.id);
			gridApi?.setGridOption('rowData', [...profileList]);
			toastStore.success('Profile deleted');
		} catch (err) {
			toastStore.error(err instanceof ApiError ? err.message.slice(0, 35) : 'Delete failed');
		} finally {
			deleting = false;
			pendingDelete = null;
		}
	}

	function formatDob(dob: string): string {
		// ISO YYYY-MM-DD → DD-MM-YYYY
		if (!dob) return '—';
		const [y, m, d] = dob.split('-');
		return `${d}-${m}-${y}`;
	}

	// Inline status pill HTML (mirrors admin grid style)
	function statusPill(status: string): string {
		const styles: Record<string, string> = {
			approved: 'background:#fef3c7;color:#92400e',  // saffron/25 text-maroon (badge-approved)
			pending:  'background:#fef9c3;color:#92400e',  // badge-pending
			rejected: 'background:#fee2e2;color:#dc2626',  // badge-revoked (legacy)
			revoked:  'background:#fee2e2;color:#dc2626',  // badge-revoked
			draft:    'background:#f3f4f6;color:#6b7280'   // badge-draft
		};
		const label = status === 'pending' ? 'Under Review' : status === 'revoked' ? 'Revoked' : status.charAt(0).toUpperCase() + status.slice(1);
		return `<span style="display:inline-block;padding:1px 8px;border-radius:9999px;font-size:11px;font-weight:600;${styles[status] ?? ''}">${label}</span>`;
	}

	// ag-Grid use:action
	function profilesGridAction(node: HTMLDivElement, rows: Profile[]) {
		const make = (data: Profile[]) => {
			gridApi?.destroy();
			const colDefs = [
				{
					field: 'profile_number',
					headerName: 'ID',
					width: 130,
					sortable: true,
					filter: true,
					headerClass: 'mk-header',
					cellStyle: { fontFamily: 'monospace', fontSize: '12px', color: '#6b7280', fontVariantNumeric: 'tabular-nums' }
				},
				{
					headerName: 'Name',
					width: 200,
					sortable: true,
					filter: true,
					headerClass: 'mk-header',
					valueGetter: (p: { data: Profile }) => `${p.data.first_name} ${p.data.last_name ?? ''}`.trim()
				},
				{
					field: 'gender',
					headerName: 'Gender',
					width: 100,
					sortable: true,
					filter: true,
					headerClass: 'mk-header',
					valueFormatter: (p: { value: string }) => p.value.charAt(0).toUpperCase() + p.value.slice(1)
				},
				{
					field: 'dob',
					headerName: 'DOB',
					width: 120,
					sortable: true,
					headerClass: 'mk-header',
					cellStyle: { fontVariantNumeric: 'tabular-nums' },
					valueFormatter: (p: { value: string }) => formatDob(p.value)
				},
				{
					headerName: 'Location',
					width: 190,
					filter: true,
					headerClass: 'mk-header',
					valueGetter: (p: { data: Profile }) => [p.data.city, p.data.state].filter(Boolean).join(', ')
				},
				{
					field: 'status',
					headerName: 'Status',
					width: 130,
					sortable: true,
					filter: true,
					headerClass: 'mk-header',
					cellRenderer: (p: { value: string }) => statusPill(p.value)
				},
				{
					headerName: '',
					width: 130,
					sortable: false,
					filter: false,
					pinned: 'right' as const,
					headerClass: 'mk-header',
					cellRenderer: (p: { data: Profile }) => {
						// View / Edit / Delete on every owner row regardless of admin
						// status. Editing one's own profile follows the standard
						// lifecycle (drops to pending) — admin/super-edit-preserves
						// only kicks in when editing someone ELSE's profile.
						return `<div style="display:flex;gap:6px;align-items:center;justify-content:flex-end;height:100%">
							<button data-action="view" data-id="${p.data.id}" title="View profile" style="background:none;border:1px solid #c9a227;border-radius:4px;padding:3px 5px;cursor:pointer;color:#6b0f1a;">
								<svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M2 12s3-7 10-7 10 7 10 7-3 7-10 7-10-7-10-7Z"/><circle cx="12" cy="12" r="3"/></svg>
							</button>
							<button data-action="edit" data-id="${p.data.id}" title="Edit profile" style="background:none;border:1px solid #6b0f1a;border-radius:4px;padding:3px 5px;cursor:pointer;color:#6b0f1a;">
								<svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 20h9"/><path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4 12.5-12.5z"/></svg>
							</button>
							<button data-action="delete" data-id="${p.data.id}" title="Delete profile" style="background:#e63946;border:none;border-radius:4px;padding:3px 5px;cursor:pointer;color:#fff;">
								<svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6"/><path d="M10 11v6"/><path d="M14 11v6"/><path d="M9 6V4h6v2"/></svg>
							</button>
						</div>`;
					},
					onCellClicked: (e: { event: Event; data: Profile }) => {
						const target = (e.event.target as HTMLElement).closest('[data-action]') as HTMLElement | null;
						if (!target) return;
						const action = target.dataset.action;
						if (action === 'view') {
							goto(`/profiles/${e.data.id}`);
						} else if (action === 'edit') {
							goto(`/profiles/${e.data.id}/edit`);
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
				onRowClicked: (e) => {
					// Only navigate if the click wasn't on an action button
					const target = e.event?.target as HTMLElement | null;
					if (target?.closest('[data-action]')) return;
					if (e.data) goto(`/profiles/${(e.data as Profile).id}`);
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
	<title>My Profiles — Maratha Kalyanam</title>
</svelte:head>

<div class="mx-auto max-w-5xl px-4 py-10">
	<div class="flex items-center justify-between">
		<div>
			<h1 class="font-serif text-3xl font-bold text-maroon">
				{T.myProfiles.en}
				<span class="ml-2" lang={langStore.current}>{tx('myProfiles', langStore.current)}</span>
			</h1>
			<p class="mt-1 text-sm text-ink/60">Manage your matrimonial profiles</p>
		</div>
		{#if !data.user || data.user.is_approved}
			<a href="/profiles/new" class="btn-primary flex flex-col items-center justify-center text-center leading-tight px-3 py-2 min-h-[52px] whitespace-normal">
				<span class="flex items-center gap-1.5 text-sm"><Plus size={16} />New Profile</span>
				<span lang={langStore.current} class="text-[10px] opacity-90">{tx('newProfile', langStore.current)}</span>
			</a>
		{:else}
			<button class="btn-primary flex flex-col items-center justify-center text-center leading-tight px-3 py-2 min-h-[52px] whitespace-normal opacity-50 cursor-not-allowed" disabled title="Account pending admin approval">
				<span class="flex items-center gap-1.5 text-sm"><Plus size={16} />New Profile</span>
				<span lang={langStore.current} class="text-[10px] opacity-90">{tx('newProfile', langStore.current)}</span>
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
			<div class="flex items-start justify-between gap-3 flex-wrap">
				<p class="font-medium text-maroon font-serif text-base mb-2">Account Details
					<span class="ml-1" lang={langStore.current}>{tx('dashAccountDetails', langStore.current)}</span>
				</p>
				<a
					href="/account"
					class="btn-secondary flex items-center gap-1.5 text-sm py-1 px-3 min-h-[36px] whitespace-nowrap"
				>
					<Settings size={14} />
					<span>{T.myAccount.en}</span>
					<span lang={langStore.current} class="text-[10px] opacity-80">{tx('myAccount', langStore.current)}</span>
				</a>
			</div>
			<div class="grid grid-cols-2 gap-x-6 gap-y-1 sm:grid-cols-4 text-ink/70">
				<div><span class="text-xs text-ink/50 block">Name</span>{data.user.full_name || '—'}</div>
				<div><span class="text-xs text-ink/50 block">User ID</span><span class="font-mono">{data.user.user_id}</span></div>
				<div><span class="text-xs text-ink/50 block">Email</span>{data.user.email}</div>
				<div><span class="text-xs text-ink/50 block">Phone</span>{data.user.phone_number}</div>
				<div class="col-span-2 sm:col-span-4 mt-1 flex items-center gap-2 flex-wrap">
					<span class="text-xs text-ink/50">Account status</span>
					{#if userStatus(data.user) === 'approved'}
						<span class="inline-flex items-center gap-1 rounded-full bg-green-100 px-2.5 py-0.5 text-xs font-semibold text-green-800">
							<svg xmlns="http://www.w3.org/2000/svg" width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>
							Approved
						</span>
					{:else if userStatus(data.user) === 'revoked'}
						<span class="inline-flex items-center gap-1 rounded-full bg-red-100 px-2.5 py-0.5 text-xs font-semibold text-red-700">
							<svg xmlns="http://www.w3.org/2000/svg" width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>
							Revoked — contact admin
						</span>
					{:else}
						<span class="inline-flex items-center gap-1 rounded-full bg-amber-100 px-2.5 py-0.5 text-xs font-semibold text-amber-800">
							<svg xmlns="http://www.w3.org/2000/svg" width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
							Pending approval
						</span>
					{/if}
					{#if !data.user.email_verified}
						<span class="inline-flex items-center gap-1 rounded-full bg-orange-100 px-2.5 py-0.5 text-xs font-semibold text-orange-800">
							Email unverified
						</span>
					{/if}
				</div>
			</div>
		</div>
	{/if}

	{#if loading}
		<div class="flex items-center justify-center py-20">
			<Loader size={36} class="animate-spin text-saffron" />
		</div>
	{:else if error}
		<div class="rounded-lg border border-vermilion/30 bg-vermilion/5 p-4 text-vermilion">
			{error}
		</div>
	{:else if profileList.length === 0}
		<div class="py-16 text-center">
			<div class="mx-auto mb-4 flex h-20 w-20 items-center justify-center rounded-full bg-cream/60 border-2 border-gold/30">
				<User size={40} class="text-gold/50" />
			</div>
			<h2 class="mt-2 font-serif text-xl font-semibold text-maroon">No profiles yet</h2>
			<p class="mt-2 text-ink/60">Use the "New Profile" button in the top right to start appearing in search results.</p>
			{#if data.user && !data.user.is_approved}
				<p class="mt-4 text-sm text-saffron font-medium">Your account is pending admin approval before you can create profiles.</p>
			{/if}
		</div>
	{:else}
		<div class="mt-6">
			<p class="mb-2 text-xs text-ink/50">Click a row to view profile. Use the action buttons in the last column to view or delete.</p>
			<!-- ag-Grid -->
			{#key profileList.length}
			<div
				use:profilesGridAction={profileList}
				class="ag-theme-quartz w-full rounded-lg overflow-hidden border border-[#c8a96e] shadow-sm"
				style="height: 420px; {AG_STYLE}"
			></div>
			{/key}
		</div>
	{/if}
</div>

<!-- Double-confirm delete modal -->
<ConfirmDelete
	bind:open={deleteModalOpen}
	title="Delete profile?"
	description={pendingDelete
		? `This will permanently remove ${pendingDelete.first_name} ${pendingDelete.last_name ?? ''}'s profile, all photos, and detail requests. This cannot be undone.`
		: 'This will permanently remove the profile. This cannot be undone.'}
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
