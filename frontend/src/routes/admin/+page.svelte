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
		Trash2,
		XCircle,
		RotateCcw,
		Megaphone,
		Settings
	} from 'lucide-svelte';
	import { tx } from '$lib/i18n';
	import { langStore } from '$lib/stores/lang.svelte';
	import ConfirmDelete from '$lib/components/ConfirmDelete.svelte';
	import { userStatus } from '$lib/userStatus';

	let { data } = $props();
	let loggedInUser = $derived<User | null>(data.user ?? null);

	// ── Tab state ────────────────────────────────────────────────────────────────

	type Tab = 'profiles' | 'requests' | 'users';
	let activeTab = $state<Tab>('users');

	// ── Dashboard state ──────────────────────────────────────────────────────────

	let dashboard = $state<AdminDashboard | null>(null);
	let loading = $state(true);
	let error = $state('');

	// ── Shared ConfirmDelete modal ───────────────────────────────────────────────

	let confirmOpen = $state(false);
	let confirmTitle = $state('');
	let confirmDescription = $state('');
	let confirmCallback = $state<(() => Promise<void>) | null>(null);

	function openConfirm(title: string, description: string, callback: () => Promise<void>) {
		confirmTitle = title;
		confirmDescription = description;
		confirmCallback = callback;
		confirmOpen = true;
	}

	async function handleConfirm() {
		if (confirmCallback) await confirmCallback();
	}

	// Per-item action loading (legacy pending tab)
	let actionLoading = $state<Record<string, boolean>>({});

	// ── All Profiles tab state ───────────────────────────────────────────────────

	let allProfiles = $state<Profile[] | null>(null);
	let allProfilesLoading = $state(false);
	let allProfilesError = $state('');
	let profileStatusFilter = $state<'all' | 'pending' | 'approved' | 'revoked' | 'draft' | null>(null);

	// ── All Requests tab state ───────────────────────────────────────────────────

	let allRequests = $state<DetailRequest[] | null>(null);
	let allRequestsLoading = $state(false);
	let allRequestsError = $state('');
	let requestStatusFilter = $state<'all' | 'pending' | 'approved' | 'revoked' | null>(null);

	// ── All Users tab state ──────────────────────────────────────────────────────

	let allUsers = $state<User[] | null>(null);
	let allUsersLoading = $state(false);
	let allUsersError = $state('');
	let userFilter = $state<'all' | 'pending' | 'approved' | 'revoked' | null>(null);
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
	// userStatus() now returns 'revoked' | 'approved' | 'pending'
	let usersRevoked = $derived(
		(allUsers ?? []).filter(
			(u) => (!userIncludeAdmins ? !u.is_admin : true) && u.is_revoked
		).length
	);
	let usersPending = $derived(
		(allUsers ?? []).filter(
			(u) => (!userIncludeAdmins ? !u.is_admin : true) && !u.is_revoked && !(u.email_verified && u.is_approved)
		).length
	);
	let usersApproved = $derived(Math.max(0, usersTotal - usersPending - usersRevoked));

	// ag-Grid state
	let usersGridApi: GridApi | undefined;
	let selectedUser = $state<User | null>(null);
	let userActionLoading = $state(false);

	// Profiles grid
	let profilesGridApi: GridApi | undefined;
	let selectedProfile = $state<Profile | null>(null);
	let profileActionLoading = $state(false);

	// Requests grid
	let requestsGridApi: GridApi | undefined;
	let selectedRequest = $state<DetailRequest | null>(null);
	let requestActionLoading = $state(false);


	// Content section anchor for scroll-into-view on tab change
	let contentSectionEl = $state<HTMLElement | undefined>();

	// Format an integer byte count into a human-readable label.
	// Used by the dashboard photo-storage badge and the per-profile size column.
	function formatBytes(n: number): string {
		if (!n || n < 1024) return `${n} B`;
		if (n < 1024 * 1024) return `${(n / 1024).toFixed(1)} KB`;
		if (n < 1024 * 1024 * 1024) return `${(n / (1024 * 1024)).toFixed(1)} MB`;
		return `${(n / (1024 * 1024 * 1024)).toFixed(2)} GB`;
	}

	// Compute age in completed years from an ISO date string. Used by the
	// selected-profile action panel where we want a tight header without
	// status / location / gender clutter.
	function ageFromDob(dob: string | null | undefined): number | null {
		if (!dob) return null;
		const d = new Date(dob);
		if (Number.isNaN(d.getTime())) return null;
		const t = new Date();
		let a = t.getFullYear() - d.getFullYear();
		const md = t.getMonth() - d.getMonth();
		if (md < 0 || (md === 0 && t.getDate() < d.getDate())) a -= 1;
		return a;
	}

	// ── Mount: dashboard only — full lists fetched lazily on chip click ──────────

	/**
	 * Re-fetch the dashboard endpoint to keep the chip counts honest after a
	 * state-changing admin action. Necessary because:
	 *   - approve/revoke/reinstate moves a row between status buckets, and
	 *     the local mutations don't always know which counters to bump
	 *   - delete-user cascade-removes profiles + requests in the DB; the
	 *     frontend has no way to enumerate the cascaded rows from the UX
	 *     side, so a refetch is the only correct way to refresh totals
	 * One extra round-trip per admin action is fine — dashboard is a handful
	 * of cheap COUNT queries.
	 */
	async function refreshDashboardStats() {
		try {
			const fresh = await adminApi.dashboard();
			dashboard = fresh;
		} catch (err) {
			// Don't blow up the action — local stats just stay stale until
			// the next manual page refresh.
			console.warn('Failed to refresh dashboard stats', err);
		}
	}

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
			refreshDashboardStats();
			toastStore.success('User approved');
		} catch (err) {
			toastStore.error(err instanceof ApiError ? err.message.slice(0, 35) : 'Action failed');
		} finally {
			userActionLoading = false;
		}
	}

	// unapproveUser handler removed when the "Revoke Approval" button was
	// dropped from the action panel. The backend endpoint
	// /admin/users/{id}/unapprove and the api.users.unapprove() client
	// method are still available for scripted use.

	async function promoteUserFromGrid(u: User) {
		userActionLoading = true;
		try {
			await adminApi.users.promote(u.uuid);
			allUsers = allUsers!.map(x => x.uuid === u.uuid ? { ...x, is_admin: true } : x);
			selectedUser = { ...u, is_admin: true };
			usersGridApi?.setGridOption('rowData', [...computeUsersRows(userFilter)]);
			refreshDashboardStats();
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
			refreshDashboardStats();
			toastStore.success('Email verified');
		} catch (err) {
			toastStore.error(err instanceof ApiError ? err.message.slice(0, 35) : 'Action failed');
		} finally {
			userActionLoading = false;
		}
	}

	async function resendVerificationFromGrid(u: User) {
		userActionLoading = true;
		try {
			await adminApi.users.resendVerification(u.uuid);
			toastStore.success('Verification email re-sent');
		} catch (err) {
			toastStore.error(err instanceof ApiError ? err.message.slice(0, 50) : 'Action failed');
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
			refreshDashboardStats();
			toastStore.success('Admin demoted');
		} catch (err) {
			toastStore.error(err instanceof ApiError ? err.message.slice(0, 35) : 'Action failed');
		} finally {
			userActionLoading = false;
		}
	}

	async function revokeUser(u: User) {
		userActionLoading = true;
		try {
			const updated = await adminApi.users.revoke(u.uuid);
			allUsers = allUsers!.map(x => x.uuid === u.uuid ? updated : x);
			selectedUser = updated;
			usersGridApi?.setGridOption('rowData', [...computeUsersRows(userFilter)]);
			// User revoke G1-cascades pending requests → revoked. Refetch to
			// keep request stat tiles in sync.
			refreshDashboardStats();
			toastStore.success('User revoked');
		} catch (err) {
			toastStore.error(err instanceof ApiError ? err.message.slice(0, 35) : 'Action failed');
		} finally {
			userActionLoading = false;
		}
	}

	async function suspendUser(u: User) {
		userActionLoading = true;
		try {
			const updated = await adminApi.users.suspend(u.uuid);
			allUsers = allUsers!.map(x => x.uuid === u.uuid ? updated : x);
			selectedUser = updated;
			usersGridApi?.setGridOption('rowData', [...computeUsersRows(userFilter)]);
			refreshDashboardStats();
			toastStore.success('User suspended');
		} catch (err) {
			toastStore.error(err instanceof ApiError ? err.message.slice(0, 50) : 'Action failed');
		} finally {
			userActionLoading = false;
		}
	}

	async function unsuspendUser(u: User) {
		userActionLoading = true;
		try {
			const updated = await adminApi.users.unsuspend(u.uuid);
			allUsers = allUsers!.map(x => x.uuid === u.uuid ? updated : x);
			selectedUser = updated;
			usersGridApi?.setGridOption('rowData', [...computeUsersRows(userFilter)]);
			refreshDashboardStats();
			toastStore.success('User unsuspended');
		} catch (err) {
			toastStore.error(err instanceof ApiError ? err.message.slice(0, 50) : 'Action failed');
		} finally {
			userActionLoading = false;
		}
	}

	async function reinstateUser(u: User) {
		userActionLoading = true;
		try {
			const updated = await adminApi.users.reinstate(u.uuid);
			allUsers = allUsers!.map(x => x.uuid === u.uuid ? updated : x);
			selectedUser = updated;
			usersGridApi?.setGridOption('rowData', [...computeUsersRows(userFilter)]);
			refreshDashboardStats();
			toastStore.success('User reinstated');
		} catch (err) {
			toastStore.error(err instanceof ApiError ? err.message.slice(0, 35) : 'Action failed');
		} finally {
			userActionLoading = false;
		}
	}

	function startDeleteUser(u: User) {
		openConfirm(
			'Delete user?',
			`Permanently remove user "${u.email}" and all their profiles, photos, and requests. Cannot be undone.`,
			async () => {
				userActionLoading = true;
				try {
					await adminApi.users.delete(u.uuid);
					allUsers = allUsers!.filter(x => x.uuid !== u.uuid);
					// User delete cascade-removes profiles + photos + requests in
					// the DB. We can't enumerate the cascaded rows here, so drop
					// any locally-cached profile/request lists to force a fresh
					// fetch on next chip click, and refetch the dashboard for
					// accurate counts.
					allProfiles = null;
					allRequests = null;
					selectedUser = null;
					selectedProfile = null;
					selectedRequest = null;
					usersGridApi?.setGridOption('rowData', [...computeUsersRows(userFilter)]);
					refreshDashboardStats();
					toastStore.success('User deleted');
				} catch (err) {
					toastStore.error(err instanceof ApiError ? err.message.slice(0, 35) : 'Action failed');
				} finally {
					userActionLoading = false;
				}
			}
		);
	}

	async function doApproveProfile() {
		if (!selectedProfile) return;
		profileActionLoading = true;
		try {
			await adminApi.profiles.approve(selectedProfile.id);
			allProfiles = allProfiles!.map(p => p.id === selectedProfile!.id ? { ...p, status: 'approved' as const } : p);
			selectedProfile = { ...selectedProfile, status: 'approved' };
			profilesGridApi?.setGridOption('rowData', [...computeProfilesRows(profileStatusFilter)]);
			refreshDashboardStats();
			toastStore.success('Profile approved');
		} catch (err) {
			toastStore.error(err instanceof ApiError ? err.message.slice(0, 60) : 'Action failed');
		} finally {
			profileActionLoading = false;
		}
	}

	async function doRevokeProfile() {
		if (!selectedProfile) return;
		profileActionLoading = true;
		try {
			const updated = await adminApi.profiles.reject(selectedProfile.id);
			allProfiles = allProfiles!.map(p => p.id === selectedProfile!.id ? updated : p);
			selectedProfile = updated;
			profilesGridApi?.setGridOption('rowData', [...computeProfilesRows(profileStatusFilter)]);
			// Profile revoke G2-cascades pending requests for this profile.
			// Drop the cached request list so it refetches with the new state.
			allRequests = null;
			refreshDashboardStats();
			toastStore.success('Profile revoked');
		} catch (err) {
			toastStore.error(err instanceof ApiError ? err.message.slice(0, 60) : 'Action failed');
		} finally {
			profileActionLoading = false;
		}
	}

	async function doReinstateProfile() {
		if (!selectedProfile) return;
		profileActionLoading = true;
		try {
			const updated = await adminApi.profiles.reinstate(selectedProfile.id);
			allProfiles = allProfiles!.map(p => p.id === selectedProfile!.id ? updated : p);
			selectedProfile = updated;
			profilesGridApi?.setGridOption('rowData', [...computeProfilesRows(profileStatusFilter)]);
			refreshDashboardStats();
			toastStore.success('Profile reinstated');
		} catch (err) {
			toastStore.error(err instanceof ApiError ? err.message.slice(0, 60) : 'Action failed');
		} finally {
			profileActionLoading = false;
		}
	}

	function startDeleteProfile() {
		if (!selectedProfile) return;
		const label = `${selectedProfile.profile_number} (${selectedProfile.first_name} ${selectedProfile.last_name ?? ''})`.trim();
		openConfirm(
			'Reject + delete profile?',
			`Permanently remove profile ${label} and all photos. Cannot be undone.`,
			async () => {
				if (!selectedProfile) return;
				profileActionLoading = true;
				try {
					await adminApi.profiles.delete(selectedProfile.id);
					allProfiles = (allProfiles ?? []).filter(p => p.id !== selectedProfile!.id);
					// Profile delete cascades photos + detail-requests in the
					// DB; drop cached request list and refetch dashboard for
					// fresh counts.
					allRequests = null;
					selectedProfile = null;
					selectedRequest = null;
					profilesGridApi?.setGridOption('rowData', [...computeProfilesRows(profileStatusFilter)]);
					refreshDashboardStats();
					toastStore.success('Profile deleted');
				} catch (err) {
					toastStore.error(err instanceof ApiError ? err.message.slice(0, 60) : 'Action failed');
				} finally {
					profileActionLoading = false;
				}
			}
		);
	}

	async function doApproveRequest() {
		if (!selectedRequest) return;
		requestActionLoading = true;
		try {
			await adminApi.requests.approve(selectedRequest.id);
			allRequests = allRequests!.map(r => r.id === selectedRequest!.id ? { ...r, status: 'approved' as const } : r);
			selectedRequest = { ...selectedRequest, status: 'approved' };
			requestsGridApi?.setGridOption('rowData', [...computeRequestsRows(requestStatusFilter)]);
			refreshDashboardStats();
			toastStore.success('Request approved — email sent');
		} catch (err) {
			toastStore.error(err instanceof ApiError ? err.message.slice(0, 60) : 'Action failed');
		} finally {
			requestActionLoading = false;
		}
	}

	async function doRevokeRequest() {
		if (!selectedRequest) return;
		requestActionLoading = true;
		try {
			const updated = await adminApi.requests.reject(selectedRequest.id);
			allRequests = allRequests!.map(r => r.id === selectedRequest!.id ? updated : r);
			selectedRequest = updated;
			requestsGridApi?.setGridOption('rowData', [...computeRequestsRows(requestStatusFilter)]);
			refreshDashboardStats();
			toastStore.success('Request revoked');
		} catch (err) {
			toastStore.error(err instanceof ApiError ? err.message.slice(0, 60) : 'Action failed');
		} finally {
			requestActionLoading = false;
		}
	}

	async function doReinstateRequest() {
		if (!selectedRequest) return;
		requestActionLoading = true;
		try {
			const updated = await adminApi.requests.reinstate(selectedRequest.id);
			allRequests = allRequests!.map(r => r.id === selectedRequest!.id ? updated : r);
			selectedRequest = updated;
			requestsGridApi?.setGridOption('rowData', [...computeRequestsRows(requestStatusFilter)]);
			refreshDashboardStats();
			toastStore.success('Request reinstated');
		} catch (err) {
			toastStore.error(err instanceof ApiError ? err.message.slice(0, 60) : 'Action failed');
		} finally {
			requestActionLoading = false;
		}
	}

	function startDeleteRequest() {
		if (!selectedRequest) return;
		const label = selectedRequest.request_number || selectedRequest.id.slice(0, 8) + '…';
		openConfirm(
			'Reject + delete request?',
			`Permanently remove request ${label}. Cannot be undone.`,
			async () => {
				if (!selectedRequest) return;
				requestActionLoading = true;
				try {
					await adminApi.requests.delete(selectedRequest.id);
					allRequests = (allRequests ?? []).filter(r => r.id !== selectedRequest!.id);
					selectedRequest = null;
					requestsGridApi?.setGridOption('rowData', [...computeRequestsRows(requestStatusFilter)]);
					refreshDashboardStats();
					toastStore.success('Request deleted');
				} catch (err) {
					toastStore.error(err instanceof ApiError ? err.message.slice(0, 60) : 'Action failed');
				} finally {
					requestActionLoading = false;
				}
			}
		);
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
			if (activeTab === 'profiles') { selectedProfile = null; }
			if (activeTab === 'requests') { selectedRequest = null; }
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
			refreshDashboardStats();
			toastStore.success('Profile approved');
		} catch (err) {
			toastStore.error(err instanceof ApiError ? err.message.slice(0, 35) : 'Action failed');
		} finally {
			actionLoading[p.id] = false;
		}
	}

	async function rejectPendingProfile(p: PendingProfileSummary) {
		actionLoading[p.id] = true;
		try {
			await adminApi.profiles.reject(p.id);
			dashboard!.pending_profiles = dashboard!.pending_profiles.filter(x => x.id !== p.id);
			// Profile reject G2-cascades pending requests; drop their cache.
			allRequests = null;
			refreshDashboardStats();
			toastStore.success('Profile revoked');
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
			refreshDashboardStats();
			toastStore.success('Request approved — email sent');
		} catch (err) {
			toastStore.error(err instanceof ApiError ? err.message.slice(0, 35) : 'Action failed');
		} finally {
			actionLoading[r.id] = false;
		}
	}

	async function rejectPendingRequest(r: PendingRequest) {
		actionLoading[r.id] = true;
		try {
			await adminApi.requests.reject(r.id);
			dashboard!.pending_requests = dashboard!.pending_requests.filter(x => x.id !== r.id);
			refreshDashboardStats();
			toastStore.success('Request revoked');
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
		if (f === 'revoked') rows = allUsers.filter((u: any) => u.is_revoked);
		else if (f === 'pending') rows = allUsers.filter((u: any) => !u.is_revoked && !(u.email_verified && u.is_approved));
		else if (f === 'approved') rows = allUsers.filter((u: any) => !u.is_revoked && u.email_verified && u.is_approved);
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
		if (f) loadAllProfiles();
	}

	function applyRequestFilter(f: typeof requestStatusFilter) {
		requestStatusFilter = f;
		selectedRequest = null;
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
				{ headerName: 'Status', width: 140, sortable: true, headerClass: 'mk-header',
				  valueGetter: (p: { data: User }) => userStatus(p.data),
				  cellClass: (p: { value: string }) => p.value === 'approved' ? 'mk-cell-green' : p.value === 'revoked' ? 'mk-cell-vermilion' : 'mk-cell-amber',
				  cellRenderer: (p: { value: string }) => p.value === 'approved'
					? '<span style="display:inline-flex;align-items:center;gap:4px;background:#dcfce7;color:#166534;border-radius:9999px;padding:1px 8px;font-size:11px;font-weight:600">&#10003; Approved</span>'
					: p.value === 'revoked'
					? '<span style="display:inline-flex;align-items:center;gap:4px;background:#fee2e2;color:#dc2626;border-radius:9999px;padding:1px 8px;font-size:11px;font-weight:600">&#10005; Revoked</span>'
					: '<span style="display:inline-flex;align-items:center;gap:4px;background:#fef3c7;color:#92400e;border-radius:9999px;padding:1px 8px;font-size:11px;font-weight:600">&#9888; Pending</span>' },
				// Admin column is super-only — non-super admins don't see the
				// admin tier (it's filtered out of /admin/users for them, but
				// hide the column too in case the API ever leaks).
				...(loggedInUser?.is_super ? [{
					field: 'is_admin', headerName: 'Admin', width: 100, sortable: true, headerClass: 'mk-header',
					cellClass: (p: { value: boolean }) => p.value ? 'mk-cell-maroon' : '',
					cellRenderer: (p: { value: boolean }) => p.value ? '<span>&#9733; Admin</span>' : ''
				}] : [])
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
					const styles: Record<string, string> = { approved: 'background:#dcfce7;color:#16a34a', pending: 'background:#fef3c7;color:#92400e', revoked: 'background:#fee2e2;color:#dc2626', draft: 'background:#f3f4f6;color:#6b7280' };
					const label = p.value.charAt(0).toUpperCase() + p.value.slice(1);
					return `<span style="display:inline-block;padding:1px 8px;border-radius:9999px;font-size:11px;font-weight:600;${styles[p.value] ?? ''}">${label}</span>`;
				  }},
				{ headerName: 'Location', width: 200, filter: true, headerClass: 'mk-header',
				  valueGetter: (p: { data: Profile }) => [p.data.city, p.data.state].filter(Boolean).join(', ') },
				{ field: 'education', headerName: 'Education', width: 180, filter: true, sortable: true, headerClass: 'mk-header' },
				// Photo storage column — sortable by raw bytes; rendered as
				// "<count> · <size>" so admins can spot heavy profiles at a glance.
				{ headerName: 'Photos', width: 130, sortable: true, headerClass: 'mk-header',
				  valueGetter: (p: { data: Profile }) => p.data.photos_bytes ?? 0,
				  cellRenderer: (p: { data: Profile }) => {
					const c = p.data.photos_count ?? 0;
					const b = p.data.photos_bytes ?? 0;
					return c > 0 ? `${c} · ${formatBytes(b)}` : '<span style="color:#9ca3af">—</span>';
				  }},
				{ field: 'created_at', headerName: 'Submitted', width: 130, sortable: true, headerClass: 'mk-header',
				  valueFormatter: (p: { value: string }) => new Date(p.value).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' }) }
			];
			profilesGridApi = createGrid(node, {
				columnDefs: columnDefs as any[],
				rowData: [...rows],
				rowSelection: { mode: 'singleRow', checkboxes: false, enableClickSelection: true },
				onRowClicked: (e) => { selectedProfile = e.data as Profile; },
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
					const styles: Record<string, string> = { approved: 'background:#dcfce7;color:#16a34a', pending: 'background:#fef3c7;color:#92400e', revoked: 'background:#fee2e2;color:#dc2626' };
					const label = p.value.charAt(0).toUpperCase() + p.value.slice(1);
					return `<span style="display:inline-block;padding:1px 8px;border-radius:9999px;font-size:11px;font-weight:600;${styles[p.value] ?? ''}">${label}</span>`;
				  }},
				{ field: 'created_at', headerName: 'Date', width: 130, sortable: true, headerClass: 'mk-header',
				  valueFormatter: (p: { value: string }) => new Date(p.value).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' }) }
			];
			requestsGridApi = createGrid(node, {
				columnDefs: columnDefs as any[],
				rowData: [...rows],
				rowSelection: { mode: 'singleRow', checkboxes: false, enableClickSelection: true },
				onRowClicked: (e) => { selectedRequest = e.data as DetailRequest; },
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

<!-- Shared ConfirmDelete modal — one instance, reused for all entity types -->
<ConfirmDelete
	bind:open={confirmOpen}
	title={confirmTitle}
	description={confirmDescription}
	onConfirm={handleConfirm}
/>

<div class="mx-auto max-w-6xl px-4 py-10">
	<div class="flex flex-wrap items-start justify-between gap-3">
		<div>
			<h1 class="font-serif text-3xl font-bold text-maroon">Dashboard</h1>
			<p class="mt-1 text-sm text-ink/60">Platform overview and quick approvals</p>
		</div>
		<div class="flex flex-wrap items-center gap-2">
			<a href="/admin/settings" class="inline-flex items-center gap-1.5 rounded border border-gold/50 bg-white px-3 py-1.5 text-sm font-medium text-maroon hover:border-saffron hover:bg-cream transition-colors">
				<Settings size={15} />Settings
			</a>
			<a href="/admin/broadcast" class="inline-flex items-center gap-1.5 rounded border border-gold/50 bg-white px-3 py-1.5 text-sm font-medium text-maroon hover:border-saffron hover:bg-cream transition-colors">
				<Megaphone size={15} />Broadcast
			</a>
		</div>
	</div>

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
				<div class="relative {activeTab === 'users' ? 'bg-maroon' : 'bg-white hover:bg-maroon/5'}">
					<button
						class="flex w-full items-center gap-3 px-4 py-3 text-left transition-colors"
						onclick={() => { selectTab('users'); applyUserFilter(null); }}
					>
						<Users size={20} class="text-saffron shrink-0" />
						<span class="font-serif font-semibold {activeTab === 'users' ? 'text-cream' : 'text-maroon'}">Users</span>
						<span class="ml-auto tabular-nums text-2xl font-bold {activeTab === 'users' ? 'text-cream' : 'text-ink'}">{usersTotal}</span>
					</button>
					<!-- Admin / Super counts in the header — display-only, not
					     filter chips. Super-only (regular admins never see the
					     admin tier exists). Positioned absolutely so they stay
					     in the header band but don't hijack the click area. -->
					{#if loggedInUser?.is_super && (dashboard?.stats?.users_admins || dashboard?.stats?.users_super)}
						<div class="pointer-events-none absolute right-2 top-2 flex gap-1 text-[10px]">
							{#if dashboard?.stats?.users_admins}
								<span class="rounded bg-saffron/30 px-1.5 py-0.5 font-semibold text-maroon">A · {dashboard.stats.users_admins}</span>
							{/if}
							{#if dashboard?.stats?.users_super}
								<span class="rounded bg-maroon/40 px-1.5 py-0.5 font-semibold text-cream">S · {dashboard.stats.users_super}</span>
							{/if}
						</div>
					{/if}
				</div>
				<div class="flex flex-wrap items-center gap-2 bg-white px-4 py-3">
					<button
						class="rounded-full border px-3 py-1 text-xs font-semibold transition-colors {activeTab === 'users' && userFilter === 'all' ? 'border-maroon bg-maroon text-cream' : 'border-gray-300 bg-gray-50 text-gray-600 hover:bg-gray-100'}"
						onclick={() => { selectTab('users'); applyUserFilter('all'); }}
					>All</button>
					{#if usersPending > 0}
						<button
							class="rounded-full border px-3 py-1 text-xs font-semibold transition-colors {activeTab === 'users' && userFilter === 'pending' ? 'border-maroon bg-maroon text-cream' : 'border-amber-300 bg-amber-50 text-amber-700 hover:bg-amber-100'}"
							onclick={() => { selectTab('users'); applyUserFilter('pending'); }}
						>Pending · {usersPending}</button>
					{/if}
					{#if usersApproved > 0}
						<button
							class="rounded-full border px-3 py-1 text-xs font-semibold transition-colors {activeTab === 'users' && userFilter === 'approved' ? 'border-maroon bg-maroon text-cream' : 'border-green-300 bg-green-50 text-green-700 hover:bg-green-100'}"
							onclick={() => { selectTab('users'); applyUserFilter('approved'); }}
						>Approved · {usersApproved}</button>
					{/if}
					{#if usersRevoked > 0}
						<button
							class="rounded-full border px-3 py-1 text-xs font-semibold transition-colors {activeTab === 'users' && userFilter === 'revoked' ? 'border-maroon bg-maroon text-cream' : 'border-red-300 bg-red-50 text-red-700 hover:bg-red-100'}"
							onclick={() => { selectTab('users'); applyUserFilter('revoked'); }}
						>Revoked · {usersRevoked}</button>
					{/if}
					<!-- Admin/Super counts moved into the card header above (super-
					     only, display-only badges). Chip row stays purely about
					     filterable user statuses. -->
					<!-- "Include admins" toggle is super-only; non-super admins
					     don't have admin users in their list to begin with. -->
					{#if loggedInUser?.is_super}
						<label class="ml-auto inline-flex cursor-pointer items-center gap-1.5 text-xs text-ink/60">
							<input
								type="checkbox"
								class="rounded accent-maroon"
								bind:checked={userIncludeAdmins}
							/>
							Include admins
						</label>
					{/if}
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
							class="rounded-full border px-3 py-1 text-xs font-semibold transition-colors {activeTab === 'profiles' && profileStatusFilter === 'revoked' ? 'border-maroon bg-maroon text-cream' : 'border-red-300 bg-red-50 text-red-700 hover:bg-red-100'}"
							onclick={() => { selectTab('profiles'); applyProfileFilter('revoked'); }}
						>Revoked · {dashboard.stats.profiles_rejected}</button>
					{/if}
					{#if dashboard.stats.profiles_draft > 0}
						<button
							class="rounded-full border px-3 py-1 text-xs font-semibold transition-colors {activeTab === 'profiles' && profileStatusFilter === 'draft' ? 'border-maroon bg-maroon text-cream' : 'border-blue-300 bg-blue-50 text-blue-700 hover:bg-blue-100'}"
							onclick={() => { selectTab('profiles'); applyProfileFilter('draft'); }}
						>Draft · {dashboard.stats.profiles_draft}</button>
					{/if}
					<!-- Photo storage badge — shown to anyone with admin access -->
					{#if dashboard.stats.photos_count}
						<span
							class="ml-auto rounded-full border border-gold/40 bg-gold/10 px-3 py-1 text-xs font-semibold text-maroon"
							title="Total bytes used by passport.jpg variants of every profile photo"
						>
							{dashboard.stats.photos_count} photos · {formatBytes(dashboard.stats.photos_total_bytes ?? 0)}
						</span>
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
							class="rounded-full border px-3 py-1 text-xs font-semibold transition-colors {activeTab === 'requests' && requestStatusFilter === 'revoked' ? 'border-maroon bg-maroon text-cream' : 'border-red-300 bg-red-50 text-red-700 hover:bg-red-100'}"
							onclick={() => { selectTab('requests'); applyRequestFilter('revoked'); }}
						>Revoked · {dashboard.stats.requests_rejected}</button>
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
								{#if selectedUser.is_revoked} · <span class="text-vermilion font-semibold">Revoked</span>
								{:else if selectedUser.email_verified} · <span class="text-green-600">Email verified</span>{:else} · <span class="text-marigold">Unverified email</span>
								{/if}
								{#if !selectedUser.is_revoked}
									{#if selectedUser.is_approved} · <span class="text-green-600">Approved</span>{:else} · <span class="text-marigold">Not approved</span>{/if}
								{/if}
								{#if selectedUser.is_suspended} · <span class="font-semibold" style="color:#92400e">⏸ Suspended</span>{/if}
								{#if selectedUser.is_paused} · <span class="font-semibold" style="color:#a16207">⏸ Paused (vacation)</span>{/if}
							</p>
						</div>
						<div class="mt-3 flex flex-wrap gap-2">
							{#if !selectedUser.is_revoked}
								{#if !selectedUser.is_approved}
									<!-- Approving an admin is super-only; approving a regular user
									     additionally requires their email to be verified first. -->
									{#if (!selectedUser.is_admin || loggedInUser?.is_super) && selectedUser.email_verified}
										<button
											class="btn-primary text-sm flex flex-col items-center justify-center text-center leading-tight px-3 py-1.5 min-h-[44px] whitespace-normal"
											disabled={userActionLoading}
											onclick={() => approveUser(selectedUser!)}
										>
											{#if userActionLoading}<Loader size={13} class="animate-spin" />{/if}
											<span class="text-xs">Approve User</span>
											<span lang={langStore.current} class="text-[10px] opacity-90">{tx('approveUser', langStore.current)}</span>
										</button>
									{/if}
								{/if}
								<!-- The old "Revoke Approval" (clears is_approved without
								     blocking login) was collapsed into the harder "Revoke" below
								     to remove the two-step ambiguity. Flow is now simply
								     approve → revoke → reinstate / delete. The /admin/users/{id}/
								     unapprove endpoint still exists for scripted use. -->
								<!-- Verifying email of an admin is super-only (mirrors approve gate).
								     Resend Verification preserves the verify-then-approve flow; Verify
								     Email is the override that skips it. -->
								{#if !selectedUser.email_verified && (!selectedUser.is_admin || loggedInUser?.is_super)}
									<button
										class="btn-secondary text-sm flex flex-col items-center justify-center text-center leading-tight px-3 py-1.5 min-h-[44px] whitespace-normal"
										disabled={userActionLoading}
										onclick={() => resendVerificationFromGrid(selectedUser!)}
									>
										<span class="text-xs">Resend Verification</span>
										<span lang={langStore.current} class="text-[10px] opacity-90">{tx('resendVerification', langStore.current)}</span>
									</button>
									<button
										class="btn-secondary text-sm flex flex-col items-center justify-center text-center leading-tight px-3 py-1.5 min-h-[44px] whitespace-normal"
										disabled={userActionLoading}
										onclick={() => verifyEmailFromGrid(selectedUser!)}
									>
										<span class="text-xs flex items-center gap-1"><ShieldCheck size={13} />Verify (override)</span>
										<span lang={langStore.current} class="text-[10px] opacity-90">{tx('verifyEmailOverride', langStore.current)}</span>
									</button>
								{/if}
								<!-- Promote: super-only -->
								{#if loggedInUser?.is_super && !selectedUser.is_admin}
									<button
										class="btn-secondary text-sm flex flex-col items-center justify-center text-center leading-tight px-3 py-1.5 min-h-[44px] whitespace-normal"
										disabled={userActionLoading}
										onclick={() => promoteUserFromGrid(selectedUser!)}
									>
										<span class="text-xs">Make Admin</span>
										<span lang={langStore.current} class="text-[10px] opacity-90">{tx('makeAdmin', langStore.current)}</span>
									</button>
								{/if}
								<!-- Demote: super-only for admin targets -->
								{#if loggedInUser?.is_super && selectedUser.is_admin}
									<button
										class="flex flex-col items-center justify-center text-center leading-tight text-sm px-3 py-1.5 min-h-[44px] whitespace-normal rounded border border-vermilion/40 bg-white text-vermilion hover:bg-vermilion/5 disabled:opacity-50"
										disabled={userActionLoading}
										onclick={() => demoteUserFromGrid(selectedUser!)}
									>
										<span class="text-xs">Demote to User</span>
										<span lang={langStore.current} class="text-[10px] opacity-90">{tx('demoteToUser', langStore.current)}</span>
									</button>
								{/if}
								<!-- Suspend (admin enforcement hold) — softer than revoke. Login
								     still works; profiles drop from search; only admin can lift. -->
								{#if (!selectedUser.is_admin || loggedInUser?.is_super) && !selectedUser.is_suspended}
									<button
										class="flex flex-col items-center justify-center text-center leading-tight text-sm px-3 py-1.5 min-h-[44px] whitespace-normal rounded border border-saffron/50 bg-white text-saffron-700 hover:bg-saffron/10 disabled:opacity-50"
										style="color: #92400e"
										disabled={userActionLoading}
										onclick={() => suspendUser(selectedUser!)}
									>
										<span class="text-xs">⏸ Suspend</span>
										<span lang={langStore.current} class="text-[10px] opacity-90">{tx('suspend', langStore.current)}</span>
									</button>
								{/if}
								{#if selectedUser.is_suspended && (!selectedUser.is_admin || loggedInUser?.is_super)}
									<button
										class="flex flex-col items-center justify-center text-center leading-tight text-sm px-3 py-1.5 min-h-[44px] whitespace-normal rounded border border-green-600 bg-white text-green-700 hover:bg-green-50 disabled:opacity-50"
										disabled={userActionLoading}
										onclick={() => unsuspendUser(selectedUser!)}
									>
										<span class="text-xs flex items-center gap-1"><RotateCcw size={13} />Unsuspend</span>
										<span lang={langStore.current} class="text-[10px] opacity-90">{tx('unsuspend', langStore.current)}</span>
									</button>
								{/if}
								<!-- Revoke: super-only when target is admin, otherwise any admin -->
								{#if !selectedUser.is_admin || loggedInUser?.is_super}
									<button
										class="flex flex-col items-center justify-center text-center leading-tight text-sm px-3 py-1.5 min-h-[44px] whitespace-normal rounded border border-vermilion/40 bg-white text-vermilion hover:bg-vermilion/5 disabled:opacity-50"
										disabled={userActionLoading}
										onclick={() => revokeUser(selectedUser!)}
									>
										<span class="text-xs flex items-center gap-1"><XCircle size={13} />Revoke</span>
										<span lang={langStore.current} class="text-[10px] opacity-90">{tx('reject', langStore.current)}</span>
									</button>
								{/if}
							{:else}
								<!-- Reinstated: super-only when target is admin -->
								{#if !selectedUser.is_admin || loggedInUser?.is_super}
									<button
										class="flex flex-col items-center justify-center text-center leading-tight text-sm px-3 py-1.5 min-h-[44px] whitespace-normal rounded border border-green-600 bg-white text-green-700 hover:bg-green-50 disabled:opacity-50"
										disabled={userActionLoading}
										onclick={() => reinstateUser(selectedUser!)}
									>
										<span class="text-xs flex items-center gap-1"><RotateCcw size={13} />Reinstate</span>
										<span lang={langStore.current} class="text-[10px] opacity-90">{tx('approve', langStore.current)}</span>
									</button>
								{/if}
							{/if}
							<!-- Delete: super-only for admin targets; any-admin for non-admin users -->
							{#if loggedInUser?.is_super || (loggedInUser?.is_admin && !selectedUser.is_admin)}
								<button
									class="flex flex-col items-center justify-center text-center leading-tight text-sm px-3 py-1.5 min-h-[44px] whitespace-normal rounded bg-vermilion text-cream hover:bg-vermilion/80 disabled:opacity-50"
									disabled={userActionLoading}
									onclick={() => startDeleteUser(selectedUser!)}
								>
									<span class="text-xs flex items-center gap-1"><Trash2 size={13} />Delete User</span>
									<span lang={langStore.current} class="text-[10px] opacity-90">{tx('deleteUser', langStore.current)}</span>
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

			<!-- Selected profile action panel.
			     Stack vertically on mobile, side-by-side on sm+ — matches the
			     user-panel pattern. Avoids the "name overlaps Approve/Suspend/
			     Revoke buttons" issue when the row was forced into a single
			     flex line on narrow viewports. -->
			{#if selectedProfile}
				<div class="mt-4 rounded-lg border border-gold/30 bg-white px-5 py-4 shadow-sm">
					<div class="min-w-0">
						<!-- Tight one-line header: name + age. Status, gender, location
						     are visible in the row above and would crowd the buttons. -->
						<p class="font-semibold text-ink">
							{selectedProfile.first_name}{selectedProfile.last_name ? ` ${selectedProfile.last_name}` : ''}{ageFromDob(selectedProfile.dob) !== null ? `, ${ageFromDob(selectedProfile.dob)}` : ''}
						</p>
					</div>
					<div class="mt-3 flex flex-wrap gap-2">
						<a href="/profiles/{selectedProfile.id}" class="btn-secondary flex flex-col items-center justify-center text-center leading-tight text-xs px-4 py-1.5 min-h-[44px] whitespace-normal">
							<span>View →</span>
							<span lang={langStore.current} class="text-[10px] opacity-90">{tx('view', langStore.current)}</span>
						</a>
						<a
							href="/profiles/{selectedProfile.id}/edit"
							class="btn-secondary flex flex-col items-center justify-center text-center leading-tight text-xs px-4 py-1.5 min-h-[44px] whitespace-normal"
							title="Edit this profile as admin — status will not change"
						>
							<span>Edit ✎</span>
							<span lang={langStore.current} class="text-[10px] opacity-90">{tx('edit', langStore.current)}</span>
						</a>
						{#if selectedProfile.status === 'pending'}
							<button
								class="btn-primary flex flex-col items-center justify-center text-center leading-tight text-xs px-4 py-1.5 min-h-[44px] whitespace-normal"
								disabled={profileActionLoading}
								onclick={doApproveProfile}
							>
								{#if profileActionLoading}<Loader size={12} class="inline animate-spin mr-1" />{/if}
								<span>✓ Approve</span>
								<span lang={langStore.current} class="text-[10px] opacity-90">{tx('approve', langStore.current)}</span>
							</button>
							<button
								class="btn-danger flex flex-col items-center justify-center text-center leading-tight text-xs px-4 py-1.5 min-h-[44px] whitespace-normal"
								disabled={profileActionLoading}
								onclick={doRevokeProfile}
							>
								{#if profileActionLoading}<Loader size={12} class="inline animate-spin mr-1" />{/if}
								<span>✕ Revoke</span>
								<span lang={langStore.current} class="text-[10px] opacity-90">{tx('reject', langStore.current)}</span>
							</button>
						{/if}
						{#if selectedProfile.status === 'revoked'}
							<button
								class="flex flex-col items-center justify-center text-center leading-tight text-xs px-4 py-1.5 min-h-[44px] whitespace-normal rounded border border-green-600 bg-white text-green-700 hover:bg-green-50 disabled:opacity-50"
								disabled={profileActionLoading}
								onclick={doReinstateProfile}
							>
								{#if profileActionLoading}<Loader size={12} class="inline animate-spin mr-1" />{/if}
								<span class="flex items-center gap-1"><RotateCcw size={12} />Reinstate</span>
								<span lang={langStore.current} class="text-[10px] opacity-90">{tx('approve', langStore.current)}</span>
							</button>
						{/if}
						<!-- Delete is always available on any profile status -->
						<button
							class="flex flex-col items-center justify-center text-center leading-tight text-xs px-4 py-1.5 min-h-[44px] whitespace-normal rounded bg-vermilion text-cream hover:bg-vermilion/90 disabled:opacity-50"
							disabled={profileActionLoading}
							onclick={startDeleteProfile}
						>
							{#if profileActionLoading}<Loader size={12} class="inline animate-spin mr-1" />{/if}
							<span class="flex items-center gap-1"><Trash2 size={12} />Delete</span>
							<span lang={langStore.current} class="text-[10px] opacity-90">{tx('delete', langStore.current)}</span>
						</button>
					</div>
				</div>
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

			<!-- Selected request action panel — stack vertically on all
			     widths (matches the user / profile panels) so action buttons
			     never overlap the request label on mobile. -->
			{#if selectedRequest}
				<div class="mt-4 rounded-lg border border-gold/30 bg-white px-5 py-4 shadow-sm">
					<div class="min-w-0">
						<p class="font-semibold text-ink font-mono text-sm">{selectedRequest.id.slice(0, 8)}…</p>
						<p class="text-sm text-ink/60">
							Status: <span class="{selectedRequest.status === 'approved' ? 'text-green-600' : selectedRequest.status === 'revoked' ? 'text-vermilion' : 'text-saffron'} font-medium capitalize">{selectedRequest.status}</span>
							{#if selectedRequest.message} · "{selectedRequest.message}"{/if}
						</p>
					</div>
					<div class="mt-3 flex flex-wrap gap-2">
						{#if selectedRequest.status === 'pending'}
							<button
								class="btn-primary flex flex-col items-center justify-center text-center leading-tight text-xs px-4 py-1.5 min-h-[44px] whitespace-normal"
								disabled={requestActionLoading}
								onclick={doApproveRequest}
							>
								{#if requestActionLoading}<Loader size={12} class="inline animate-spin mr-1" />{/if}
								<span>✓ Approve</span>
								<span lang={langStore.current} class="text-[10px] opacity-90">{tx('approve', langStore.current)}</span>
							</button>
							<button
								class="btn-danger flex flex-col items-center justify-center text-center leading-tight text-xs px-4 py-1.5 min-h-[44px] whitespace-normal"
								disabled={requestActionLoading}
								onclick={doRevokeRequest}
							>
								{#if requestActionLoading}<Loader size={12} class="inline animate-spin mr-1" />{/if}
								<span>✕ Revoke</span>
								<span lang={langStore.current} class="text-[10px] opacity-90">{tx('reject', langStore.current)}</span>
							</button>
						{/if}
						{#if selectedRequest.status === 'revoked'}
							<button
								class="flex flex-col items-center justify-center text-center leading-tight text-xs px-4 py-1.5 min-h-[44px] whitespace-normal rounded border border-green-600 bg-white text-green-700 hover:bg-green-50 disabled:opacity-50"
								disabled={requestActionLoading}
								onclick={doReinstateRequest}
							>
								{#if requestActionLoading}<Loader size={12} class="inline animate-spin mr-1" />{/if}
								<span class="flex items-center gap-1"><RotateCcw size={12} />Reinstate</span>
								<span lang={langStore.current} class="text-[10px] opacity-90">{tx('approve', langStore.current)}</span>
							</button>
						{/if}
						<!-- Delete is always available on any request status -->
						<button
							class="flex flex-col items-center justify-center text-center leading-tight text-xs px-4 py-1.5 min-h-[44px] whitespace-normal rounded bg-vermilion text-cream hover:bg-vermilion/90 disabled:opacity-50"
							disabled={requestActionLoading}
							onclick={startDeleteRequest}
						>
							{#if requestActionLoading}<Loader size={12} class="inline animate-spin mr-1" />{/if}
							<span class="flex items-center gap-1"><Trash2 size={12} />Delete</span>
							<span lang={langStore.current} class="text-[10px] opacity-90">{tx('delete', langStore.current)}</span>
						</button>
					</div>
				</div>
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
	:global(.ag-theme-quartz .mk-cell-vermilion) {
		color: #dc2626 !important;
		font-weight: 600;
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
