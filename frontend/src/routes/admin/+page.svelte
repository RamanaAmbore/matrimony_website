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
		type PendingUser,
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
		Clock,
		CheckCircle2,
		Inbox,
		CheckCheck,
		X,
		ShieldCheck
	} from 'lucide-svelte';

	// ── Tab state ────────────────────────────────────────────────────────────────

	type Tab = 'pending' | 'profiles' | 'requests' | 'users' | 'broadcast';
	let activeTab = $state<Tab>('pending');

	// ── Pending tab state ────────────────────────────────────────────────────────

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

	// ── All Requests tab state ───────────────────────────────────────────────────

	let allRequests = $state<DetailRequest[] | null>(null);
	let allRequestsLoading = $state(false);
	let allRequestsError = $state('');

	// ── All Users tab state ──────────────────────────────────────────────────────

	let allUsers = $state<User[] | null>(null);
	let allUsersLoading = $state(false);
	let allUsersError = $state('');

	// ag-Grid state
	let usersGridDiv = $state<HTMLDivElement | undefined>(undefined);
	let usersGridApi = $state<GridApi | undefined>(undefined);
	let selectedUser = $state<User | null>(null);
	let userActionLoading = $state(false);

	// ── Broadcast Email tab state ─────────────────────────────────────────────────

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

	// ── Mount: load pending dashboard ────────────────────────────────────────────

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
			{ field: 'email', headerName: 'Email', flex: 2, filter: true, sortable: true },
			{
				field: 'user_handle', headerName: 'Handle', flex: 1, filter: true, sortable: true,
				valueFormatter: (p: { value: string }) => `@${p.value}`
			},
			{ field: 'full_name', headerName: 'Name', flex: 1, filter: true, sortable: true },
			{ field: 'phone_number', headerName: 'Phone', flex: 1 },
			{
				field: 'email_verified', headerName: 'Email Verified', width: 140, sortable: true,
				cellRenderer: (p: { value: boolean }) => p.value ? '✓ Verified' : '⚠ Pending'
			},
			{
				field: 'is_approved', headerName: 'Approved', width: 120, sortable: true,
				cellRenderer: (p: { value: boolean }) => p.value ? '✓ Approved' : '— Pending'
			},
			{
				field: 'is_admin', headerName: 'Admin', width: 90, sortable: true,
				cellRenderer: (p: { value: boolean }) => p.value ? '★ Admin' : ''
			}
		];

		const gridOptions: GridOptions = {
			columnDefs,
			rowData: allUsers,
			rowSelection: { mode: 'singleRow', checkboxes: false, enableClickSelection: true },
			onRowClicked: (e) => { selectedUser = e.data as User; },
			defaultColDef: { resizable: true },
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
		if (tab === 'profiles') loadAllProfiles();
		if (tab === 'requests') loadAllRequests();
		if (tab === 'users') loadAllUsers();
	}

	// ── Profile actions ──────────────────────────────────────────────────────────

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

	// ── Request actions ──────────────────────────────────────────────────────────

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

	// ── User actions ─────────────────────────────────────────────────────────────

	async function verifyUser(u: PendingUser) {
		actionLoading[u.id] = true;
		try {
			await adminApi.users.verifyEmail(u.id);
			dashboard!.pending_users = dashboard!.pending_users.filter(x => x.id !== u.id);
			toastStore.success('Email verified');
		} catch (err) {
			toastStore.error(err instanceof ApiError ? err.message.slice(0, 35) : 'Action failed');
		} finally {
			actionLoading[u.id] = false;
		}
	}

	function toggleReject(id: string) {
		rejectOpen[id] = !rejectOpen[id];
		if (!rejectOpen[id]) rejectNotes[id] = '';
	}

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

	// Tab button class helper
	function tabClass(tab: Tab) {
		return activeTab === tab
			? 'rounded-full px-4 py-1.5 text-sm font-semibold bg-maroon text-cream transition-colors duration-150'
			: 'rounded-full px-4 py-1.5 text-sm font-medium text-ink/60 hover:text-maroon transition-colors duration-150';
	}
</script>

<svelte:head>
	<title>Admin Dashboard — Maratha Kalyanam</title>
</svelte:head>

