<script lang="ts">
	import { onMount, onDestroy } from 'svelte';
	import { createGrid, type GridApi, type GridOptions } from 'ag-grid-community';
	import 'ag-grid-community/styles/ag-grid.css';
	import 'ag-grid-community/styles/ag-theme-quartz.css';
	import {
		admin as adminApi,
		ApiError,
		type AdminDashboard,
		type PendingProfileSummary,
		type PendingRequest,
		type Profile,
		type DetailRequest,
		type User
	} from '$lib/api';
	import { goto } from '$app/navigation';
	import { toastStore } from '$lib/stores/toast.svelte';
	import {
		Loader,
		Users,
		UserCheck,
		Inbox,
		ShieldCheck
	} from 'lucide-svelte';

	// ── Tab state ────────────────────────────────────────────────────────────────

	type Tab = 'profiles' | 'requests' | 'users';
	let activeTab = $state<Tab>('profiles');

	// ── Dashboard state ──────────────────────────────────────────────────────────

	let dashboard = $state<AdminDashboard | null>(null);
	let loading = $state(true);
	let error = $state('');

	// Reject notes state: keyed by item id
	let rejectNotes = $state<Record<string, string>>({});
	let rejectOpen = $state<Record<string, boolean>>({});
	// Per-item action loading
	let actionLoading = $state<Record<string, boolean>>({});

	// ── All Profiles tab state ───────────────────────────────────────────────────

	let allProfiles = $state<Profile[] | null>(null);
	let allProfilesLoading = $state(false);
	let allProfilesError = $state('');
	let profileStatusFilter = $state<'all' | 'pending' | 'approved' | 'rejected' | 'draft'>('all');

	// ── All Requests tab state ───────────────────────────────────────────────────

	let allRequests = $state<DetailRequest[] | null>(null);
	let allRequestsLoading = $state(false);
	let allRequestsError = $state('');
	let requestStatusFilter = $state<'all' | 'pending' | 'approved' | 'rejected'>('all');

	// ── All Users tab state ──────────────────────────────────────────────────────

	let allUsers = $state<User[] | null>(null);
	let allUsersLoading = $state(false);
	let allUsersError = $state('');

	// ag-Grid state
	let usersGridDiv = $state<HTMLDivElement | undefined>(undefined);
	let usersGridApi = $state<GridApi | undefined>(undefined);
	let selectedUser = $state<User | null>(null);
	let userActionLoading = $state(false);

	// ── Broadcast Email state ─────────────────────────────────────────────────────

	let broadcastSubject = $state('');
	let broadcastBody = $state('');
	let broadcastVerifiedOnly = $state(true);
	let broadcastApprovedOnly = $state(false);
	let broadcastSending = $state(false);
	let broadcastResult = $state<{ sent: number; failed: number } | null>(null);

	async function sendBroadcast() {
		if (!broadcastSubject.trim() || !broadcastBody.trim()) {
			toastStore.error('Subject and message body are required.');
			return;
		}
		broadcastSending = true;
		broadcastResult = null;
		try {
			const result = await adminApi.broadcastEmail({
				subject: broadcastSubject.trim(),
				body_html: broadcastBody.trim(),
				filter_verified_only: broadcastVerifiedOnly,
				filter_approved_only: broadcastApprovedOnly
			});
			broadcastResult = result;
			toastStore.success(`Broadcast sent: ${result.sent} delivered, ${result.failed} failed.`);
		} catch (err) {
			toastStore.error(err instanceof ApiError ? err.message : 'Broadcast failed.');
		} finally {
			broadcastSending = false;
		}
	}

	// ── Mount: load dashboard + pre-load profiles ────────────────────────────────

	onMount(async () => {
		loadAllProfiles(); // start immediately so profiles show without waiting for dashboard
		try {
			dashboard = await adminApi.dashboard();
		} catch (err) {
			if (err instanceof ApiError) {
				if (err.status === 401) { goto('/login'); return; }
				if (err.status === 403) { goto('/'); return; }
			}
			error = 'Failed to load dashboard.';
		} finally {
			loading = false;
		}
	});

	// ── Lazy tab loaders ─────────────────────────────────────────────────────────

	async function loadAllProfiles() {
		if (allProfiles !== null) return; // already loaded
		allProfilesLoading = true;
		allProfilesError = '';
		try {
			allProfiles = await adminApi.profiles.list();
		} catch (err) {
			allProfilesError = err instanceof ApiError ? err.message.slice(0, 35) : 'Failed to load profiles';
		} finally {
			allProfilesLoading = false;
		}
	}

	async function loadAllRequests() {
		if (allRequests !== null) return; // already loaded
		allRequestsLoading = true;
		allRequestsError = '';
		try {
			allRequests = await adminApi.requests.list();
		} catch (err) {
			allRequestsError = err instanceof ApiError ? err.message.slice(0, 35) : 'Failed to load requests';
		} finally {
			allRequestsLoading = false;
		}
	}

	async function loadAllUsers() {
		if (allUsers !== null) return; // already loaded
		allUsersLoading = true;
		allUsersError = '';
		try {
			allUsers = await adminApi.users.list();
		} catch (err) {
			allUsersError = err instanceof ApiError ? err.message.slice(0, 35) : 'Failed to load users';
		} finally {
			allUsersLoading = false;
		}
		// Grid initialised by $effect once usersGridDiv is bound and allUsers is populated
	}

	// Grid is created reactively when the div is available and data is loaded.
	// The $effect cleanup (return fn) destroys the grid when the div unmounts
	// (e.g. when the user switches away from the Users tab).
	$effect(() => {
		if (!usersGridDiv || !allUsers) return;
		if (usersGridApi) {
			// Already created — just refresh row data
			usersGridApi.setGridOption('rowData', allUsers);
			return;
		}

		const columnDefs = [
			{
				field: 'email', headerName: 'Email', flex: 2, filter: true, sortable: true,
				headerClass: 'mk-header',
			},
			{
				field: 'user_handle', headerName: 'Handle', flex: 1, filter: true, sortable: true,
				headerClass: 'mk-header',
				valueFormatter: (p: { value: string }) => `@${p.value}`
			},
			{
				field: 'full_name', headerName: 'Name', flex: 1, filter: true, sortable: true,
				headerClass: 'mk-header',
			},
			{
				field: 'phone_number', headerName: 'Phone', flex: 1,
				headerClass: 'mk-header',
			},
			{
				field: 'email_verified', headerName: 'Email Verified', width: 150, sortable: true,
				headerClass: 'mk-header',
				cellClass: (p: { value: boolean }) => p.value ? 'mk-cell-green' : 'mk-cell-amber',
				cellRenderer: (p: { value: boolean }) => p.value
					? '<span>&#10003; Verified</span>'
					: '<span>&#9888; Pending</span>'
			},
			{
				field: 'is_approved', headerName: 'Approved', width: 130, sortable: true,
				headerClass: 'mk-header',
				cellClass: (p: { value: boolean }) => p.value ? 'mk-cell-green' : 'mk-cell-amber',
				cellRenderer: (p: { value: boolean }) => p.value
					? '<span>&#10003; Approved</span>'
					: '<span>&mdash; Pending</span>'
			},
			{
				field: 'is_admin', headerName: 'Admin', width: 100, sortable: true,
				headerClass: 'mk-header',
				cellClass: (p: { value: boolean }) => p.value ? 'mk-cell-maroon' : '',
				cellRenderer: (p: { value: boolean }) => p.value ? '<span>&#9733; Admin</span>' : ''
			}
		];

		const gridOptions: GridOptions = {
			columnDefs,
			rowData: allUsers,
			rowSelection: { mode: 'singleRow', checkboxes: false, enableClickSelection: true },
			onRowClicked: (e) => { selectedUser = e.data as User; },
			defaultColDef: { resizable: true, floatingFilter: true, filter: true },
			pagination: true,
			paginationPageSize: 20,
			theme: 'legacy'
		};

		const api = createGrid(usersGridDiv, gridOptions);
		usersGridApi = api;

		return () => {
			api.destroy();
			usersGridApi = undefined;
		};
	});

	// ── User action functions ─────────────────────────────────────────────────────

	async function approveUser(u: User) {
		userActionLoading = true;
		try {
			const updated = await adminApi.users.approve(u.user_id);
			allUsers = allUsers!.map(x => x.user_id === u.user_id ? updated : x);
			selectedUser = updated;
			usersGridApi?.setGridOption('rowData', allUsers);
			toastStore.success('User approved');
		} catch (err) {
			toastStore.error(err instanceof ApiError ? err.message.slice(0, 35) : 'Action failed');
		} finally {
			userActionLoading = false;
		}
	}

	async function unapproveUser(u: User) {
		userActionLoading = true;
		try {
			const updated = await adminApi.users.unapprove(u.user_id);
			allUsers = allUsers!.map(x => x.user_id === u.user_id ? updated : x);
			selectedUser = updated;
			usersGridApi?.setGridOption('rowData', allUsers);
			toastStore.success('Approval revoked');
		} catch (err) {
			toastStore.error(err instanceof ApiError ? err.message.slice(0, 35) : 'Action failed');
		} finally {
			userActionLoading = false;
		}
	}

	async function promoteUserFromGrid(u: User) {
		userActionLoading = true;
		try {
			await adminApi.users.promote(u.user_id);
			allUsers = allUsers!.map(x => x.user_id === u.user_id ? { ...x, is_admin: true } : x);
			selectedUser = { ...u, is_admin: true };
			usersGridApi?.setGridOption('rowData', allUsers);
			toastStore.success('Promoted to admin');
		} catch (err) {
			toastStore.error(err instanceof ApiError ? err.message.slice(0, 35) : 'Action failed');
		} finally {
			userActionLoading = false;
		}
	}

	async function verifyEmailFromGrid(u: User) {
		userActionLoading = true;
		try {
			await adminApi.users.verifyEmail(u.user_id);
			allUsers = allUsers!.map(x => x.user_id === u.user_id ? { ...x, email_verified: true } : x);
			selectedUser = { ...u, email_verified: true };
			usersGridApi?.setGridOption('rowData', allUsers);
			toastStore.success('Email verified');
		} catch (err) {
			toastStore.error(err instanceof ApiError ? err.message.slice(0, 35) : 'Action failed');
		} finally {
			userActionLoading = false;
		}
	}

	onDestroy(() => {
		usersGridApi?.destroy();
	});

	function selectTab(tab: Tab) {
		activeTab = tab;
		if (tab === 'profiles') loadAllProfiles(); // no-op if already loaded
		if (tab === 'requests') loadAllRequests();
		if (tab === 'users') loadAllUsers();
	}

	// ── Profile actions (pending tab legacy — kept for dashboard stat cards) ─────

	async function approveProfile(p: PendingProfileSummary) {
		actionLoading[p.id] = true;
		try {
			await adminApi.profiles.approve(p.id);
			dashboard!.pending_profiles = dashboard!.pending_profiles.filter(x => x.id !== p.id);
			dashboard!.stats.profiles_pending = Math.max(0, dashboard!.stats.profiles_pending - 1);
			dashboard!.stats.profiles_approved += 1;
			toastStore.success('Profile approved');
		} catch (err) {
			toastStore.error(err instanceof ApiError ? err.message.slice(0, 35) : 'Action failed');
		} finally {
			actionLoading[p.id] = false;
		}
	}

	async function rejectProfile(p: PendingProfileSummary) {
		const notes = rejectNotes[p.id] ?? '';
		if (!notes.trim()) { toastStore.error('Add a rejection reason'); return; }
		actionLoading[p.id] = true;
		try {
			await adminApi.profiles.reject(p.id, notes);
			dashboard!.pending_profiles = dashboard!.pending_profiles.filter(x => x.id !== p.id);
			dashboard!.stats.profiles_pending = Math.max(0, dashboard!.stats.profiles_pending - 1);
			rejectOpen[p.id] = false;
			toastStore.success('Profile rejected');
		} catch (err) {
			toastStore.error(err instanceof ApiError ? err.message.slice(0, 35) : 'Action failed');
		} finally {
			actionLoading[p.id] = false;
		}
	}

	// ── Request actions (legacy — kept for type compat) ──────────────────────────

	async function approveRequest(r: PendingRequest) {
		actionLoading[r.id] = true;
		try {
			await adminApi.requests.approve(r.id);
			dashboard!.pending_requests = dashboard!.pending_requests.filter(x => x.id !== r.id);
			dashboard!.stats.requests_pending = Math.max(0, dashboard!.stats.requests_pending - 1);
			toastStore.success('Request approved — email sent');
		} catch (err) {
			toastStore.error(err instanceof ApiError ? err.message.slice(0, 35) : 'Action failed');
		} finally {
			actionLoading[r.id] = false;
		}
	}

	async function rejectRequest(r: PendingRequest) {
		const notes = rejectNotes[r.id] ?? '';
		if (!notes.trim()) { toastStore.error('Add a rejection reason'); return; }
		actionLoading[r.id] = true;
		try {
			await adminApi.requests.reject(r.id, notes);
			dashboard!.pending_requests = dashboard!.pending_requests.filter(x => x.id !== r.id);
			dashboard!.stats.requests_pending = Math.max(0, dashboard!.stats.requests_pending - 1);
			rejectOpen[r.id] = false;
			toastStore.success('Request rejected');
		} catch (err) {
			toastStore.error(err instanceof ApiError ? err.message.slice(0, 35) : 'Action failed');
		} finally {
			actionLoading[r.id] = false;
		}
	}

	// ── Inline profile approve/reject (Profiles tab, works on full Profile) ──────

	async function approvePendingProfile(p: Profile) {
		actionLoading[p.id] = true;
		try {
			await adminApi.profiles.approve(p.id);
			allProfiles = allProfiles!.map(x => x.id === p.id ? { ...x, status: 'approved' as const } : x);
			toastStore.success('Profile approved');
		} catch (err) {
			toastStore.error(err instanceof ApiError ? err.message.slice(0, 60) : 'Action failed');
		} finally {
			actionLoading[p.id] = false;
		}
	}

	async function rejectPendingProfile(p: Profile) {
		const notes = rejectNotes[p.id] ?? '';
		if (!notes.trim()) { toastStore.error('Add a rejection reason'); return; }
		actionLoading[p.id] = true;
		try {
			await adminApi.profiles.reject(p.id, notes);
			allProfiles = allProfiles!.map(x => x.id === p.id ? { ...x, status: 'rejected' as const } : x);
			rejectOpen[p.id] = false;
			toastStore.success('Profile rejected');
		} catch (err) {
			toastStore.error(err instanceof ApiError ? err.message.slice(0, 60) : 'Action failed');
		} finally {
			actionLoading[p.id] = false;
		}
	}

	function toggleRejectProfile(id: string) {
		rejectOpen[id] = !rejectOpen[id];
		if (!rejectOpen[id]) rejectNotes[id] = '';
	}

	// ── Inline request approve/reject (Requests tab, works on full DetailRequest) ─

	async function approvePendingRequest(r: DetailRequest) {
		actionLoading[r.id] = true;
		try {
			await adminApi.requests.approve(r.id);
			allRequests = allRequests!.map(x => x.id === r.id ? { ...x, status: 'approved' as const } : x);
			toastStore.success('Request approved — email sent');
		} catch (err) {
			toastStore.error(err instanceof ApiError ? err.message.slice(0, 60) : 'Action failed');
		} finally {
			actionLoading[r.id] = false;
		}
	}

	async function rejectPendingRequest(r: DetailRequest) {
		const notes = rejectNotes[r.id] ?? '';
		if (!notes.trim()) { toastStore.error('Add a rejection reason'); return; }
		actionLoading[r.id] = true;
		try {
			await adminApi.requests.reject(r.id, notes);
			allRequests = allRequests!.map(x => x.id === r.id ? { ...x, status: 'rejected' as const } : x);
			rejectOpen[r.id] = false;
			toastStore.success('Request rejected');
		} catch (err) {
			toastStore.error(err instanceof ApiError ? err.message.slice(0, 60) : 'Action failed');
		} finally {
			actionLoading[r.id] = false;
		}
	}

	function toggleRejectRequest(id: string) {
		rejectOpen[id] = !rejectOpen[id];
		if (!rejectOpen[id]) rejectNotes[id] = '';
	}

	// ── Helpers ──────────────────────────────────────────────────────────────────

	function fmtDate(iso: string) {
		return new Date(iso).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' });
	}

	function truncateId(id: string) {
		return id.slice(0, 8) + '…';
	}

	function statusBadgeClass(status: string) {
		switch (status) {
			case 'approved': return 'badge-approved';
			case 'pending':  return 'badge-pending';
			case 'rejected': return 'badge-rejected';
			default:         return 'badge-draft';
		}
	}

