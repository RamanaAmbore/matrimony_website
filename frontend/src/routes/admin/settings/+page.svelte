<script lang="ts">
	import { onMount } from 'svelte';
	import { admin as adminApi, type Setting } from '$lib/api';
	import { ApiError } from '$lib/api';
	import { toastStore } from '$lib/stores/toast.svelte';
	import { goto } from '$app/navigation';
	import { Loader, Save } from 'lucide-svelte';

	let settings = $state<Setting[]>([]);
	let values = $state<Record<string, string>>({});
	let loading = $state(true);
	let saving = $state(false);

	onMount(async () => {
		try {
			settings = await adminApi.settings.get();
			values = Object.fromEntries(settings.map((s) => [s.key, s.value]));
		} catch (err) {
			if (err instanceof ApiError) {
				if (err.status === 401) { goto('/login'); return; }
				if (err.status === 403) { goto('/'); return; }
			}
			toastStore.error('Failed to load settings');
		} finally {
			loading = false;
		}
	});

	async function save() {
		saving = true;
		try {
			const updated = await adminApi.settings.update(values);
			settings = updated;
			toastStore.success('Settings saved');
		} catch {
			toastStore.error('Failed to save settings');
		} finally {
			saving = false;
		}
	}
</script>

<svelte:head>
	<title>Admin: Settings — Maratha Kalyanam</title>
</svelte:head>

<div class="mx-auto max-w-2xl px-4 py-10">
	<div class="flex flex-wrap items-center justify-between gap-3 mb-2">
		<h1 class="font-serif text-3xl font-bold text-maroon">Settings</h1>
		<a href="/admin" class="btn-secondary text-sm">← Dashboard</a>
	</div>
	<p class="text-sm text-ink/60">Runtime configuration — changes take effect immediately.</p>


	{#if loading}
		<div class="flex items-center justify-center py-20">
			<Loader size={36} class="animate-spin text-saffron" />
		</div>
	{:else}
		<form onsubmit={(e) => { e.preventDefault(); save(); }} class="space-y-4 mt-6">
			{#each settings as setting (setting.key)}
				<div>
					<label for="setting-{setting.key}" class="label font-mono text-xs">{setting.key}</label>
					{#if setting.description}
						<p class="text-xs text-ink/50 mb-1">{setting.description}</p>
					{/if}
					<input
						id="setting-{setting.key}"
						type="text"
						class="input font-mono text-sm"
						bind:value={values[setting.key]}
					/>
				</div>
			{/each}

			{#if settings.length === 0}
				<p class="text-ink/50 text-center py-8">No settings configured yet.</p>
			{/if}

			{#if settings.length > 0}
				<div class="flex justify-end pt-4">
					<button type="submit" class="btn-primary flex items-center gap-2" disabled={saving}>
						<Save size={16} />
						{saving ? 'Saving…' : 'Save Settings'}
					</button>
				</div>
			{/if}
		</form>
	{/if}
</div>
