<script lang="ts">
	let {
		class: className = '',
		size = 32,
		color = '#c9a227',
		opacity = 0.3
	}: { class?: string; size?: number; color?: string; opacity?: number } = $props();
</script>

<!-- Paisley / Boteh motif — decorative accent for section corners -->
<svg
	width={size}
	height={size}
	viewBox="0 0 32 32"
	fill="none"
	xmlns="http://www.w3.org/2000/svg"
	class={className}
	aria-hidden="true"
	style="opacity: {opacity}"
>
	<!-- Teardrop body of paisley -->
	<path
		d="M16 28 C8 28 4 22 4 16 C4 10 8 4 14 4 C18 4 20 7 20 10 C20 14 17 16 16 20 C15 24 16 28 16 28Z"
		fill={color}
	/>
	<!-- Inner curl -->
	<path
		d="M16 24 C13 22 12 18 14 15 C15 13 17 12 18 10"
		stroke="white"
		stroke-width="1"
		fill="none"
		stroke-linecap="round"
		opacity="0.6"
	/>
	<!-- Decorative dot -->
	<circle cx="14" cy="10" r="1.5" fill="white" opacity="0.6" />
	<!-- Curling tip -->
	<path
		d="M16 28 C17 26 20 25 22 23 C24 21 24 18 22 17"
		stroke={color}
		stroke-width="1.5"
		fill="none"
		stroke-linecap="round"
		opacity="0.7"
	/>
</svg>
