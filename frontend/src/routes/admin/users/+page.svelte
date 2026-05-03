<script lang="ts">
	import { onMount } from 'svelte';
	import { admin as adminApi, type User } from '$lib/api';
	import { ApiError } from '$lib/api';
	import { toastStore } from '$lib/stores/toast.svelte';
	import { goto } from '$app/navigation';
	import { Loader, ShieldCheck, UserCheck } from 'lucide-svelte';
	import KalashaDivider from '$lib/components/KalashaDivider.svelte';

	let userList = $state<User[]>([]);
	let loading = $state(true);
	let promotingId = $state<string | null>(null);
	let search = $state('');

	onMount(async () => {
		try {
			userList = await adminApi.users.list();
		} catch (err) {
			if (err instanceof ApiError) {
				if (err.status === 401) { goto('/login'); return; }
				if (err.status === 403) { goto('/'); return; }
			}
			toastStore.error('Failed to load users');
		} finally {
			loading = false;
		}
	});

	const filtered = $derived(
		search.trim()
			? userList.filter((u) =>
					u.email.toLowerCase().includes(search.toLowerCase()) ||
					u.user_handle?.toLowerCase().includes(search.toLowerCase())
				)
			: userList
	);

	async function promote(id: string) {
		if (!confirm('Promote this user to admin? This cannot be undone easily.')) return;
		promotingId = id;
		try {
			await adminApi.users.promote(id);
			userList = userList.map((u) =>
				u.user_id === id ? { ...u, is_admin: true } : u
			);
			toastStore.success('User promoted to admin');
		} catch {
			toastStore.error('Promotion failed');
		} finally {
			promotingId = null;
		}
	}
</script>

<svelte:head>
	<title>Admin: Users — Maratha Kalyanam</title>
</svelte:head>

<div class="mx-auto max-w-5xl px-4 py-10">
	<div class="flex flex-wrap items-center justify-between gap-3 mb-2">
		<h1 class="font-serif text-3xl font-bold text-maroon">Users</h1>
		<a href="/admin" class="btn-secondary text-sm">← Dashboard</a>
	</div>

	<KalashaDivider />

	<div class="mt-4 mb-6">
		<input
			type="search"
			class="input max-w-sm"
			bind:value={search}
			placeholder="Search by user ID or email…"
		/>
	</div>

	{#if loading}
		<div class="flex items-center justify-center py-20">
			<Loader size={36} class="animate-spin text-saffron" />
		</div>
	{:else}
		<div class="overflow-x-auto rounded-lg border border-gold/20">
			<table class="w-full text-sm">
				<thead class="bg-cream border-b border-gold/20">
					<tr>
						<th class="px-4 py-3 text-left font-semibold text-ink/70">User ID</th>
						<th class="px-4 py-3 text-left font-semibold text-ink/70">Email</th>
						<th class="px-4 py-3 text-left font-semibold text-ink/70">Verified</th>
						<th class="px-4 py-3 text-left font-semibold text-ink/70">Role</th>
						<th class="px-4 py-3 text-right font-semibold text-ink/70">Actions</th>
					</tr>
				</thead>
				<tbody class="divide-y divide-gold/10">
					{#each filtered as user (user.user_id)}
						<tr class="hover:bg-cream/50">
							<td class="px-4 py-3 font-mono text-ink/80 text-sm">@{user.user_handle}</td>
							<td class="px-4 py-3 text-ink">{user.email}</td>
							<td class="px-4 py-3">
								{#if user.email_verified}
									<span class="flex items-center gap-1 text-green-600">
										<UserCheck size={14} />
										Verified
									</span>
								{:else}
									<span class="text-ink/40">Unverified</span>
								{/if}
							</td>
							<td class="px-4 py-3">
								{#if user.is_admin}
									<span class="flex items-center gap-1 text-saffron font-medium">
										<ShieldCheck size={14} />
										Admin
									</span>
								{:else}
									<span class="text-ink/60">User</span>
								{/if}
							</td>
							<td class="px-4 py-3 text-right">
								{#if !user.is_admin}
									<button
										onclick={() => promote(user.user_id)}
										disabled={promotingId === user.user_id}
										class="text-xs font-medium text-saffron hover:underline disabled:opacity-60 focus-visible:outline-2 focus-visible:outline-saffron"
									>
										{promotingId === user.user_id ? 'Promoting…' : 'Promote to Admin'}
									</button>
								{/if}
							</td>
						</tr>
					{/each}
				</tbody>
			</table>
		</div>
		<p class="mt-2 text-xs text-ink/40">{filtered.length} of {userList.length} users</p>
	{/if}
</div>
