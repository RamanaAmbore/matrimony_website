<script lang="ts">
	let { size = 24 }: { size?: number } = $props();
</script>

<!-- Mango-leaf garland (torana) — auspicious welcome symbol -->
<svg
	width={size}
	height={size}
	viewBox="0 0 24 24"
	fill="none"
	xmlns="http://www.w3.org/2000/svg"
	aria-label="Mango leaf garland"
	role="img"
>
	<!-- String / torana cord -->
	<path d="M2 8 Q6 6 12 7 Q18 6 22 8" stroke="#C9A227" stroke-width="1" fill="none" stroke-linecap="round"/>
	<!-- Mango leaves hanging down from string — alternating sides -->
	<!-- Leaf 1 (left) -->
	<path d="M4 8 Q3 10 4 13 Q5.5 12 4 8Z" fill="#C9A227" opacity="0.85"/>
	<!-- Leaf 2 -->
	<path d="M7 7.5 Q6.5 10 7.5 13 Q8.5 12 7 7.5Z" fill="#FFB627" opacity="0.8"/>
	<!-- Leaf 3 -->
	<path d="M10 7.2 Q9.5 10 10.5 13 Q11.5 12 10 7.2Z" fill="#C9A227" opacity="0.85"/>
	<!-- Leaf 4 (center / slightly longer) -->
	<path d="M12 7 Q11.5 10.5 12.5 14 Q13.5 12.5 12 7Z" fill="#F4A300" opacity="0.75"/>
	<!-- Leaf 5 -->
	<path d="M14 7.2 Q13.5 10 14.5 13 Q15.5 12 14 7.2Z" fill="#C9A227" opacity="0.85"/>
	<!-- Leaf 6 -->
	<path d="M17 7.5 Q16.5 10 17.5 13 Q18.5 12 17 7.5Z" fill="#FFB627" opacity="0.8"/>
	<!-- Leaf 7 (right) -->
	<path d="M20 8 Q19 10 20 13 Q21.5 12 20 8Z" fill="#C9A227" opacity="0.85"/>
	<!-- Marigold flowers on cord -->
	<circle cx="2.5" cy="7.5" r="1.3" fill="#F4A300"/>
	<circle cx="2.5" cy="7.5" r="0.7" fill="#FFB627"/>
	<circle cx="12" cy="6.8" r="1.5" fill="#6B0F1A"/>
	<circle cx="12" cy="6.8" r="0.8" fill="#F4A300"/>
	<circle cx="21.5" cy="7.5" r="1.3" fill="#F4A300"/>
	<circle cx="21.5" cy="7.5" r="0.7" fill="#FFB627"/>
	<!-- Small dots on leaves (venation hint) -->
	<line x1="4" y1="9" x2="4" y2="12" stroke="#6B0F1A" stroke-width="0.3" opacity="0.4"/>
	<line x1="12" y1="9" x2="12.2" y2="13" stroke="#6B0F1A" stroke-width="0.3" opacity="0.4"/>
	<line x1="20" y1="9" x2="20" y2="12" stroke="#6B0F1A" stroke-width="0.3" opacity="0.4"/>
</svg>
