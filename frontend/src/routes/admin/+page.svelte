<script lang="ts">
	import { onMount, onDestroy } from 'svelte';
	import { createGrid, ModuleRegistry, AllCommunityModule, type GridApi, type GridOptions } from 'ag-grid-community';
	import 'ag-grid-community/styles/ag-grid.css';
	import 'ag-grid-community/styles/ag-theme-quartz.css';

	// ag-Grid v33+ requires explicit module registration — without this the grid
	// silently fails to render rows even though createGrid returns an api object.
	ModuleRegistry.registerModules([AllCommunityModule]);
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
		ShieldCheck,
		Trash2
	} from 'lucide-svelte';

	let { data } = $props();
	let loggedInUser = $derived<User | null>(data.user ?? null);

	// ── Tab state ────────────────────────────────────────────────────────────────

	type Tab = 'profiles' | 'requests' | 'users';
	let activeTab = $state<Tab>('users');

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
	let profileStatusFilter = $state<'all' | 'pending' | 'approved' | 'rejected' | 'draft' | null>(null);

	// ── All Requests tab state ───────────────────────────────────────────────────

	let allRequests = $state<DetailRequest[] | null>(null);
	let allRequestsLoading = $state(false);
	let allRequestsError = $state('');
	let requestStatusFilter = $state<'all' | 'pending' | 'approved' | 'rejected' | null>(null);

	// ── All Users tab state ──────────────────────────────────────────────────────

	let allUsers = $state<User[] | null>(null);
	let allUsersLoading = $state(false);
	let allUsersError = $state('');
	let userFilter = $state<'all' | 'unverified' | 'verified' | null>(null);
	// When false (default), admins are hidden from the Users grid so the
	// list shows just regular users. Toggle to true to include admins.
	let userIncludeAdmins = $state(false);

	// Stat-card display counts for the Users tab — depend on dashboard +
	// the include-admins toggle. Derived so they update when either changes.
	let usersTotal = $derived(
		dashboard
			? userIncludeAdmins
				? dashboard.stats.users
				: dashboard.stats.users - (dashboard.stats.users_admins ?? 0)
			: 0
	);
	let usersUnverified = $derived(dashboard?.pending_users.length ?? 0);
	let usersVerified = $derived(Math.max(0, usersTotal - usersUnverified));

	// ag-Grid state
	let usersGridApi: GridApi | undefined;
	let selectedUser = $state<User | null>(null);
	let userActionLoading = $state(false);

	// Profiles grid
	let profilesGridApi: GridApi | undefined;
	let selectedProfile = $state<Profile | null>(null);
	let profileActionLoading = $state(false);
	let profileRejectNote = $state('');
	let profileRejectOpen = $state(false);

	// Requests grid
	let requestsGridApi: GridApi | undefined;
	let selectedRequest = $state<DetailRequest | null>(null);
	let requestActionLoading = $state(false);
	let requestRejectNote = $state('');
	let requestRejectOpen = $state(false);


	// Content section anchor for scroll-into-view on tab change
	let contentSectionEl = $state<HTMLElement | undefined>();

	// ── Mount: dashboard only — full lists fetched lazily on chip click ──────────

	onMount(async () => {
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
	}

	// ── User action functions ─────────────────────────────────────────────────────

	async function approveUser(u: User) {
		userActionLoading = true;
		try {
			const updated = await adminApi.users.approve(u.uuid);
			allUsers = allUsers!.map(x => x.uuid === u.uuid ? updated : x);
			selectedUser = updated;
			usersGridApi?.setGridOption('rowData', [...computeUsersRows(userFilter)]);
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
			const updated = await adminApi.users.unapprove(u.uuid);
			allUsers = allUsers!.map(x => x.uuid === u.uuid ? updated : x);
			selectedUser = updated;
			usersGridApi?.setGridOption('rowData', [...computeUsersRows(userFilter)]);
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
			await adminApi.users.promote(u.uuid);
			allUsers = allUsers!.map(x => x.uuid === u.uuid ? { ...x, is_admin: true } : x);
			selectedUser = { ...u, is_admin: true };
			usersGridApi?.setGridOption('rowData', [...computeUsersRows(userFilter)]);
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
			await adminApi.users.verifyEmail(u.uuid);
			allUsers = allUsers!.map(x => x.uuid === u.uuid ? { ...x, email_verified: true } : x);
			selectedUser = { ...u, email_verified: true };
			usersGridApi?.setGridOption('rowData', [...computeUsersRows(userFilter)]);
			toastStore.success('Email verified');
		} catch (err) {
			toastStore.error(err instanceof ApiError ? err.message.slice(0, 35) : 'Action failed');
		} finally {
			userActionLoading = false;
		}
	}

	async function demoteUserFromGrid(u: User) {
		userActionLoading = true;
		try {
			const updated = await adminApi.users.demote(u.uuid);
			allUsers = allUsers!.map(x => x.uuid === u.uuid ? updated : x);
			selectedUser = updated;
			usersGridApi?.setGridOption('rowData', [...computeUsersRows(userFilter)]);
			toastStore.success('Admin demoted');
		} catch (err) {
			toastStore.error(err instanceof ApiError ? err.message.slice(0, 35) : 'Action failed');
		} finally {
			userActionLoading = false;
		}
	}

	async function deleteUserFromGrid(u: User) {
		if (!confirm(`Delete user "${u.email}"? This cannot be undone.`)) return;
		userActionLoading = true;
		try {
			await adminApi.users.delete(u.uuid);
			allUsers = allUsers!.filter(x => x.uuid !== u.uuid);
			selectedUser = null;
			usersGridApi?.setGridOption('rowData', [...computeUsersRows(userFilter)]);
			if (dashboard) {
				dashboard.stats.users = Math.max(0, dashboard.stats.users - 1);
			}
			toastStore.success('User deleted');
		} catch (err) {
			toastStore.error(err instanceof ApiError ? err.message.slice(0, 35) : 'Action failed');
		} finally {
			userActionLoading = false;
		}
	}

	async function doApproveProfile() {
		if (!selectedProfile) return;
		profileActionLoading = true;
		try {
			await adminApi.profiles.approve(selectedProfile.id);
			allProfiles = allProfiles!.map(p => p.id === selectedProfile!.id ? { ...p, status: 'approved' as const } : p);
			selectedProfile = { ...selectedProfile, status: 'approved' };
			profilesGridApi?.setGridOption('rowData', [...computeProfilesRows(profileStatusFilter)]);
			toastStore.success('Profile approved');
		} catch (err) {
			toastStore.error(err instanceof ApiError ? err.message.slice(0, 60) : 'Action failed');
		} finally {
			profileActionLoading = false;
		}
	}

	async function doRejectProfile() {
		if (!selectedProfile || !profileRejectNote.trim()) { toastStore.error('Add a rejection reason'); return; }
		profileActionLoading = true;
		try {
			await adminApi.profiles.reject(selectedProfile.id, profileRejectNote.trim());
			allProfiles = allProfiles!.map(p => p.id === selectedProfile!.id ? { ...p, status: 'rejected' as const } : p);
			selectedProfile = { ...selectedProfile, status: 'rejected' };
			profileRejectOpen = false;
			profileRejectNote = '';
			profilesGridApi?.setGridOption('rowData', [...computeProfilesRows(profileStatusFilter)]);
			toastStore.success('Profile rejected');
		} catch (err) {
			toastStore.error(err instanceof ApiError ? err.message.slice(0, 60) : 'Action failed');
		} finally {
			profileActionLoading = false;
		}
	}

	async function doDeleteProfile() {
		if (!selectedProfile) return;
		const label = `${selectedProfile.profile_number} (${selectedProfile.first_name} ${selectedProfile.last_name ?? ''})`.trim();
		if (!confirm(`Delete profile ${label}? This cannot be undone — photos and detail requests on this profile are also removed.`)) {
			return;
		}
		profileActionLoading = true;
		try {
			await adminApi.profiles.delete(selectedProfile.id);
			const wasStatus = selectedProfile.status;
			allProfiles = (allProfiles ?? []).filter(p => p.id !== selectedProfile!.id);
			selectedProfile = null;
			profileRejectOpen = false;
			profileRejectNote = '';
			profilesGridApi?.setGridOption('rowData', [...computeProfilesRows(profileStatusFilter)]);
			// Decrement dashboard counters so chip totals stay accurate
			if (dashboard) {
				dashboard.stats.profiles_total = Math.max(0, dashboard.stats.profiles_total - 1);
				const k = `profiles_${wasStatus}` as keyof typeof dashboard.stats;
				const cur = dashboard.stats[k];
				if (typeof cur === 'number') (dashboard.stats[k] as number) = Math.max(0, cur - 1);
			}
			toastStore.success('Profile deleted');
		} catch (err) {
			toastStore.error(err instanceof ApiError ? err.message.slice(0, 60) : 'Action failed');
		} finally {
			profileActionLoading = false;
		}
	}

	async function doApproveRequest() {
		if (!selectedRequest) return;
		requestActionLoading = true;
		try {
			await adminApi.requests.approve(selectedRequest.id);
			allRequests = allRequests!.map(r => r.id === selectedRequest!.id ? { ...r, status: 'approved' as const } : r);
			selectedRequest = { ...selectedRequest, status: 'approved' };
			requestsGridApi?.setGridOption('rowData', [...computeRequestsRows(requestStatusFilter)]);
			toastStore.success('Request approved — email sent');
		} catch (err) {
			toastStore.error(err instanceof ApiError ? err.message.slice(0, 60) : 'Action failed');
		} finally {
			requestActionLoading = false;
		}
	}

	async function doRejectRequest() {
		if (!selectedRequest || !requestRejectNote.trim()) { toastStore.error('Add a rejection reason'); return; }
		requestActionLoading = true;
		try {
			await adminApi.requests.reject(selectedRequest.id, requestRejectNote.trim());
			allRequests = allRequests!.map(r => r.id === selectedRequest!.id ? { ...r, status: 'rejected' as const } : r);
			selectedRequest = { ...selectedRequest, status: 'rejected' };
			requestRejectOpen = false;
			requestRejectNote = '';
			requestsGridApi?.setGridOption('rowData', [...computeRequestsRows(requestStatusFilter)]);
			toastStore.success('Request rejected');
		} catch (err) {
			toastStore.error(err instanceof ApiError ? err.message.slice(0, 60) : 'Action failed');
		} finally {
			requestActionLoading = false;
		}
	}

	async function doDeleteRequest() {
		if (!selectedRequest) return;
		const label = selectedRequest.request_number || selectedRequest.id.slice(0, 8) + '…';
		if (!confirm(`Delete request ${label}? This cannot be undone.`)) return;
		requestActionLoading = true;
		try {
			await adminApi.requests.delete(selectedRequest.id);
			const wasStatus = selectedRequest.status;
			allRequests = (allRequests ?? []).filter(r => r.id !== selectedRequest!.id);
			selectedRequest = null;
			requestRejectOpen = false;
			requestRejectNote = '';
			requestsGridApi?.setGridOption('rowData', [...computeRequestsRows(requestStatusFilter)]);
			if (dashboard) {
				dashboard.stats.requests_total = Math.max(0, dashboard.stats.requests_total - 1);
				const k = `requests_${wasStatus}` as keyof typeof dashboard.stats;
				const cur = dashboard.stats[k];
				if (typeof cur === 'number') (dashboard.stats[k] as number) = Math.max(0, cur - 1);
			}
			toastStore.success('Request deleted');
		} catch (err) {
			toastStore.error(err instanceof ApiError ? err.message.slice(0, 60) : 'Action failed');
		} finally {
			requestActionLoading = false;
		}
	}

	onDestroy(() => {
		usersGridApi?.destroy();
		usersGridApi = undefined;
		profilesGridApi?.destroy();
		profilesGridApi = undefined;
		requestsGridApi?.destroy();
		requestsGridApi = undefined;
	});

	function selectTab(tab: Tab) {
		// Clear selection when leaving a tab so stale panels don't persist
		if (activeTab !== tab) {
			if (activeTab === 'profiles') { selectedProfile = null; profileRejectOpen = false; }
			if (activeTab === 'requests') { selectedRequest = null; requestRejectOpen = false; }
			if (activeTab === 'users') selectedUser = null;
		}
		activeTab = tab;
		// Lists are fetched lazily by applyXFilter — header click alone doesn't load
		setTimeout(() => contentSectionEl?.scrollIntoView({ behavior: 'smooth', block: 'nearest' }), 50);
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

	// ── Helpers ──────────────────────────────────────────────────────────────────

	function computeUsersRows(f: typeof userFilter): User[] {
		if (!f || !allUsers) return [];
		let rows: User[];
		if (f === 'unverified') rows = allUsers.filter((u: any) => !u.email_verified);
		else if (f === 'verified') rows = allUsers.filter((u: any) => u.email_verified);
		else rows = allUsers; // 'all'
		// Hide admins by default — operator opts in via the "Include admins" checkbox.
		if (!userIncludeAdmins) rows = rows.filter((u: any) => !u.is_admin);
		return rows;
	}

	function computeProfilesRows(f: typeof profileStatusFilter): Profile[] {
		if (!f || !allProfiles) return [];
		if (f === 'all') return allProfiles;
		return allProfiles.filter(p => p.status === f);
	}

	function computeRequestsRows(f: typeof requestStatusFilter): DetailRequest[] {
		if (!f || !allRequests) return [];
		if (f === 'all') return allRequests;
		return allRequests.filter(r => r.status === f);
	}

	function applyUserFilter(f: typeof userFilter) {
		userFilter = f;
		selectedUser = null;
		if (f) loadAllUsers(); // lazy fetch on chip click
	}

	function applyProfileFilter(f: typeof profileStatusFilter) {
		profileStatusFilter = f;
		selectedProfile = null;
		profileRejectOpen = false;
		if (f) loadAllProfiles();
	}

	function applyRequestFilter(f: typeof requestStatusFilter) {
		requestStatusFilter = f;
		selectedRequest = null;
		requestRejectOpen = false;
		if (f) loadAllRequests();
	}

	// ── Grid actions (use:action pattern) ────────────────────────────────────────

	function usersGridAction(node: HTMLDivElement, data: User[]) {
		const makeGrid = (rows: User[]) => {
			usersGridApi?.destroy();
			const columnDefs = [
				{ field: 'email', headerName: 'Email', width: 260, filter: true, sortable: true, headerClass: 'mk-header' },
				{ field: 'user_id', headerName: 'User ID', width: 160, filter: true, sortable: true, headerClass: 'mk-header' },
				{ field: 'full_name', headerName: 'Name', width: 180, filter: true, sortable: true, headerClass: 'mk-header' },
				{ field: 'phone_number', headerName: 'Phone', width: 150, headerClass: 'mk-header' },
				{ field: 'email_verified', headerName: 'Email Verified', width: 150, sortable: true, headerClass: 'mk-header',
				  cellClass: (p: { value: boolean }) => p.value ? 'mk-cell-green' : 'mk-cell-amber',
				  cellRenderer: (p: { value: boolean }) => p.value ? '<span>&#10003; Verified</span>' : '<span>&#9888; Pending</span>' },
				{ field: 'is_approved', headerName: 'Approved', width: 130, sortable: true, headerClass: 'mk-header',
				  cellClass: (p: { value: boolean }) => p.value ? 'mk-cell-green' : 'mk-cell-amber',
				  cellRenderer: (p: { value: boolean }) => p.value ? '<span>&#10003; Approved</span>' : '<span>&mdash; Pending</span>' },
				{ field: 'is_admin', headerName: 'Admin', width: 100, sortable: true, headerClass: 'mk-header',
				  cellClass: (p: { value: boolean }) => p.value ? 'mk-cell-maroon' : '',
				  cellRenderer: (p: { value: boolean }) => p.value ? '<span>&#9733; Admin</span>' : '' }
			];
			usersGridApi = createGrid(node, {
				columnDefs: columnDefs as any[],
				rowData: [...rows],
				rowSelection: { mode: 'singleRow', checkboxes: false, enableClickSelection: true },
				onRowClicked: (e) => { selectedUser = e.data as User; },
				defaultColDef: { resizable: true, floatingFilter: true, filter: true },
				pagination: true, paginationPageSize: 20, theme: 'legacy'
			});
		};
		makeGrid(data);
		return {
			destroy: () => { usersGridApi?.destroy(); usersGridApi = undefined; }
		};
	}

	function profilesGridAction(node: HTMLDivElement, data: Profile[]) {
		const makeGrid = (rows: Profile[]) => {
			profilesGridApi?.destroy();
			const columnDefs = [
				{ field: 'profile_number', headerName: 'ID', width: 130, sortable: true, filter: true, headerClass: 'mk-header',
				  cellStyle: { fontFamily: 'monospace', fontSize: '12px', color: '#6b7280' } },
				{ headerName: 'Name', width: 200, sortable: true, filter: true, headerClass: 'mk-header',
				  valueGetter: (p: { data: Profile }) => `${p.data.first_name} ${p.data.last_name ?? ''}`.trim() },
				{ field: 'gender', headerName: 'Gender', width: 100, sortable: true, filter: true, headerClass: 'mk-header',
				  valueFormatter: (p: { value: string }) => p.value.charAt(0).toUpperCase() + p.value.slice(1) },
				{ field: 'status', headerName: 'Status', width: 120, sortable: true, filter: true, headerClass: 'mk-header',
				  cellRenderer: (p: { value: string }) => {
					const styles: Record<string, string> = { approved: 'background:#dcfce7;color:#16a34a', pending: 'background:#fef3c7;color:#92400e', rejected: 'background:#fee2e2;color:#dc2626', draft: 'background:#f3f4f6;color:#6b7280' };
					return `<span style="display:inline-block;padding:1px 8px;border-radius:9999px;font-size:11px;font-weight:600;${styles[p.value] ?? ''}">${p.value}</span>`;
				  }},
				{ headerName: 'Location', width: 200, filter: true, headerClass: 'mk-header',
				  valueGetter: (p: { data: Profile }) => [p.data.city, p.data.state].filter(Boolean).join(', ') },
				{ field: 'education', headerName: 'Education', width: 180, filter: true, sortable: true, headerClass: 'mk-header' },
				{ field: 'created_at', headerName: 'Submitted', width: 130, sortable: true, headerClass: 'mk-header',
				  valueFormatter: (p: { value: string }) => new Date(p.value).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' }) }
			];
			profilesGridApi = createGrid(node, {
				columnDefs: columnDefs as any[],
				rowData: [...rows],
				rowSelection: { mode: 'singleRow', checkboxes: false, enableClickSelection: true },
				onRowClicked: (e) => { selectedProfile = e.data as Profile; profileRejectOpen = false; profileRejectNote = ''; },
				defaultColDef: { resizable: true, floatingFilter: true, filter: true },
				pagination: true, paginationPageSize: 20, theme: 'legacy'
			});
		};
		makeGrid(data);
		return {
			destroy: () => { profilesGridApi?.destroy(); profilesGridApi = undefined; }
		};
	}

	function requestsGridAction(node: HTMLDivElement, data: DetailRequest[]) {
		const makeGrid = (rows: DetailRequest[]) => {
			requestsGridApi?.destroy();
			const columnDefs = [
				{ field: 'request_number', headerName: 'Request ID', width: 150, sortable: true, filter: true, headerClass: 'mk-header',
				  cellStyle: { fontFamily: 'monospace', fontSize: '12px', color: '#6b7280' } },
				{ field: 'profile_number', headerName: 'Profile ID', width: 130, sortable: true, filter: true, headerClass: 'mk-header',
				  cellStyle: { fontFamily: 'monospace', fontSize: '12px', color: '#6b7280' } },
				{ headerName: 'Profile Name', width: 200, sortable: true, filter: true, headerClass: 'mk-header',
				  valueGetter: (p: { data: DetailRequest }) => `${p.data.profile_first_name ?? ''} ${p.data.profile_last_name ?? ''}`.trim() || '—' },
				{ field: 'profile_gender', headerName: 'Gender', width: 100, sortable: true, headerClass: 'mk-header',
				  valueFormatter: (p: { value: string | null }) => p.value ? p.value.charAt(0).toUpperCase() + p.value.slice(1) : '' },
				{ field: 'profile_city', headerName: 'City', width: 140, sortable: true, filter: true, headerClass: 'mk-header' },
				{ field: 'requester_email', headerName: 'Requester', width: 240, sortable: true, filter: true, headerClass: 'mk-header' },
				{ field: 'status', headerName: 'Status', width: 120, sortable: true, filter: true, headerClass: 'mk-header',
				  cellRenderer: (p: { value: string }) => {
					const styles: Record<string, string> = { approved: 'background:#dcfce7;color:#16a34a', pending: 'background:#fef3c7;color:#92400e', rejected: 'background:#fee2e2;color:#dc2626' };
					return `<span style="display:inline-block;padding:1px 8px;border-radius:9999px;font-size:11px;font-weight:600;${styles[p.value] ?? ''}">${p.value}</span>`;
				  }},
				{ field: 'created_at', headerName: 'Date', width: 130, sortable: true, headerClass: 'mk-header',
				  valueFormatter: (p: { value: string }) => new Date(p.value).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' }) }
			];
			requestsGridApi = createGrid(node, {
				columnDefs: columnDefs as any[],
				rowData: [...rows],
				rowSelection: { mode: 'singleRow', checkboxes: false, enableClickSelection: true },
				onRowClicked: (e) => { selectedRequest = e.data as DetailRequest; requestRejectOpen = false; requestRejectNote = ''; },
				defaultColDef: { resizable: true, floatingFilter: true, filter: true },
				pagination: true, paginationPageSize: 20, theme: 'legacy'
			});
		};
		makeGrid(data);
		return {
			destroy: () => { requestsGridApi?.destroy(); requestsGridApi = undefined; }
		};
	}

</script>

<svelte:head>
	<title>Dashboard — Maratha Kalyanam</title>
</svelte:head>

<div class="mx-auto max-w-6xl px-4 py-10">
	<h1 class="font-serif text-3xl font-bold text-maroon">Dashboard</h1>
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

			<!-- ── All Users card ─────────────────────────────────────────── -->
			<div class="overflow-hidden rounded-xl border shadow-sm transition-all {activeTab === 'users' ? 'border-maroon shadow-md' : 'border-gold/40 hover:border-maroon/40 hover:shadow-md'}">
				<button
					class="flex w-full items-center gap-3 px-4 py-3 text-left transition-colors {activeTab === 'users' ? 'bg-maroon' : 'bg-white hover:bg-maroon/5'}"
					onclick={() => { selectTab('users'); applyUserFilter(null); }}
				>
					<Users size={20} class="text-saffron shrink-0" />
					<span class="font-serif font-semibold {activeTab === 'users' ? 'text-cream' : 'text-maroon'}">Users</span>
					<span class="ml-auto tabular-nums text-2xl font-bold {activeTab === 'users' ? 'text-cream' : 'text-ink'}">{usersTotal}</span>
				</button>
				<div class="flex flex-wrap items-center gap-2 bg-white px-4 py-3">
					<button
						class="rounded-full border px-3 py-1 text-xs font-semibold transition-colors {activeTab === 'users' && userFilter === 'all' ? 'border-maroon bg-maroon text-cream' : 'border-gray-300 bg-gray-50 text-gray-600 hover:bg-gray-100'}"
						onclick={() => { selectTab('users'); applyUserFilter('all'); }}
					>All</button>
					{#if usersUnverified > 0}
						<button
							class="rounded-full border px-3 py-1 text-xs font-semibold transition-colors {activeTab === 'users' && userFilter === 'unverified' ? 'border-maroon bg-maroon text-cream' : 'border-amber-300 bg-amber-50 text-amber-700 hover:bg-amber-100'}"
							onclick={() => { selectTab('users'); applyUserFilter('unverified'); }}
						>Unverified · {usersUnverified}</button>
					{/if}
					{#if usersVerified > 0}
						<button
							class="rounded-full border px-3 py-1 text-xs font-semibold transition-colors {activeTab === 'users' && userFilter === 'verified' ? 'border-maroon bg-maroon text-cream' : 'border-green-300 bg-green-50 text-green-700 hover:bg-green-100'}"
							onclick={() => { selectTab('users'); applyUserFilter('verified'); }}
						>Verified · {usersVerified}</button>
					{/if}
					<label class="ml-auto inline-flex cursor-pointer items-center gap-1.5 text-xs text-ink/60">
						<input
							type="checkbox"
							class="rounded accent-maroon"
							bind:checked={userIncludeAdmins}
						/>
						Include admins
					</label>
				</div>
			</div>

			<!-- ── All Profiles card ───────────────────────────────────────── -->
			<div class="overflow-hidden rounded-xl border shadow-sm transition-all {activeTab === 'profiles' ? 'border-maroon shadow-md' : 'border-gold/40 hover:border-maroon/40 hover:shadow-md'}">
				<button
					class="flex w-full items-center gap-3 px-4 py-3 text-left transition-colors {activeTab === 'profiles' ? 'bg-maroon' : 'bg-white hover:bg-maroon/5'}"
					onclick={() => { selectTab('profiles'); applyProfileFilter(null); }}
				>
					<UserCheck size={20} class="{activeTab === 'profiles' ? 'text-saffron' : 'text-gold'} shrink-0" />
					<span class="font-serif font-semibold {activeTab === 'profiles' ? 'text-cream' : 'text-maroon'}">Profiles</span>
					<span class="ml-auto tabular-nums text-2xl font-bold {activeTab === 'profiles' ? 'text-cream' : 'text-ink'}">{dashboard.stats.profiles_total}</span>
				</button>
				<div class="flex flex-wrap gap-2 bg-white px-4 py-3">
					<button
						class="rounded-full border px-3 py-1 text-xs font-semibold transition-colors {activeTab === 'profiles' && profileStatusFilter === 'all' ? 'border-maroon bg-maroon text-cream' : 'border-gray-300 bg-gray-50 text-gray-600 hover:bg-gray-100'}"
						onclick={() => { selectTab('profiles'); applyProfileFilter('all'); }}
					>All</button>
					{#if dashboard.stats.profiles_pending > 0}
						<button
							class="rounded-full border px-3 py-1 text-xs font-semibold transition-colors {activeTab === 'profiles' && profileStatusFilter === 'pending' ? 'border-maroon bg-maroon text-cream' : 'border-amber-300 bg-amber-50 text-amber-700 hover:bg-amber-100'}"
							onclick={() => { selectTab('profiles'); applyProfileFilter('pending'); }}
						>Pending · {dashboard.stats.profiles_pending}</button>
					{/if}
					{#if dashboard.stats.profiles_approved > 0}
						<button
							class="rounded-full border px-3 py-1 text-xs font-semibold transition-colors {activeTab === 'profiles' && profileStatusFilter === 'approved' ? 'border-maroon bg-maroon text-cream' : 'border-green-300 bg-green-50 text-green-700 hover:bg-green-100'}"
							onclick={() => { selectTab('profiles'); applyProfileFilter('approved'); }}
						>Approved · {dashboard.stats.profiles_approved}</button>
					{/if}
					{#if dashboard.stats.profiles_rejected > 0}
						<button
							class="rounded-full border px-3 py-1 text-xs font-semibold transition-colors {activeTab === 'profiles' && profileStatusFilter === 'rejected' ? 'border-maroon bg-maroon text-cream' : 'border-red-300 bg-red-50 text-red-700 hover:bg-red-100'}"
							onclick={() => { selectTab('profiles'); applyProfileFilter('rejected'); }}
						>Rejected · {dashboard.stats.profiles_rejected}</button>
					{/if}
					{#if dashboard.stats.profiles_draft > 0}
						<button
							class="rounded-full border px-3 py-1 text-xs font-semibold transition-colors {activeTab === 'profiles' && profileStatusFilter === 'draft' ? 'border-maroon bg-maroon text-cream' : 'border-blue-300 bg-blue-50 text-blue-700 hover:bg-blue-100'}"
							onclick={() => { selectTab('profiles'); applyProfileFilter('draft'); }}
						>Draft · {dashboard.stats.profiles_draft}</button>
					{/if}
				</div>
			</div>

			<!-- ── All Requests card ───────────────────────────────────────── -->
			<div class="overflow-hidden rounded-xl border shadow-sm transition-all {activeTab === 'requests' ? 'border-maroon shadow-md' : 'border-gold/40 hover:border-maroon/40 hover:shadow-md'}">
				<button
					class="flex w-full items-center gap-3 px-4 py-3 text-left transition-colors {activeTab === 'requests' ? 'bg-maroon' : 'bg-white hover:bg-maroon/5'}"
					onclick={() => { selectTab('requests'); applyRequestFilter(null); }}
				>
					<Inbox size={20} class="{activeTab === 'requests' ? 'text-saffron' : 'text-sky-500'} shrink-0" />
					<span class="font-serif font-semibold {activeTab === 'requests' ? 'text-cream' : 'text-maroon'}">Requests</span>
					<span class="ml-auto tabular-nums text-2xl font-bold {activeTab === 'requests' ? 'text-cream' : 'text-ink'}">{dashboard.stats.requests_total}</span>
				</button>
				<div class="flex flex-wrap gap-2 bg-white px-4 py-3">
					<button
						class="rounded-full border px-3 py-1 text-xs font-semibold transition-colors {activeTab === 'requests' && requestStatusFilter === 'all' ? 'border-maroon bg-maroon text-cream' : 'border-gray-300 bg-gray-50 text-gray-600 hover:bg-gray-100'}"
						onclick={() => { selectTab('requests'); applyRequestFilter('all'); }}
					>All</button>
					{#if dashboard.stats.requests_pending > 0}
						<button
							class="rounded-full border px-3 py-1 text-xs font-semibold transition-colors {activeTab === 'requests' && requestStatusFilter === 'pending' ? 'border-maroon bg-maroon text-cream' : 'border-amber-300 bg-amber-50 text-amber-700 hover:bg-amber-100'}"
							onclick={() => { selectTab('requests'); applyRequestFilter('pending'); }}
						>Pending · {dashboard.stats.requests_pending}</button>
					{/if}
					{#if dashboard.stats.requests_approved > 0}
						<button
							class="rounded-full border px-3 py-1 text-xs font-semibold transition-colors {activeTab === 'requests' && requestStatusFilter === 'approved' ? 'border-maroon bg-maroon text-cream' : 'border-green-300 bg-green-50 text-green-700 hover:bg-green-100'}"
							onclick={() => { selectTab('requests'); applyRequestFilter('approved'); }}
						>Approved · {dashboard.stats.requests_approved}</button>
					{/if}
					{#if dashboard.stats.requests_rejected > 0}
						<button
							class="rounded-full border px-3 py-1 text-xs font-semibold transition-colors {activeTab === 'requests' && requestStatusFilter === 'rejected' ? 'border-maroon bg-maroon text-cream' : 'border-red-300 bg-red-50 text-red-700 hover:bg-red-100'}"
							onclick={() => { selectTab('requests'); applyRequestFilter('rejected'); }}
						>Rejected · {dashboard.stats.requests_rejected}</button>
					{/if}
				</div>
			</div>

		</div>

	{/if}

	<!-- anchor for scroll-into-view when stat card is clicked -->
	<div bind:this={contentSectionEl}></div>
	{#if activeTab === 'users'}
		{#if userFilter === null}
			<div class="card text-sm text-ink/60 text-center py-6">Click a chip above to view users.</div>
		{:else if allUsersLoading}
			<div class="flex items-center justify-center py-20">
				<Loader size={36} class="animate-spin text-saffron" />
			</div>
		{:else if allUsersError}
			<div class="rounded-lg border border-vermilion/30 bg-vermilion/5 p-4 text-vermilion">{allUsersError}</div>
		{:else if allUsers !== null}
			{#if allUsers.length === 0}
				<div class="card text-sm text-ink/60">No users found.</div>
			{:else}
				<!-- ag-Grid container -->
				{#key `${userFilter}:${userIncludeAdmins}`}
				<div use:usersGridAction={computeUsersRows(userFilter)} class="ag-theme-quartz w-full rounded-lg overflow-hidden border border-[#c8a96e] shadow-sm" style="height: 480px;
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
				{/key}

				<!-- Selected-user action panel -->
				{#if selectedUser}
					<div class="mt-4 rounded-lg border border-gold/30 bg-white px-5 py-4 shadow-sm">
						<div class="min-w-0">
							<p class="font-medium text-ink truncate">{selectedUser.email}</p>
							<p class="text-xs text-ink/50">
								{selectedUser.user_id}
								{#if selectedUser.is_admin} · <span class="text-saffron font-semibold">Admin</span>{/if}
								{#if selectedUser.email_verified} · <span class="text-green-600">Email verified</span>{:else} · <span class="text-marigold">Unverified email</span>{/if}
								{#if selectedUser.is_approved} · <span class="text-green-600">Approved</span>{:else} · <span class="text-marigold">Not approved</span>{/if}
							</p>
						</div>
						<div class="mt-3 flex flex-wrap gap-2">
							{#if !selectedUser.is_approved}
								<button
									class="btn-primary text-sm px-4 py-1.5 flex items-center gap-1.5"
									disabled={userActionLoading}
									onclick={() => approveUser(selectedUser!)}
								>
									{#if userActionLoading}<Loader size={13} class="animate-spin" />{/if}
									Approve User
								</button>
							{:else if !selectedUser.is_admin || loggedInUser?.is_super}
								<!-- Revoking approval from an admin is super-only -->
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
							{#if loggedInUser?.is_super && selectedUser.is_admin}
								<button
									class="text-sm px-4 py-1.5 rounded border border-vermilion/40 bg-white text-vermilion hover:bg-vermilion/5 disabled:opacity-50 flex items-center gap-1.5"
									disabled={userActionLoading}
									onclick={() => demoteUserFromGrid(selectedUser!)}
								>
									Demote to User
								</button>
							{/if}
							{#if loggedInUser?.is_super || (loggedInUser?.is_admin && !selectedUser.is_admin)}
								<button
									class="text-sm px-4 py-1.5 rounded bg-vermilion text-cream hover:bg-vermilion/80 disabled:opacity-50 flex items-center gap-1.5"
									disabled={userActionLoading}
									onclick={() => deleteUserFromGrid(selectedUser!)}
								>
									<Trash2 size={13} />
									Delete User
								</button>
							{/if}
						</div>
					</div>
				{/if}
			{/if}

		{/if}

	<!-- ── All Profiles tab ────────────────────────────────────────────────────── -->
	{:else if activeTab === 'profiles'}
		{#if profileStatusFilter === null}
			<div class="card text-sm text-ink/60 text-center py-6">Click a chip above to view profiles.</div>
		{:else if allProfilesLoading}
			<div class="flex items-center justify-center py-20">
				<Loader size={36} class="animate-spin text-saffron" />
			</div>
		{:else if allProfilesError}
			<div class="rounded-lg border border-vermilion/30 bg-vermilion/5 p-4 text-vermilion">{allProfilesError}</div>
		{:else if allProfiles}
			<!-- ag-Grid -->
			{#key profileStatusFilter}
			<div use:profilesGridAction={computeProfilesRows(profileStatusFilter)}
				class="ag-theme-quartz w-full rounded-lg overflow-hidden border border-[#c8a96e] shadow-sm"
				style="height: 460px;
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
					--ag-header-height: 42px;"
			></div>
			{/key}

			<!-- Selected profile action panel -->
			{#if selectedProfile}
				<div class="mt-4 flex flex-wrap items-center gap-3 rounded-lg border border-gold/30 bg-white px-5 py-4 shadow-sm">
					<div class="min-w-0 flex-1">
						<p class="font-semibold text-ink">
							{selectedProfile.profile_number} — {selectedProfile.first_name} {selectedProfile.last_name ?? ''}
						</p>
						<p class="text-sm text-ink/60 capitalize">
							{selectedProfile.gender} · <span class="{selectedProfile.status === 'approved' ? 'text-green-600' : selectedProfile.status === 'rejected' ? 'text-vermilion' : 'text-saffron'} font-medium">{selectedProfile.status}</span>
							· {selectedProfile.city}{selectedProfile.state ? `, ${selectedProfile.state}` : ''}
						</p>
					</div>
					<div class="flex shrink-0 flex-wrap gap-2">
						<a href="/profiles/{selectedProfile.id}" class="btn-secondary text-xs px-4 py-2">View →</a>
						{#if selectedProfile.status === 'pending'}
							<button
								class="btn-primary text-xs px-4 py-2"
								disabled={profileActionLoading}
								onclick={doApproveProfile}
							>
								{#if profileActionLoading}<Loader size={12} class="inline animate-spin mr-1" />{/if}
								✓ Approve
							</button>
							<button
								class="btn-danger text-xs px-4 py-2"
								disabled={profileActionLoading}
								onclick={() => { profileRejectOpen = !profileRejectOpen; profileRejectNote = ''; }}
							>
								✕ Reject
							</button>
						{/if}
						<!-- Delete is always available on any profile status -->
						<button
							class="text-xs px-4 py-2 rounded bg-vermilion text-cream hover:bg-vermilion/90 disabled:opacity-50"
							disabled={profileActionLoading}
							onclick={doDeleteProfile}
						>
							{#if profileActionLoading}<Loader size={12} class="inline animate-spin mr-1" />{/if}
							🗑 Delete
						</button>
					</div>
				</div>
				{#if profileRejectOpen && selectedProfile.status === 'pending'}
					<div class="flex gap-2 mt-2">
						<input
							type="text"
							class="input flex-1 text-sm"
							placeholder="Rejection reason (required)"
							bind:value={profileRejectNote}
						/>
						<button
							class="btn-danger text-sm px-4"
							disabled={profileActionLoading}
							onclick={doRejectProfile}
						>
							{#if profileActionLoading}<Loader size={12} class="inline animate-spin mr-1" />{/if}
							Confirm
						</button>
					</div>
				{/if}
			{:else}
				<p class="mt-3 text-xs text-ink/40 text-center">Click a row to select and act on it</p>
			{/if}
		{:else}
			<div class="flex items-center justify-center py-20">
				<Loader size={36} class="animate-spin text-saffron" />
			</div>
		{/if}

	<!-- ── All Requests tab ────────────────────────────────────────────────────── -->
	{:else if activeTab === 'requests'}
		{#if requestStatusFilter === null}
			<div class="card text-sm text-ink/60 text-center py-6">Click a chip above to view requests.</div>
		{:else if allRequestsLoading}
			<div class="flex items-center justify-center py-20">
				<Loader size={36} class="animate-spin text-saffron" />
			</div>
		{:else if allRequestsError}
			<div class="rounded-lg border border-vermilion/30 bg-vermilion/5 p-4 text-vermilion">{allRequestsError}</div>
		{:else if allRequests}
			<!-- ag-Grid -->
			{#key requestStatusFilter}
			<div use:requestsGridAction={computeRequestsRows(requestStatusFilter)}
				class="ag-theme-quartz w-full rounded-lg overflow-hidden border border-[#c8a96e] shadow-sm"
				style="height: 400px;
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
					--ag-header-height: 42px;"
			></div>
			{/key}

			<!-- Selected request action panel -->
			{#if selectedRequest}
				<div class="mt-4 flex flex-wrap items-center gap-3 rounded-lg border border-gold/30 bg-white px-5 py-4 shadow-sm">
					<div class="min-w-0 flex-1">
						<p class="font-semibold text-ink font-mono text-sm">{selectedRequest.id.slice(0, 8)}…</p>
						<p class="text-sm text-ink/60">
							Status: <span class="{selectedRequest.status === 'approved' ? 'text-green-600' : selectedRequest.status === 'rejected' ? 'text-vermilion' : 'text-saffron'} font-medium capitalize">{selectedRequest.status}</span>
							{#if selectedRequest.message} · "{selectedRequest.message}"{/if}
						</p>
					</div>
					<div class="flex shrink-0 flex-wrap gap-2">
						{#if selectedRequest.status === 'pending'}
							<button
								class="btn-primary text-xs px-4 py-2"
								disabled={requestActionLoading}
								onclick={doApproveRequest}
							>
								{#if requestActionLoading}<Loader size={12} class="inline animate-spin mr-1" />{/if}
								✓ Approve
							</button>
							<button
								class="btn-danger text-xs px-4 py-2"
								disabled={requestActionLoading}
								onclick={() => { requestRejectOpen = !requestRejectOpen; requestRejectNote = ''; }}
							>
								✕ Reject
							</button>
						{/if}
						<!-- Delete is always available on any request status -->
						<button
							class="text-xs px-4 py-2 rounded bg-vermilion text-cream hover:bg-vermilion/90 disabled:opacity-50"
							disabled={requestActionLoading}
							onclick={doDeleteRequest}
						>
							{#if requestActionLoading}<Loader size={12} class="inline animate-spin mr-1" />{/if}
							🗑 Delete
						</button>
					</div>
				</div>
				{#if requestRejectOpen && selectedRequest.status === 'pending'}
					<div class="flex gap-2 mt-2">
						<input
							type="text"
							class="input flex-1 text-sm"
							placeholder="Rejection reason (required)"
							bind:value={requestRejectNote}
						/>
						<button
							class="btn-danger text-sm px-4"
							disabled={requestActionLoading}
							onclick={doRejectRequest}
						>
							{#if requestActionLoading}<Loader size={12} class="inline animate-spin mr-1" />{/if}
							Confirm
						</button>
					</div>
				{/if}
			{:else}
				<p class="mt-3 text-xs text-ink/40 text-center">Click a row to select and act on it</p>
			{/if}
		{:else}
			<div class="flex items-center justify-center py-20">
				<Loader size={36} class="animate-spin text-saffron" />
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
	/* --- Pagination panel: keep readable on mobile --- */
	/* Allow children to wrap onto multiple lines instead of overlapping. */
	:global(.ag-theme-quartz .ag-paging-panel) {
		flex-wrap: wrap !important;
		row-gap: 4px !important;
		column-gap: 8px !important;
		padding: 6px 10px !important;
		justify-content: center !important;
	}
	@media (max-width: 640px) {
		/* Hide the verbose "Page Size: 20" selector and the
		   "1 to 20 of 100" row-summary on small screens — pagination
		   buttons + "Page X of Y" still convey enough. */
		:global(.ag-theme-quartz .ag-paging-page-size),
		:global(.ag-theme-quartz .ag-paging-row-summary-panel) {
			display: none !important;
		}
		:global(.ag-theme-quartz .ag-paging-panel) {
			font-size: 12px !important;
			gap: 4px !important;
		}
		:global(.ag-theme-quartz .ag-paging-panel .ag-paging-button) {
			min-width: 28px !important;
			min-height: 28px !important;
			padding: 2px !important;
		}
	}
</style>
