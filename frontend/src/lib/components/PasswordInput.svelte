<script lang="ts">
	import { Eye, EyeOff } from 'lucide-svelte';

	interface Props {
		value: string;
		id?: string;
		name?: string;
		placeholder?: string;
		required?: boolean;
		autocomplete?: HTMLInputElement['autocomplete'];
		disabled?: boolean;
		hasError?: boolean;
		class?: string;
	}

	let {
		value = $bindable(''),
		id,
		name,
		placeholder,
		required,
		autocomplete,
		disabled,
		hasError = false,
		class: extraClass = ''
	}: Props = $props();

	let visible = $state(false);

	function toggle() {
		visible = !visible;
	}
</script>

<div class="relative">
	<input
		{id}
		{name}
		type={visible ? 'text' : 'password'}
		{placeholder}
		{required}
		{autocomplete}
		{disabled}
		bind:value
		class="input pr-10 {extraClass}"
		class:border-vermilion={hasError}
	/>
	<button
		type="button"
		onclick={toggle}
		aria-label={visible ? 'Hide password' : 'Show password'}
		aria-pressed={visible}
		tabindex="0"
		class="absolute right-2.5 top-1/2 -translate-y-1/2 rounded p-0.5 text-ink/40 hover:text-ink/70 focus-visible:outline-2 focus-visible:outline-saffron"
	>
		{#if visible}
			<EyeOff size={16} />
		{:else}
			<Eye size={16} />
		{/if}
	</button>
</div>
