<script lang="ts">
	let { size = 24 }: { size?: number } = $props();
</script>

<!-- Palm-leaf manuscript / scroll — create profile symbol -->
<svg
	width={size}
	height={size}
	viewBox="0 0 24 24"
	fill="none"
	xmlns="http://www.w3.org/2000/svg"
	aria-label="Palm leaf manuscript"
	role="img"
>
	<!-- Scroll body (slightly curved leaf shape) -->
	<path d="M3.5 6 Q4 4 6 4 L18 4 Q20 4 20.5 6 L20.5 18 Q20 20 18 20 L6 20 Q4 20 3.5 18 Z" fill="#FFB627" opacity="0.85"/>
	<!-- Scroll edge shadow -->
	<path d="M3.5 6 Q4 4 6 4 L18 4 Q20 4 20.5 6" stroke="#C9A227" stroke-width="1" fill="none" stroke-linecap="round"/>
	<path d="M3.5 18 Q4 20 6 20 L18 20 Q20 20 20.5 18" stroke="#C9A227" stroke-width="1" fill="none" stroke-linecap="round"/>
	<!-- Center rib (palm leaf midrib) -->
	<line x1="12" y1="4" x2="12" y2="20" stroke="#C9A227" stroke-width="0.8" opacity="0.7"/>
	<!-- Script lines (text rows) -->
	<line x1="6.5" y1="8" x2="17.5" y2="8" stroke="#6B0F1A" stroke-width="0.7" opacity="0.55" stroke-linecap="round"/>
	<line x1="6.5" y1="10.5" x2="17.5" y2="10.5" stroke="#6B0F1A" stroke-width="0.7" opacity="0.55" stroke-linecap="round"/>
	<line x1="6.5" y1="13" x2="15" y2="13" stroke="#6B0F1A" stroke-width="0.7" opacity="0.55" stroke-linecap="round"/>
	<line x1="6.5" y1="15.5" x2="17.5" y2="15.5" stroke="#6B0F1A" stroke-width="0.7" opacity="0.55" stroke-linecap="round"/>
	<line x1="6.5" y1="18" x2="13" y2="18" stroke="#6B0F1A" stroke-width="0.7" opacity="0.4" stroke-linecap="round"/>
	<!-- Gold decorative corner ornament (top-left) -->
	<path d="M5 5 Q5.5 5 6 5.5 Q5.5 6 5 6 Z" fill="#C9A227"/>
	<!-- Stylus / pen mark -->
	<path d="M16 6.5 L18.5 4 Q19 3.8 19.2 4 Q19.4 4.3 19.2 4.8 L16.5 7.5 Z" fill="#6B0F1A" opacity="0.7"/>
	<path d="M16 6.5 L16.5 7.5" stroke="#C9A227" stroke-width="0.8" stroke-linecap="round"/>
</svg>
