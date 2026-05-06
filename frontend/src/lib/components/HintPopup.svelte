<script lang="ts">
	import { Info } from 'lucide-svelte';
	import { tx } from '$lib/i18n';
	import { langStore } from '$lib/stores/lang.svelte';

	let { text, langKey }: { text: string; langKey: string } = $props();

	let open = $state(false);
	let buttonEl = $state<HTMLButtonElement | undefined>();
	let popoverEl = $state<HTMLDivElement | undefined>();

	function toggle() {
		open = !open;
	}

	function close() {
		open = false;
	}

	function onKeydown(e: KeyboardEvent) {
		if (e.key === 'Escape') {
			close();
			buttonEl?.focus();
		}
	}

	function onBackdropClick(e: MouseEvent) {
		if (
			popoverEl &&
			buttonEl &&
			!popoverEl.contains(e.target as Node) &&
			!buttonEl.contains(e.target as Node)
		) {
			close();
		}
	}

	$effect(() => {
		if (open) {
			window.addEventListener('mousedown', onBackdropClick);
			window.addEventListener('keydown', onKeydown);
		} else {
			window.removeEventListener('mousedown', onBackdropClick);
			window.removeEventListener('keydown', onKeydown);
		}
		return () => {
			window.removeEventListener('mousedown', onBackdropClick);
			window.removeEventListener('keydown', onKeydown);
		};
	});
</script>

<span class="relative inline-flex items-center">
	<button
		bind:this={buttonEl}
		type="button"
		aria-label="Show help"
		aria-expanded={open}
		onclick={toggle}
		class="ml-1 inline-flex items-center rounded focus-visible:outline-2 focus-visible:outline-saffron"
	>
		<Info
			size={14}
			class="text-saffron/80 hover:text-saffron transition-colors"
		/>
	</button>

	{#if open}
		<div
			bind:this={popoverEl}
			role="tooltip"
			class="absolute left-5 top-0 z-50 max-w-[280px] sm:max-w-xs w-[calc(100vw-2rem)] rounded-lg border border-gold/50 bg-cream shadow-md"
			style="min-width:180px"
		>
			<div class="px-3 py-2.5 text-xs leading-relaxed">
				<p class="text-ink/80">{text}</p>
				<p class="mt-1 text-xs leading-relaxed text-maroon font-medium" lang={langStore.current}>
					{tx(langKey, langStore.current)}
				</p>
			</div>
		</div>
	{/if}
</span>
