<script lang="ts">
	import { ChevronDown, X } from 'lucide-svelte';

	type OptionObj = { value: string; label: string };
	type Option = string | OptionObj;

	function optValue(o: Option): string {
		return typeof o === 'string' ? o : o.value;
	}
	function optLabel(o: Option): string {
		return typeof o === 'string' ? o : o.label;
	}

	let {
		id = '',
		value = $bindable(''),
		options,
		placeholder = 'Select or type…',
		allowCustom = false,
		required = false,
		class: className = '',
	}: {
		id?: string;
		value?: string;
		options: Option[];
		placeholder?: string;
		allowCustom?: boolean;
		required?: boolean;
		class?: string;
	} = $props();

	let inputEl = $state<HTMLInputElement | undefined>();
	let open = $state(false);

	// Derive the display label for the currently stored value
	function labelForValue(v: string): string {
		if (!v) return '';
		const match = options.find(o => optValue(o) === v);
		return match ? optLabel(match) : v;
	}

	let query = $state(labelForValue(value));

	// Keep query in sync when value changes externally (e.g. parent resets filters)
	$effect(() => {
		const expected = labelForValue(value);
		if (query !== expected) query = expected;
	});

	const filtered = $derived(
		query.trim()
			? options.filter(o => optLabel(o).toLowerCase().includes(query.toLowerCase().trim()))
			: options
	);

	function select(opt: Option) {
		value = optValue(opt);
		query = optLabel(opt);
		open = false;
	}

	function handleInput(e: Event) {
		const v = (e.currentTarget as HTMLInputElement).value;
		query = v;
		open = true;
		if (allowCustom) value = v;
	}

	function handleFocus() {
		open = true;
	}

	function handleBlur() {
		// delay so onmousedown on option fires first
		setTimeout(() => {
			open = false;
			// If not allowing custom and typed label isn't in options, revert to last valid label
			if (!allowCustom && !options.some(o => optLabel(o) === query)) {
				query = labelForValue(value);
			}
		}, 200);
	}

	function clear(e: MouseEvent) {
		e.preventDefault();
		value = '';
		query = '';
		open = true;
		inputEl?.focus();
	}

	function toggle(e: MouseEvent) {
		e.preventDefault();
		open = !open;
		if (open) inputEl?.focus();
	}
</script>

<div class="relative {className}">
	<div class="relative flex items-center">
		<input
			bind:this={inputEl}
			{id}
			type="text"
			class="input pr-14"
			value={query}
			oninput={handleInput}
			onfocus={handleFocus}
			onblur={handleBlur}
			{placeholder}
			{required}
			autocomplete="off"
			role="combobox"
			aria-expanded={open}
			aria-haspopup="listbox"
			aria-autocomplete="list"
		/>
		<div class="absolute right-0 flex items-center gap-px pr-2">
			{#if query}
				<button
					type="button"
					tabindex="-1"
					class="rounded p-1 text-ink/40 hover:text-maroon transition-colors"
					onmousedown={clear}
					aria-label="Clear"
				>
					<X size={13} />
				</button>
			{/if}
			<button
				type="button"
				tabindex="-1"
				class="rounded p-1 text-ink/40 hover:text-maroon transition-colors"
				onmousedown={toggle}
				aria-label="Toggle options"
			>
				<ChevronDown size={14} class="transition-transform duration-150 {open ? 'rotate-180' : ''}" />
			</button>
		</div>
	</div>

	{#if open && filtered.length > 0}
		<div
			class="combobox-popup absolute z-50 mt-0.5 max-h-52 w-full overflow-y-auto"
			role="listbox"
		>
			{#each filtered as opt}
				<button
					type="button"
					role="option"
					aria-selected={value === optValue(opt)}
					class="combobox-option w-full px-3 py-2 text-left text-sm transition-colors {value === optValue(opt) ? 'selected' : ''}"
					onmousedown={(e) => { e.preventDefault(); select(opt); }}
				>
					{optLabel(opt)}
				</button>
			{/each}
			{#if filtered.length === 0 && allowCustom}
				<p class="px-3 py-2 text-sm text-ink/40">No matches — your entry will be saved</p>
			{/if}
		</div>
	{/if}
</div>

<style>
	.combobox-popup {
		background: var(--color-cream);
		border: 1px solid var(--color-gold);
		border-radius: 8px;
		box-shadow: 0 4px 12px rgba(0, 0, 0, 0.12);
	}

	.combobox-option {
		color: var(--color-ink);
	}

	.combobox-option:hover,
	.combobox-option:focus-visible {
		background: var(--color-saffron);
		color: var(--color-maroon);
		outline: none;
	}

	.combobox-option.selected {
		background: var(--color-maroon);
		color: var(--color-cream);
		font-weight: 500;
	}

	.combobox-option.selected:hover {
		background: var(--color-maroon);
		color: var(--color-cream);
	}
</style>
