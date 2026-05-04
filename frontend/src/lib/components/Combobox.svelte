<script lang="ts">
	import { ChevronDown, X } from 'lucide-svelte';

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
		options: string[];
		placeholder?: string;
		allowCustom?: boolean;
		required?: boolean;
		class?: string;
	} = $props();

	let inputEl = $state<HTMLInputElement | undefined>();
	let open = $state(false);
	let query = $state(value);

	// Keep query in sync when value changes externally (e.g. parent resets filters)
	$effect(() => {
		if (value !== query) query = value;
	});

	const filtered = $derived(
		query.trim()
			? options.filter(o => o.toLowerCase().includes(query.toLowerCase().trim()))
			: options
	);

	function select(opt: string) {
		value = opt;
		query = opt;
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
			// If not allowing custom and typed value isn't in options, revert to last valid
			if (!allowCustom && !options.includes(query)) {
				query = value;
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
			class="absolute z-50 mt-0.5 max-h-52 w-full overflow-y-auto rounded-lg border border-gold/50 bg-white shadow-lg"
			role="listbox"
		>
			{#each filtered as opt}
				<button
					type="button"
					role="option"
					aria-selected={value === opt}
					class="w-full px-3 py-2 text-left text-sm transition-colors {value === opt ? 'bg-maroon text-cream font-medium' : 'text-ink hover:bg-saffron/15 hover:text-maroon'}"
					onmousedown={(e) => { e.preventDefault(); select(opt); }}
				>
					{opt}
				</button>
			{/each}
			{#if filtered.length === 0 && allowCustom}
				<p class="px-3 py-2 text-sm text-ink/40">No matches — your entry will be saved</p>
			{/if}
		</div>
	{/if}
</div>
