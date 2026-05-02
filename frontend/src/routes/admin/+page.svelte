<script lang="ts">
	import { onMount } from 'svelte';
	import { admin as adminApi, type AdminStats } from '$lib/api';
	import { ApiError } from '$lib/api';
	import { goto } from '$app/navigation';
	import { Loader, Users, UserCheck, Clock, CheckCircle2, XCircle, Inbox, Clock3 } from 'lucide-svelte';
	import KalashaDivider from '$lib/components/KalashaDivider.svelte';

	let stats = $state<AdminStats | null>(null);
	let loading = $state(true);
	let error = $state('');

	onMount(async () => {
		try {
			stats = await adminApi.getStats();
		} catch (err) {
			if (err instanceof ApiError) {
				if (err.status === 401) { goto('/login'); return; }
				if (err.status === 403) { goto('/'); return; }
			}
			error = 'Failed to load stats.';
		} finally {
			loading = false;
		}
	});
</script>

{#snippet statCard(label: string, value: number, color: string, href?: string)}
	<svelte:element
		this={href ? 'a' : 'div'}
		href={href ?? undefined}
		class="card flex flex-col items-center gap-2 text-center transition-shadow duration-200 {href ? 'hover:shadow-md cursor-pointer' : ''}"
	>
		<p class="tabular-nums text-3xl font-bold text-ink">{value}</p>
		<p class="text-sm {color}">{label}</p>
	</svelte:element>
{/snippet}

<svelte:head>
	<title>Admin Dashboard — Maratha Kalyanam</title>
</svelte:head>

<div class="mx-auto max-w-6xl px-4 py-10">
	<h1 class="font-serif text-3xl font-bold text-maroon">Admin Dashboard</h1>
	<p class="mt-1 text-sm text-ink/60">Overview of platform activity</p>

	<KalashaDivider />

	<!-- Quick nav -->
	<nav class="mb-8 flex flex-wrap gap-3">
		{#each [
			{ href: '/admin/profiles', label: 'Profiles' },
			{ href: '/admin/requests', label: 'Requests' },
			{ href: '/admin/users', label: 'Users' },
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
	{:else if stats}
		<div class="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4">
			<!-- Each card: icon rendered inline, value + label below -->
			<div class="card flex flex-col items-center gap-2 text-center">
				<Users size={28} class="text-saffron" />
				<p class="tabular-nums text-3xl font-bold text-ink">{stats.total_users}</p>
				<p class="text-sm text-ink/60">Total Users</p>
			</div>
			<div class="card flex flex-col items-center gap-2 text-center">
				<UserCheck size={28} class="text-gold" />
				<p class="tabular-nums text-3xl font-bold text-ink">{stats.total_profiles}</p>
				<p class="text-sm text-ink/60">Total Profiles</p>
			</div>
			<a href="/admin/profiles" class="card flex flex-col items-center gap-2 text-center cursor-pointer hover:shadow-md transition-shadow">
				<Clock size={28} class="text-marigold" />
				<p class="tabular-nums text-3xl font-bold text-ink">{stats.pending_profiles}</p>
				<p class="text-sm text-ink/60">Pending Profiles</p>
			</a>
			<div class="card flex flex-col items-center gap-2 text-center">
				<CheckCircle2 size={28} class="text-green-600" />
				<p class="tabular-nums text-3xl font-bold text-ink">{stats.approved_profiles}</p>
				<p class="text-sm text-ink/60">Approved Profiles</p>
			</div>
			<div class="card flex flex-col items-center gap-2 text-center">
				<XCircle size={28} class="text-vermilion" />
				<p class="tabular-nums text-3xl font-bold text-ink">{stats.rejected_profiles}</p>
				<p class="text-sm text-ink/60">Rejected Profiles</p>
			</div>
			<div class="card flex flex-col items-center gap-2 text-center">
				<Inbox size={28} class="text-sky-500" />
				<p class="tabular-nums text-3xl font-bold text-ink">{stats.total_requests}</p>
				<p class="text-sm text-ink/60">Total Requests</p>
			</div>
			<a href="/admin/requests" class="card flex flex-col items-center gap-2 text-center cursor-pointer hover:shadow-md transition-shadow">
				<Clock3 size={28} class="text-marigold" />
				<p class="tabular-nums text-3xl font-bold text-ink">{stats.pending_requests}</p>
				<p class="text-sm text-ink/60">Pending Requests</p>
			</a>
		</div>
	{/if}
</div>
