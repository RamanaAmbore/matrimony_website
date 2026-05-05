<script lang="ts">
	import { T, tx, type BilingualKey } from '$lib/i18n';
	import { langStore } from '$lib/stores/lang.svelte';

	let {
		key,
		for: htmlFor,
		layout = 'stacked',
		required = false
	}: {
		key: BilingualKey;
		for?: string;
		layout?: 'inline' | 'stacked';
		required?: boolean;
	} = $props();

	let entry = $derived(T[key]);
	let native = $derived(tx(key, langStore.current));
	let lang = $derived(langStore.current);
</script>

{#if layout === 'inline'}
	<!-- Inline: "Home · హోమ్" — used in nav links -->
	<span class="inline-flex items-baseline gap-1">
		<span>{entry.en}</span>
		<span class="text-[0.8em] font-normal opacity-75" {lang}>{native}</span>
	</span>
{:else}
	<!-- Stacked: English on top, native beneath — used in form labels -->
	<label for={htmlFor} class="label block">
		<span class="block">
			{entry.en}{#if required}<span class="text-vermilion ml-0.5">*</span>{/if}
		</span>
		<span class="block text-xs text-ink/60 font-normal leading-tight" {lang}>{native}</span>
	</label>
{/if}