<div class="mx-auto max-w-6xl px-4 py-10">
	<h1 class="font-serif text-3xl font-bold text-maroon">Admin Dashboard</h1>
	<p class="mt-1 text-sm text-ink/60">Platform overview and quick approvals</p>


	<!-- Quick nav to sub-pages -->
	<nav class="mb-6 flex flex-wrap gap-3">
		{#each [
			{ href: '/admin/profiles', label: 'All Profiles' },
			{ href: '/admin/requests', label: 'All Requests' },
			{ href: '/admin/users', label: 'All Users' },
			{ href: '/admin/settings', label: 'Settings' }
		] as link}
			<a href={link.href} class="btn-secondary text-sm">{link.label}</a>
		{/each}
	</nav>

	<!-- ── Tab bar ─────────────────────────────────────────────────────────────── -->
	<div class="mb-8 flex flex-wrap gap-1 rounded-full border border-gold/30 bg-white px-1.5 py-1.5 w-fit shadow-sm">
		<button class={tabClass('pending')} onclick={() => selectTab('pending')}>Pending</button>
		<button class={tabClass('profiles')} onclick={() => selectTab('profiles')}>All Profiles</button>
		<button class={tabClass('requests')} onclick={() => selectTab('requests')}>All Requests</button>
		<button class={tabClass('users')} onclick={() => selectTab('users')}>All Users</button>
		<button class={tabClass('broadcast')} onclick={() => selectTab('broadcast')}>Broadcast Email</button>
	</div>

	<!-- ── Pending tab ─────────────────────────────────────────────────────────── -->
	{#if activeTab === 'pending'}

		{#if loading}
			<div class="flex items-center justify-center py-20">
				<Loader size={36} class="animate-spin text-saffron" />
			</div>
		{:else if error}
			<div class="rounded-lg border border-vermilion/30 bg-vermilion/5 p-4 text-vermilion">{error}</div>
		{:else if dashboard}

			<!-- ── Stats row ──────────────────────────────────────────────────────── -->
			<div class="mb-10 grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-5">
				<div class="card flex flex-col items-center gap-1 text-center">
					<Users size={24} class="text-saffron" />
					<p class="tabular-nums text-2xl font-bold text-ink">{dashboard.stats.users}</p>
					<p class="text-xs text-ink/60">Total Users</p>
				</div>
				<div class="card flex flex-col items-center gap-1 text-center">
					<UserCheck size={24} class="text-gold" />
					<p class="tabular-nums text-2xl font-bold text-ink">{dashboard.stats.profiles_total}</p>
					<p class="text-xs text-ink/60">Total Profiles</p>
				</div>
				<a href="/admin/profiles" class="card flex flex-col items-center gap-1 text-center cursor-pointer hover:shadow-md transition-shadow">
					<Clock size={24} class="text-marigold" />
					<p class="tabular-nums text-2xl font-bold text-ink">{dashboard.stats.profiles_pending}</p>
					<p class="text-xs text-ink/60">Pending Profiles</p>
				</a>
				<div class="card flex flex-col items-center gap-1 text-center">
					<CheckCircle2 size={24} class="text-green-600" />
					<p class="tabular-nums text-2xl font-bold text-ink">{dashboard.stats.profiles_approved}</p>
					<p class="text-xs text-ink/60">Approved</p>
				</div>
				<a href="/admin/requests" class="card flex flex-col items-center gap-1 text-center cursor-pointer hover:shadow-md transition-shadow">
					<Inbox size={24} class="text-sky-500" />
					<p class="tabular-nums text-2xl font-bold text-ink">{dashboard.stats.requests_pending}</p>
					<p class="text-xs text-ink/60">Pending Requests</p>
				</a>
			</div>

			<!-- ── Pending profile approvals ──────────────────────────────────────── -->
			<section class="mb-10">
				<div class="mb-3 flex items-center justify-between">
					<h2 class="font-serif text-xl font-semibold text-maroon">Pending Profile Approvals</h2>
					<a href="/admin/profiles" class="text-sm text-saffron hover:underline">View all →</a>
				</div>

				{#if dashboard.pending_profiles.length === 0}
					<div class="card flex items-center gap-3 text-ink/60">
						<CheckCheck size={20} class="shrink-0 text-green-500" />
						<span class="text-sm">All caught up — no pending profiles</span>
					</div>
				{:else}
					<div class="space-y-3">
						{#each dashboard.pending_profiles as p (p.id)}
							<div class="card space-y-2">
								<!-- Profile summary row -->
								<div class="flex flex-wrap items-start justify-between gap-2">
									<div class="min-w-0">
										<p class="font-semibold text-ink">
											{p.first_name} {p.last_name}
											<span class="badge badge-pending ml-1">{p.gender}</span>
										</p>
										<p class="mt-0.5 text-xs text-ink/60">
											Age {p.age} · {p.city}, {p.state} · Gotra: {p.gotra} · Nakshatram: {p.nakshatram}
										</p>
										<p class="mt-0.5 text-xs text-ink/50">
											Owner: {p.owner_email} · Submitted {fmtDate(p.created_at)}
										</p>
									</div>
									<div class="flex shrink-0 gap-2">
										<button
											class="btn-primary text-xs px-3 py-1.5"
											disabled={actionLoading[p.id]}
											onclick={() => approveProfile(p)}
										>
											{#if actionLoading[p.id] && !rejectOpen[p.id]}
												<Loader size={12} class="animate-spin" />
											{:else}
												Approve
											{/if}
										</button>
										<button
											class="btn-danger text-xs px-3 py-1.5"
											disabled={actionLoading[p.id]}
											onclick={() => toggleReject(p.id)}
										>
											<X size={12} class="inline" /> Reject
										</button>
									</div>
								</div>

								<!-- Inline reject form -->
								{#if rejectOpen[p.id]}
									<div class="flex gap-2 pt-1">
										<input
											type="text"
											class="input text-sm flex-1"
											placeholder="Rejection reason (required)"
											bind:value={rejectNotes[p.id]}
										/>
										<button
											class="btn-danger text-xs px-3 py-1.5 shrink-0"
											disabled={actionLoading[p.id]}
											onclick={() => rejectProfile(p)}
										>
											{#if actionLoading[p.id]}
												<Loader size={12} class="animate-spin" />
											{:else}
												Confirm
											{/if}
										</button>
									</div>
								{/if}
							</div>
						{/each}
					</div>
				{/if}
			</section>

			<!-- ── Pending detail-info requests ───────────────────────────────────── -->
			<section class="mb-10">
				<div class="mb-3 flex items-center justify-between">
					<h2 class="font-serif text-xl font-semibold text-maroon">Pending Detail-Info Requests</h2>
					<a href="/admin/requests" class="text-sm text-saffron hover:underline">View all →</a>
				</div>

				{#if dashboard.pending_requests.length === 0}
					<div class="card flex items-center gap-3 text-ink/60">
						<CheckCheck size={20} class="shrink-0 text-green-500" />
						<span class="text-sm">All caught up — no pending requests</span>
					</div>
				{:else}
					<div class="space-y-3">
						{#each dashboard.pending_requests as r (r.id)}
							<div class="card space-y-2">
								<div class="flex flex-wrap items-start justify-between gap-2">
									<div class="min-w-0">
										<p class="font-semibold text-ink">
											{r.requester_email}
											<span class="text-ink/50 font-normal"> → </span>
											{r.profile_first_name} {r.profile_last_name}
										</p>
										{#if r.message}
											<p class="mt-0.5 text-xs text-ink/60 line-clamp-1">"{r.message}"</p>
										{/if}
										<p class="mt-0.5 text-xs text-ink/50">Requested {fmtDate(r.created_at)}</p>
									</div>
									<div class="flex shrink-0 gap-2">
										<button
											class="btn-primary text-xs px-3 py-1.5"
											disabled={actionLoading[r.id]}
											onclick={() => approveRequest(r)}
										>
											{#if actionLoading[r.id] && !rejectOpen[r.id]}
												<Loader size={12} class="animate-spin" />
											{:else}
												Approve
											{/if}
										</button>
										<button
											class="btn-danger text-xs px-3 py-1.5"
											disabled={actionLoading[r.id]}
											onclick={() => toggleReject(r.id)}
										>
											<X size={12} class="inline" /> Reject
										</button>
									</div>
								</div>

								{#if rejectOpen[r.id]}
									<div class="flex gap-2 pt-1">
										<input
											type="text"
											class="input text-sm flex-1"
											placeholder="Rejection reason (required)"
											bind:value={rejectNotes[r.id]}
										/>
										<button
											class="btn-danger text-xs px-3 py-1.5 shrink-0"
											disabled={actionLoading[r.id]}
											onclick={() => rejectRequest(r)}
										>
											{#if actionLoading[r.id]}
												<Loader size={12} class="animate-spin" />
											{:else}
												Confirm
											{/if}
										</button>
									</div>
								{/if}
							</div>
						{/each}
					</div>
				{/if}
			</section>

			<!-- ── Recently registered — pending email verification ───────────────── -->
			<section class="mb-10">
				<div class="mb-3 flex items-center justify-between">
					<h2 class="font-serif text-xl font-semibold text-maroon">
						Recently Registered (Pending Email Verification)
					</h2>
					<a href="/admin/users" class="text-sm text-saffron hover:underline">View all →</a>
				</div>

				{#if dashboard.pending_users.length === 0}
					<div class="card flex items-center gap-3 text-ink/60">
						<CheckCheck size={20} class="shrink-0 text-green-500" />
						<span class="text-sm">All caught up — no unverified users</span>
					</div>
				{:else}
					<div class="space-y-3">
						{#each dashboard.pending_users as u (u.id)}
							<div class="card flex flex-wrap items-center justify-between gap-3">
								<div class="min-w-0">
									<p class="font-medium text-ink">{u.email}</p>
									<p class="mt-0.5 text-xs text-ink/50">Registered {fmtDate(u.created_at)}</p>
								</div>
								<button
									class="btn-secondary text-xs px-3 py-1.5 shrink-0 flex items-center gap-1.5"
									disabled={actionLoading[u.id]}
									onclick={() => verifyUser(u)}
								>
									{#if actionLoading[u.id]}
										<Loader size={12} class="animate-spin" />
									{:else}
										<ShieldCheck size={14} />
										Verify email
									{/if}
								</button>
							</div>
						{/each}
					</div>
				{/if}
			</section>

		{/if}

	<!-- ── All Profiles tab ────────────────────────────────────────────────────── -->
	{:else if activeTab === 'profiles'}
		{#if allProfilesLoading}
			<div class="flex items-center justify-center py-20">
				<Loader size={36} class="animate-spin text-saffron" />
			</div>
		{:else if allProfilesError}
			<div class="rounded-lg border border-vermilion/30 bg-vermilion/5 p-4 text-vermilion">{allProfilesError}</div>
		{:else if allProfiles}
			<div class="mb-3 flex items-center justify-between">
				<h2 class="font-serif text-xl font-semibold text-maroon">All Profiles</h2>
				<span class="text-sm text-ink/50">{allProfiles.length} total</span>
			</div>
			{#if allProfiles.length === 0}
				<div class="card text-sm text-ink/60">No profiles found.</div>
			{:else}
				<div class="overflow-x-auto rounded-lg border border-gold/30 bg-white shadow-sm">
					<table class="w-full text-sm">
						<thead>
							<tr class="border-b border-gold/30 bg-cream/60 text-left text-xs font-semibold text-ink/60 uppercase tracking-wider">
								<th class="px-4 py-3">ID</th>
								<th class="px-4 py-3">Name</th>
								<th class="px-4 py-3">Gender</th>
								<th class="px-4 py-3">Status</th>
								<th class="px-4 py-3">City</th>
								<th class="px-4 py-3">Created</th>
								<th class="px-4 py-3"></th>
							</tr>
						</thead>
						<tbody class="divide-y divide-gold/20">
							{#each allProfiles as p (p.id)}
								<tr class="hover:bg-cream/40 transition-colors">
									<td class="px-4 py-3 font-mono text-xs text-ink/50">{truncateId(p.id)}</td>
									<td class="px-4 py-3 font-medium text-ink">{p.first_name} {p.last_name}</td>
									<td class="px-4 py-3 text-ink/70 capitalize">{p.gender}</td>
									<td class="px-4 py-3">
										<span class={statusBadgeClass(p.status)}>{p.status}</span>
									</td>
									<td class="px-4 py-3 text-ink/70">{p.city}</td>
									<td class="px-4 py-3 text-ink/50">{fmtDate(p.created_at)}</td>
									<td class="px-4 py-3">
										<a href="/admin/profiles/{p.id}" class="text-saffron hover:underline text-xs">View →</a>
									</td>
								</tr>
							{/each}
						</tbody>
					</table>
				</div>
			{/if}
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
			<div class="mb-3 flex items-center justify-between">
				<h2 class="font-serif text-xl font-semibold text-maroon">All Requests</h2>
				<span class="text-sm text-ink/50">{allRequests.length} total</span>
			</div>
			{#if allRequests.length === 0}
				<div class="card text-sm text-ink/60">No requests found.</div>
			{:else}
				<div class="overflow-x-auto rounded-lg border border-gold/30 bg-white shadow-sm">
					<table class="w-full text-sm">
						<thead>
							<tr class="border-b border-gold/30 bg-cream/60 text-left text-xs font-semibold text-ink/60 uppercase tracking-wider">
								<th class="px-4 py-3">ID</th>
								<th class="px-4 py-3">Requester</th>
								<th class="px-4 py-3">Profile ID</th>
								<th class="px-4 py-3">Status</th>
								<th class="px-4 py-3">Date</th>
							</tr>
						</thead>
						<tbody class="divide-y divide-gold/20">
							{#each allRequests as r (r.id)}
								<tr class="hover:bg-cream/40 transition-colors">
									<td class="px-4 py-3 font-mono text-xs text-ink/50">{truncateId(r.id)}</td>
									<!-- DetailRequest.requester_user_id is the user UUID; no email available in this type -->
									<td class="px-4 py-3 font-mono text-xs text-ink/70">{truncateId(r.requester_user_id)}</td>
									<td class="px-4 py-3 font-mono text-xs text-ink/70">{truncateId(r.profile_id)}</td>
									<td class="px-4 py-3">
										<span class={statusBadgeClass(r.status)}>{r.status}</span>
									</td>
									<td class="px-4 py-3 text-ink/50">{fmtDate(r.created_at)}</td>
								</tr>
							{/each}
						</tbody>
					</table>
				</div>
			{/if}
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
				<!-- ag-Grid container -->
				<div bind:this={usersGridDiv} class="ag-theme-quartz w-full" style="height: 480px;"></div>

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
		{/if}

	{/if}

	<!-- ── Broadcast Email tab ─────────────────────────────────────────────────── -->
	{#if activeTab === 'broadcast'}
		<div class="max-w-2xl">
			<h2 class="text-xl font-semibold text-ink mb-1">Broadcast Email</h2>
			<p class="text-sm text-ink/60 mb-6">Send a message to all registered users.</p>

			<div class="bg-white rounded-xl border border-gold/20 shadow-sm p-6 space-y-5">
				<!-- Audience filters -->
				<fieldset class="space-y-2">
					<legend class="text-sm font-medium text-ink">Audience</legend>
					<label class="flex items-center gap-2 text-sm cursor-pointer">
						<input type="checkbox" bind:checked={broadcastVerifiedOnly} class="accent-maroon" />
						Only email-verified users
					</label>
					<label class="flex items-center gap-2 text-sm cursor-pointer">
						<input type="checkbox" bind:checked={broadcastApprovedOnly} class="accent-maroon" />
						Only admin-approved users
					</label>
				</fieldset>

				<!-- Subject -->
				<div class="space-y-1">
					<label for="bc-subject" class="label text-sm">Subject</label>
					<input
						id="bc-subject"
						type="text"
						class="input"
						bind:value={broadcastSubject}
						placeholder="e.g. Important update from Maratha Kalyanam"
						disabled={broadcastSending}
					/>
				</div>

				<!-- Body -->
				<div class="space-y-1">
					<label for="bc-body" class="label text-sm">Message</label>
					<p class="text-xs text-ink/50">Plain text or simple HTML. Will be embedded in a branded email template.</p>
					<textarea
						id="bc-body"
						rows="10"
						class="input font-mono text-sm resize-y"
						bind:value={broadcastBody}
						placeholder="Dear members,&#10;&#10;We are pleased to announce..."
						disabled={broadcastSending}
					></textarea>
				</div>

				<!-- Send button -->
				<div class="flex items-center gap-4">
					<button
						class="btn-primary px-6 py-2.5 disabled:opacity-50 disabled:cursor-not-allowed"
						disabled={broadcastSending || !broadcastSubject.trim() || !broadcastBody.trim()}
						onclick={sendBroadcast}
					>
						{#if broadcastSending}
							Sending…
						{:else}
							Send Broadcast
						{/if}
					</button>
					{#if broadcastResult}
						<span class="text-sm text-ink/70">
							Sent <strong class="text-green-700">{broadcastResult.sent}</strong> ·
							Failed <strong class={broadcastResult.failed > 0 ? 'text-red-600' : 'text-ink/40'}>{broadcastResult.failed}</strong>
						</span>
					{/if}
				</div>
			</div>
		</div>
	{/if}

</div>