</script>

<svelte:head>
	<title>Admin Dashboard — Maratha Kalyanam</title>
</svelte:head>

<div class="mx-auto max-w-6xl px-4 py-10">
	<h1 class="font-serif text-3xl font-bold text-maroon">Admin Dashboard</h1>
	<p class="mt-1 text-sm text-ink/60">Platform overview and quick approvals</p>

	<!-- ── Stats row (always visible) ────────────────────────────────────────── -->
	{#if loading}
		<div class="my-6 flex items-center justify-center py-10">
			<Loader size={36} class="animate-spin text-saffron" />
		</div>
	{:else if error}
		<div class="my-6 rounded-lg border border-vermilion/30 bg-vermilion/5 p-4 text-vermilion">{error}</div>
	{:else if dashboard}
		<div class="my-6 grid grid-cols-1 gap-4 sm:grid-cols-3">
			<!-- Users card -->
			<div class="card space-y-3">
				<div class="flex items-center gap-2">
					<Users size={20} class="text-saffron shrink-0" />
					<span class="font-serif font-semibold text-maroon">Users</span>
					<span class="ml-auto tabular-nums text-2xl font-bold text-ink">{dashboard.stats.users}</span>
				</div>
				<div class="flex flex-wrap gap-2">
					<button
						class="rounded-full border border-amber-300 bg-amber-50 px-3 py-1 text-xs font-semibold text-amber-700 hover:bg-amber-100 transition-colors"
						onclick={() => selectTab('users')}
						title="View all users"
					>
						&#9888; Unverified: {dashboard.pending_users.length}
					</button>
					<button
						class="rounded-full border border-green-300 bg-green-50 px-3 py-1 text-xs font-semibold text-green-700 hover:bg-green-100 transition-colors"
						onclick={() => selectTab('users')}
						title="View all users"
					>
						&#10003; Verified: {dashboard.stats.users - dashboard.pending_users.length}
					</button>
				</div>
			</div>

			<!-- Profiles card -->
			<div class="card space-y-3">
				<div class="flex items-center gap-2">
					<UserCheck size={20} class="text-gold shrink-0" />
					<span class="font-serif font-semibold text-maroon">Profiles</span>
					<span class="ml-auto tabular-nums text-2xl font-bold text-ink">{dashboard.stats.profiles_total}</span>
				</div>
				<div class="flex flex-wrap gap-2">
					<button
						class="rounded-full border border-amber-300 bg-amber-50 px-3 py-1 text-xs font-semibold text-amber-700 hover:bg-amber-100 transition-colors"
						onclick={() => { selectTab('profiles'); profileStatusFilter = 'pending'; }}
						title="View pending profiles"
					>
						&#9203; Pending: {dashboard.stats.profiles_pending}
					</button>
					<button
						class="rounded-full border border-green-300 bg-green-50 px-3 py-1 text-xs font-semibold text-green-700 hover:bg-green-100 transition-colors"
						onclick={() => { selectTab('profiles'); profileStatusFilter = 'approved'; }}
						title="View approved profiles"
					>
						&#10003; Approved: {dashboard.stats.profiles_approved}
					</button>
					<button
						class="rounded-full border border-ink/20 bg-ink/5 px-3 py-1 text-xs font-semibold text-ink/60 hover:bg-ink/10 transition-colors"
						onclick={() => { selectTab('profiles'); profileStatusFilter = 'all'; }}
						title="View all profiles"
					>
						All profiles &rarr;
					</button>
				</div>
			</div>

			<!-- Requests card -->
			<div class="card space-y-3">
				<div class="flex items-center gap-2">
					<Inbox size={20} class="text-sky-500 shrink-0" />
					<span class="font-serif font-semibold text-maroon">Requests</span>
					<span class="ml-auto tabular-nums text-2xl font-bold text-ink">{dashboard.stats.requests_pending}</span>
				</div>
				<div class="flex flex-wrap gap-2">
					<button
						class="rounded-full border border-amber-300 bg-amber-50 px-3 py-1 text-xs font-semibold text-amber-700 hover:bg-amber-100 transition-colors"
						onclick={() => { selectTab('requests'); requestStatusFilter = 'pending'; }}
						title="View pending requests"
					>
						&#9203; Pending: {dashboard.stats.requests_pending}
					</button>
					<button
						class="rounded-full border border-ink/20 bg-ink/5 px-3 py-1 text-xs font-semibold text-ink/60 hover:bg-ink/10 transition-colors"
						onclick={() => { selectTab('requests'); requestStatusFilter = 'all'; }}
						title="View all requests"
					>
						All requests &rarr;
					</button>
				</div>
			</div>
		</div>
	{/if}

	<!-- ── Content area ───────────────────────────────────────────────────────── -->
	{#if activeTab === 'profiles'}
		{#if allProfilesLoading}
			<div class="flex items-center justify-center py-20">
				<Loader size={36} class="animate-spin text-saffron" />
			</div>
		{:else if allProfilesError}
			<div class="rounded-lg border border-vermilion/30 bg-vermilion/5 p-4 text-vermilion">{allProfilesError}</div>
		{:else if allProfiles}
			<div class="mb-3 flex flex-wrap items-center justify-between gap-3">
				<h2 class="font-serif text-xl font-semibold text-maroon">All Profiles</h2>
				<span class="text-sm text-ink/50">
					{allProfiles.filter(p => profileStatusFilter === 'all' || p.status === profileStatusFilter).length}
					{profileStatusFilter === 'all' ? 'total' : profileStatusFilter}
				</span>
			</div>
			<!-- Status filter pills -->
			<div class="mb-4 flex flex-wrap gap-1.5">
				{#each ['all', 'pending', 'approved', 'rejected', 'draft'] as s}
					{@const count = s === 'all' ? allProfiles.length : allProfiles.filter(p => p.status === s).length}
					<button
						class="rounded-full px-3 py-1 text-xs font-semibold border transition-all {profileStatusFilter === s
							? 'bg-maroon text-cream border-maroon'
							: 'bg-white text-ink/60 border-gold/40 hover:border-maroon/40 hover:text-maroon'}"
						onclick={() => { profileStatusFilter = s as typeof profileStatusFilter; }}
					>
						{s === 'all' ? 'All' : s.charAt(0).toUpperCase() + s.slice(1)}
						<span class="ml-1 opacity-70">({count})</span>
					</button>
				{/each}
			</div>
			{#if allProfiles.filter(p => profileStatusFilter === 'all' || p.status === profileStatusFilter).length === 0}
				<div class="card text-sm text-ink/60">No {profileStatusFilter === 'all' ? '' : profileStatusFilter} profiles found.</div>
			{:else}
				<div class="overflow-x-auto rounded-lg border border-gold/30 bg-white shadow-sm">
					<table class="w-full text-sm">
						<thead>
							<tr class="border-b border-gold/30 bg-[#6b0f1a] text-left text-xs font-bold text-cream uppercase tracking-wider">
								<th class="px-4 py-3">Name</th>
								<th class="px-4 py-3">Gender</th>
								<th class="px-4 py-3">Status</th>
								<th class="px-4 py-3">City · State</th>
								<th class="px-4 py-3">Education</th>
								<th class="px-4 py-3">Submitted</th>
								<th class="px-4 py-3">Actions</th>
							</tr>
						</thead>
						<tbody class="divide-y divide-gold/20">
							{#each allProfiles.filter(p => profileStatusFilter === 'all' || p.status === profileStatusFilter) as p (p.id)}
								<tr class="hover:bg-cream/40 transition-colors">
									<td class="px-4 py-3 font-medium text-ink">{p.first_name} {p.last_name}</td>
									<td class="px-4 py-3 text-ink/70 capitalize">{p.gender}</td>
									<td class="px-4 py-3">
										<span class={statusBadgeClass(p.status)}>{p.status}</span>
									</td>
									<td class="px-4 py-3 text-ink/70">{p.city}{p.state ? `, ${p.state}` : ''}</td>
									<td class="px-4 py-3 text-ink/60 text-xs">{p.education ?? '—'}</td>
									<td class="px-4 py-3 text-ink/50 text-xs">{fmtDate(p.created_at)}</td>
									<td class="px-4 py-3">
										{#if profileStatusFilter === 'pending'}
											<div class="flex items-center gap-1.5">
												<button
													class="rounded px-2 py-1 text-xs font-semibold bg-green-600 text-white hover:bg-green-700 transition-colors disabled:opacity-50"
													disabled={actionLoading[p.id]}
													onclick={() => approvePendingProfile(p)}
													title="Approve this profile"
												>
													{actionLoading[p.id] ? '…' : '✓'}
												</button>
												<button
													class="rounded px-2 py-1 text-xs font-semibold bg-vermilion text-white hover:bg-red-700 transition-colors disabled:opacity-50"
													disabled={actionLoading[p.id]}
													onclick={() => toggleRejectProfile(p.id)}
													title="Reject this profile"
												>
													✕
												</button>
												<a href="/profiles/{p.id}" class="text-saffron hover:underline text-xs ml-1">View</a>
											</div>
											{#if rejectOpen[p.id]}
												<div class="flex gap-1.5 mt-1.5">
													<input
														type="text"
														class="input text-xs flex-1"
														placeholder="Rejection reason"
														bind:value={rejectNotes[p.id]}
													/>
													<button
														class="rounded px-2 py-1 text-xs font-semibold bg-vermilion text-white hover:bg-red-700 disabled:opacity-50"
														disabled={actionLoading[p.id]}
														onclick={() => rejectPendingProfile(p)}
													>
														Confirm
													</button>
												</div>
											{/if}
										{:else}
											<a href="/profiles/{p.id}" class="text-saffron hover:underline text-xs">View &rarr;</a>
										{/if}
									</td>
								</tr>
							{/each}
						</tbody>
					</table>
				</div>
			{/if}
		{:else}
			<div class="flex items-center justify-center py-20">
				<Loader size={36} class="animate-spin text-saffron" />
			</div>
		{/if}

	<!-- ── All Requests tab ────────────────────────────────────────────────────── -->
	{:else if activeTab === 'requests'}
		{#if allRequestsLoading}
			<div class="flex items-center justify-center py-20">
				<Loader size={36} class="animate-spin text-saffron" />
			</div>
		{:else if allRequestsError}
			<div class="rounded-lg border border-vermilion/30 bg-vermilion/5 p-4 text-vermilion">{allRequestsError}</div>
		{:else if allRequests}
			<div class="mb-3 flex flex-wrap items-center justify-between gap-3">
				<h2 class="font-serif text-xl font-semibold text-maroon">All Requests</h2>
				<span class="text-sm text-ink/50">
					{allRequests.filter(r => requestStatusFilter === 'all' || r.status === requestStatusFilter).length}
					{requestStatusFilter === 'all' ? 'total' : requestStatusFilter}
				</span>
			</div>
			<!-- Status filter pills -->
			<div class="mb-4 flex flex-wrap gap-1.5">
				{#each ['all', 'pending', 'approved', 'rejected'] as s}
					{@const count = s === 'all' ? allRequests.length : allRequests.filter(r => r.status === s).length}
					<button
						class="rounded-full px-3 py-1 text-xs font-semibold border transition-all {requestStatusFilter === s
							? 'bg-maroon text-cream border-maroon'
							: 'bg-white text-ink/60 border-gold/40 hover:border-maroon/40 hover:text-maroon'}"
						onclick={() => { requestStatusFilter = s as typeof requestStatusFilter; }}
					>
						{s === 'all' ? 'All' : s.charAt(0).toUpperCase() + s.slice(1)}
						<span class="ml-1 opacity-70">({count})</span>
					</button>
				{/each}
			</div>
			{#if allRequests.filter(r => requestStatusFilter === 'all' || r.status === requestStatusFilter).length === 0}
				<div class="card text-sm text-ink/60">No {requestStatusFilter === 'all' ? '' : requestStatusFilter} requests found.</div>
			{:else}
				<div class="overflow-x-auto rounded-lg border border-gold/30 bg-white shadow-sm">
					<table class="w-full text-sm">
						<thead>
							<tr class="border-b border-gold/30 bg-[#6b0f1a] text-left text-xs font-bold text-cream uppercase tracking-wider">
								<th class="px-4 py-3">Request ID</th>
								<th class="px-4 py-3">Requester</th>
								<th class="px-4 py-3">Profile</th>
								<th class="px-4 py-3">Status</th>
								<th class="px-4 py-3">Date</th>
								<th class="px-4 py-3">Actions</th>
							</tr>
						</thead>
						<tbody class="divide-y divide-gold/20">
							{#each allRequests.filter(r => requestStatusFilter === 'all' || r.status === requestStatusFilter) as r (r.id)}
								<tr class="hover:bg-cream/40 transition-colors">
									<td class="px-4 py-3 font-mono text-xs text-ink/40">{r.id.slice(0, 8)}…</td>
									<td class="px-4 py-3 font-mono text-xs text-ink/60">{r.requester_user_id.slice(0, 8)}…</td>
									<td class="px-4 py-3 font-mono text-xs text-ink/60">{r.profile_id.slice(0, 8)}…</td>
									<td class="px-4 py-3">
										<span class={statusBadgeClass(r.status)}>{r.status}</span>
									</td>
									<td class="px-4 py-3 text-ink/50 text-xs">{fmtDate(r.created_at)}</td>
									<td class="px-4 py-3">
										{#if requestStatusFilter === 'pending'}
											<div class="flex items-center gap-1.5">
												<button
													class="rounded px-2 py-1 text-xs font-semibold bg-green-600 text-white hover:bg-green-700 disabled:opacity-50"
													disabled={actionLoading[r.id]}
													onclick={() => approvePendingRequest(r)}
												>
													{actionLoading[r.id] ? '…' : '✓'}
												</button>
												<button
													class="rounded px-2 py-1 text-xs font-semibold bg-vermilion text-white hover:bg-red-700 disabled:opacity-50"
													disabled={actionLoading[r.id]}
													onclick={() => toggleRejectRequest(r.id)}
												>✕</button>
											</div>
											{#if rejectOpen[r.id]}
												<div class="flex gap-1.5 mt-1.5">
													<input
														type="text"
														class="input text-xs flex-1"
														placeholder="Rejection reason"
														bind:value={rejectNotes[r.id]}
													/>
													<button
														class="rounded px-2 py-1 text-xs font-semibold bg-vermilion text-white disabled:opacity-50"
														disabled={actionLoading[r.id]}
														onclick={() => rejectPendingRequest(r)}
													>Confirm</button>
												</div>
											{/if}
										{/if}
									</td>
								</tr>
							{/each}
						</tbody>
					</table>
				</div>
			{/if}
		{:else}
			<div class="flex items-center justify-center py-20">
				<Loader size={36} class="animate-spin text-saffron" />
			</div>
		{/if}

	<!-- ── All Users tab ───────────────────────────────────────────────────────── -->
	{:else if activeTab === 'users'}
		{#if allUsersLoading}
			<div class="flex items-center justify-center py-20">
				<Loader size={36} class="animate-spin text-saffron" />
			</div>
		{:else if allUsersError}
			<div class="rounded-lg border border-vermilion/30 bg-vermilion/5 p-4 text-vermilion">{allUsersError}</div>
		{:else if allUsers !== null}
			<div class="mb-3 flex items-center justify-between">
				<h2 class="font-serif text-xl font-semibold text-maroon">All Users</h2>
				<span class="text-sm text-ink/50">{allUsers.length} total · click a row to act</span>
			</div>
			{#if allUsers.length === 0}
				<div class="card text-sm text-ink/60">No users found.</div>
			{:else}
				<!-- Quick search -->
				<div class="mb-3 flex items-center gap-2">
					<input
						type="search"
						placeholder="Search users…"
						class="input text-sm w-64"
						oninput={(e) => usersGridApi?.setGridOption('quickFilterText', e.currentTarget.value)}
					/>
				</div>

				<!-- ag-Grid container -->
				<div bind:this={usersGridDiv} class="ag-theme-quartz w-full rounded-lg overflow-hidden border border-[#c8a96e] shadow-sm" style="height: 480px;
					--ag-header-background-color: #6b0f1a;
					--ag-header-foreground-color: #fff8e7;
					--ag-header-column-separator-display: block;
					--ag-header-column-separator-color: #a01428;
					--ag-header-column-separator-width: 1px;
					--ag-cell-horizontal-border: solid #e8dcc8;
					--ag-row-border-color: #e8dcc8;
					--ag-row-border-width: 1px;
					--ag-selected-row-background-color: #fdf3e7;
					--ag-row-hover-color: #fdf8f0;
					--ag-font-size: 13px;
					--ag-grid-size: 6px;
					--ag-list-item-height: 36px;
					--ag-header-height: 42px;
				"></div>

				<!-- Selected-user action panel -->
				{#if selectedUser}
					<div class="mt-4 flex flex-wrap items-center gap-3 rounded-lg border border-gold/30 bg-white px-5 py-4 shadow-sm">
						<div class="min-w-0 flex-1">
							<p class="font-medium text-ink truncate">{selectedUser.email}</p>
							<p class="text-xs text-ink/50">
								@{selectedUser.user_handle}
								{#if selectedUser.is_admin} · <span class="text-saffron font-semibold">Admin</span>{/if}
								{#if selectedUser.email_verified} · <span class="text-green-600">Email verified</span>{:else} · <span class="text-marigold">Unverified email</span>{/if}
								{#if selectedUser.is_approved} · <span class="text-green-600">Approved</span>{:else} · <span class="text-marigold">Not approved</span>{/if}
							</p>
						</div>
						<div class="flex flex-wrap gap-2 shrink-0">
							{#if !selectedUser.is_approved}
								<button
									class="btn-primary text-sm px-4 py-1.5 flex items-center gap-1.5"
									disabled={userActionLoading}
									onclick={() => approveUser(selectedUser!)}
								>
									{#if userActionLoading}<Loader size={13} class="animate-spin" />{/if}
									Approve User
								</button>
							{:else}
								<button
									class="btn-secondary text-sm px-4 py-1.5"
									disabled={userActionLoading}
									onclick={() => unapproveUser(selectedUser!)}
								>
									Revoke Approval
								</button>
							{/if}
							{#if !selectedUser.email_verified}
								<button
									class="btn-secondary text-sm px-4 py-1.5 flex items-center gap-1.5"
									disabled={userActionLoading}
									onclick={() => verifyEmailFromGrid(selectedUser!)}
								>
									<ShieldCheck size={14} />
									Verify Email
								</button>
							{/if}
							{#if !selectedUser.is_admin}
								<button
									class="btn-secondary text-sm px-4 py-1.5"
									disabled={userActionLoading}
									onclick={() => promoteUserFromGrid(selectedUser!)}
								>
									Make Admin
								</button>
							{/if}
						</div>
					</div>
				{/if}
			{/if}

			<!-- Broadcast Email section -->
			<div class="mt-8 rounded-lg border border-gold/30 bg-white p-5 shadow-sm">
				<h3 class="font-serif text-lg font-semibold text-maroon mb-4">Send Broadcast Email</h3>
				{#if broadcastResult}
					<div class="mb-3 rounded border border-green-300 bg-green-50 px-4 py-2 text-sm text-green-800">
						Sent: {broadcastResult.sent} · Failed: {broadcastResult.failed}
					</div>
				{/if}
				<div class="space-y-3">
					<input
						type="text"
						class="input w-full"
						placeholder="Subject"
						bind:value={broadcastSubject}
					/>
					<textarea
						class="input w-full h-28 resize-y font-mono text-sm"
						placeholder="HTML body…"
						bind:value={broadcastBody}
					></textarea>
					<div class="flex flex-wrap items-center gap-4">
						<label class="flex items-center gap-2 text-sm">
							<input type="checkbox" bind:checked={broadcastVerifiedOnly} class="rounded" />
							Verified emails only
						</label>
						<label class="flex items-center gap-2 text-sm">
							<input type="checkbox" bind:checked={broadcastApprovedOnly} class="rounded" />
							Approved users only
						</label>
						<button
							class="btn-primary ml-auto px-6"
							disabled={broadcastSending}
							onclick={sendBroadcast}
						>
							{#if broadcastSending}<Loader size={14} class="inline animate-spin mr-1" />{/if}
							Send Broadcast
						</button>
					</div>
				</div>
			</div>
		{/if}

	{/if}

</div>

<style>
	/* ag-Grid header decoration */
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
	/* Status cell colours */
	:global(.ag-theme-quartz .mk-cell-green) {
		color: #166534 !important;
		font-weight: 600;
	}
	:global(.ag-theme-quartz .mk-cell-amber) {
		color: #92400e !important;
		font-weight: 600;
	}
	:global(.ag-theme-quartz .mk-cell-maroon) {
		color: #6b0f1a !important;
		font-weight: 700;
	}
	/* Sort/filter icons in header */
	:global(.ag-theme-quartz .mk-header .ag-sort-indicator-icon),
	:global(.ag-theme-quartz .mk-header .ag-header-icon) {
		color: #ffb627 !important;
		opacity: 1 !important;
	}
	/* Floating filter row */
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
</style>
