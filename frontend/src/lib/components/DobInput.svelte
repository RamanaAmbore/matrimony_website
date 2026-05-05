<script lang="ts">
	let {
		value = $bindable(''),
		id,
		error = false
	}: {
		value: string;
		id: string;
		error?: boolean;
	} = $props();

	const _init = (() => {
		if (value && value.length >= 10 && /^\d{4}-\d{2}-\d{2}/.test(value)) {
			return { d: value.slice(8, 10), m: value.slice(5, 7), y: value.slice(0, 4) };
		}
		return { d: '', m: '', y: '' };
	})();
	let dd = $state(_init.d);
	let mm = $state(_init.m);
	let yyyy = $state(_init.y);

	$effect(() => {
		const dN = parseInt(dd, 10);
		const mN = parseInt(mm, 10);
		const yN = parseInt(yyyy, 10);
		const ok =
			Number.isFinite(dN) && dN >= 1 && dN <= 31 &&
			Number.isFinite(mN) && mN >= 1 && mN <= 12 &&
			Number.isFinite(yN) && yyyy.length === 4 && yN >= 1900 && yN <= 2100;
		const next = ok
			? `${String(yN).padStart(4, '0')}-${String(mN).padStart(2, '0')}-${String(dN).padStart(2, '0')}`
			: '';
		if (next !== value) value = next;
	});

	let mmEl = $state<HTMLInputElement | null>(null);
	let yyyyEl = $state<HTMLInputElement | null>(null);

	function onDdInput(e: Event) {
		const v = (e.target as HTMLInputElement).value.replace(/\D/g, '').slice(0, 2);
		dd = v;
		if (v.length === 2) mmEl?.focus();
	}
	function onMmInput(e: Event) {
		const v = (e.target as HTMLInputElement).value.replace(/\D/g, '').slice(0, 2);
		mm = v;
		if (v.length === 2) yyyyEl?.focus();
	}
	function onYyyyInput(e: Event) {
		yyyy = (e.target as HTMLInputElement).value.replace(/\D/g, '').slice(0, 4);
	}
</script>

<div class="flex items-center gap-2">
	<input
		{id}
		type="text"
		inputmode="numeric"
		maxlength="2"
		class="input w-14 text-center font-mono"
		class:border-vermilion={error}
		placeholder="DD"
		aria-label="Day"
		value={dd}
		oninput={onDdInput}
	/>
	<span class="text-ink/50">-</span>
	<input
		bind:this={mmEl}
		type="text"
		inputmode="numeric"
		maxlength="2"
		class="input w-14 text-center font-mono"
		class:border-vermilion={error}
		placeholder="MM"
		aria-label="Month"
		value={mm}
		oninput={onMmInput}
	/>
	<span class="text-ink/50">-</span>
	<input
		bind:this={yyyyEl}
		type="text"
		inputmode="numeric"
		maxlength="4"
		class="input w-20 text-center font-mono"
		class:border-vermilion={error}
		placeholder="YYYY"
		aria-label="Year"
		value={yyyy}
		oninput={onYyyyInput}
	/>
	<span class="text-xs text-ink/45">DD-MM-YYYY</span>
</div>
