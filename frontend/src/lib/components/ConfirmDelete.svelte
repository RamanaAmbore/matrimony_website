<script lang="ts">
	interface Props {
		open: boolean;
		title: string;
		description: string;
		onConfirm: () => void | Promise<void>;
	}

	let { open = $bindable(), title, description, onConfirm }: Props = $props();

	let typed = $state('');
	let confirming = $state(false);

	const canSubmit = $derived(typed === 'DELETE');

	function close() {
		open = false;
		typed = '';
		confirming = false;
	}

	async function handleConfirm() {
		if (!canSubmit) return;
		confirming = true;
		try {
			await onConfirm();
			close();
		} finally {
			confirming = false;
		}
	}

	function onKeydown(e: KeyboardEvent) {
		if (e.key === 'Escape') close();
	}

	function onBackdropClick(e: MouseEvent) {
		if (e.target === e.currentTarget) close();
	}
</script>

{#if open}
	<!-- svelte-ignore a11y_no_noninteractive_element_interactions -->
	<div
		class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 px-4"
		onclick={onBackdropClick}
		onkeydown={onKeydown}
		tabindex="-1"
		aria-hidden="true"
	>
		<div
			role="dialog"
			aria-modal="true"
			aria-labelledby="confirm-delete-title"
			tabindex="-1"
			class="w-full max-w-sm rounded-xl bg-white p-6 shadow-xl border border-vermilion/20"
			onclick={(e) => e.stopPropagation()}
			onkeydown={undefined}
		>
			<h2 id="confirm-delete-title" class="font-serif text-xl font-bold text-vermilion mb-1">{title}</h2>
			<p class="text-sm text-ink/70 mb-4">{description}</p>

			<label class="label" for="confirm-delete-input">
				Type <span class="font-mono font-bold tracking-widest text-vermilion">DELETE</span> to confirm
			</label>
			<input
				id="confirm-delete-input"
				type="text"
				class="input mb-4"
				bind:value={typed}
				placeholder="DELETE"
				autocomplete="off"
				spellcheck={false}
			/>

			<div class="flex gap-2">
				<button
					type="button"
					class="btn-secondary flex-1 text-sm min-h-[40px]"
					onclick={close}
					disabled={confirming}
				>
					Cancel
				</button>
				<button
					type="button"
					class="flex-1 rounded bg-vermilion px-4 py-2 text-sm font-medium text-white transition-opacity hover:opacity-90 disabled:opacity-40 disabled:cursor-not-allowed min-h-[40px]"
					disabled={!canSubmit || confirming}
					onclick={handleConfirm}
				>
					{confirming ? 'Deleting…' : 'Delete'}
				</button>
			</div>
		</div>
	</div>
{/if}
