<script lang="ts">
	let { size = 24 }: { size?: number } = $props();
</script>

<!-- Diya (oil lamp) — saffron flame, gold bowl, maroon wick -->
<svg
	width={size}
	height={size}
	viewBox="0 0 24 24"
	fill="none"
	xmlns="http://www.w3.org/2000/svg"
	aria-label="Diya lamp"
	role="img"
>
	<!-- Flame outer -->
	<path d="M12 3 C10 5 9 7 10.5 9 C11.2 10 12 10.2 12 10.2 C12 10.2 12.8 10 13.5 9 C15 7 14 5 12 3Z" fill="#F4A300" opacity="0.9"/>
	<!-- Flame inner (brighter core) -->
	<path d="M12 5 C11 6.5 10.8 8 11.8 9 C12 9.15 12.2 9 12.2 9 C13 8 13 6.5 12 5Z" fill="#FFB627"/>
	<!-- Wick -->
	<line x1="12" y1="10" x2="12" y2="12" stroke="#6B0F1A" stroke-width="1" stroke-linecap="round"/>
	<!-- Diya bowl -->
	<path d="M7 13 Q7.5 11.5 12 11.5 Q16.5 11.5 17 13 Q17.5 15.5 15 16.5 Q12 17.5 9 16.5 Q6.5 15.5 7 13Z" fill="#C9A227"/>
	<!-- Bowl rim highlight -->
	<path d="M8 13 Q12 12.5 16 13" stroke="#FFB627" stroke-width="0.6" fill="none" stroke-linecap="round"/>
	<!-- Spout tip -->
	<path d="M15.5 15.5 Q18 15 18.5 14 Q17.5 13.5 17 13" stroke="#C9A227" stroke-width="1.2" fill="none" stroke-linecap="round"/>
	<!-- Oil glow -->
	<ellipse cx="12" cy="14.5" rx="3" ry="1" fill="#F4A300" opacity="0.3"/>
</svg>
