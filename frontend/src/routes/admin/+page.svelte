<script lang="ts">
	import { onMount } from 'svelte';
	import {
		admin as adminApi,
		ApiError,
		type AdminDashboard,
		type PendingProfileSummary,
		type PendingRequest,
		type PendingUser
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
	import KalashaDivider from '$lib/components/KalashaDivider.svelte';

	let dashboard = $state<AdminDashboard | null>(null);
	let loading = $state(true);
	let error = $state('');

	// Reject notes state: keyed by item id
	let rejectNotes = $state<Record<string, string>>({});
	let rejectOpen = $state<Record<string, boolean>>({});
	// Per-item action loading
	let actionLoading = $state<Record<string, boolean>>({});

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

	// ── Profile actions ──────────────────────────────────────────────────────

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

	// ── Request actions ──────────────────────────────────────────────────────

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

	// ── User actions ─────────────────────────────────────────────────────────

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
</script>

<svelte:head>
	<title>Admin Dashboard — Marathya Kalaynam</title>
</svelte:head>

<div class="mx-auto max-w-6xl px-4 py-10">
	<h1 class="font-serif text-3xl font-bold text-maroon">Admin Dashboard</h1>
	<p class="mt-1 text-sm text-ink/60">Platform overview and quick approvals</p>

	<KalashaDivider />

	<!-- Quick nav to sub-pages -->
	<nav class="mb-8 flex flex-wrap gap-3">
		{#each [
			{ href: '/admin/profiles', label: 'All Profiles' },
			{ href: '/admin/requests', label: 'All Requests' },
			{ href: '/admin/users', label: 'All Users' },
			{ href: '/admin/settings', label: 'Settings' }
		] as link}
			<a href={link.href} class="btn-secondary text-sm">{link.label}</a>
		{/each}
	</nav>

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
</div>
