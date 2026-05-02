<script lang="ts">
	import { toastStore } from '$lib/stores/toast.svelte';
	import { CheckCircle, XCircle, Info, X } from 'lucide-svelte';
</script>

<div
	class="pointer-events-none fixed right-4 bottom-4 z-50 flex flex-col gap-2"
	aria-live="polite"
	aria-label="Notifications"
>
	{#each toastStore.toasts as toast (toast.id)}
		<div
			class="pointer-events-auto flex max-w-sm items-start gap-3 rounded-lg px-4 py-3 shadow-lg transition-all duration-300
				{toast.kind === 'success'
				? 'border border-green-200 bg-green-50 text-green-800'
				: toast.kind === 'error'
					? 'border border-red-200 bg-red-50 text-red-800'
					: 'border border-sky-200 bg-sky-50 text-sky-800'}"
			role="alert"
		>
			<span class="mt-0.5 shrink-0">
				{#if toast.kind === 'success'}
					<CheckCircle size={18} />
				{:else if toast.kind === 'error'}
					<XCircle size={18} />
				{:else}
					<Info size={18} />
				{/if}
			</span>
			<p class="flex-1 text-sm font-medium">{toast.message}</p>
			<button
				onclick={() => toastStore.remove(toast.id)}
				class="shrink-0 rounded p-0.5 hover:bg-black/10 focus-visible:outline-2"
				aria-label="Dismiss notification"
			>
				<X size={14} />
			</button>
		</div>
	{/each}
</div>
