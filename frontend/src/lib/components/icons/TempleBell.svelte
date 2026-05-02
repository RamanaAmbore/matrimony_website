<script lang="ts">
	let { size = 24 }: { size?: number } = $props();
</script>

<!-- Temple bell (ghanta) — privacy / silence symbol -->
<svg
	width={size}
	height={size}
	viewBox="0 0 24 24"
	fill="none"
	xmlns="http://www.w3.org/2000/svg"
	aria-label="Temple bell"
	role="img"
>
	<!-- Hook ring at top -->
	<path d="M11 2 Q11 1 12 1 Q13 1 13 2 L13 3.5 Q12 3.8 11 3.5 Z" fill="#C9A227"/>
	<!-- Bell body -->
	<path d="M12 3.5 C8 4 5.5 7 5.5 11 L5.5 16 Q5.5 17 6.5 17 L17.5 17 Q18.5 17 18.5 16 L18.5 11 C18.5 7 16 4 12 3.5Z" fill="#F4A300"/>
	<!-- Bell rim (flared bottom) -->
	<path d="M4.5 17 Q4 18.5 5 19 Q12 20.5 19 19 Q20 18.5 19.5 17Z" fill="#C9A227"/>
	<!-- Bell clapper -->
	<line x1="12" y1="17" x2="12" y2="20" stroke="#6B0F1A" stroke-width="1" stroke-linecap="round"/>
	<circle cx="12" cy="20.5" r="1" fill="#6B0F1A"/>
	<!-- Decorative horizontal bands -->
	<path d="M7 10.5 Q12 11.5 17 10.5" stroke="#C9A227" stroke-width="0.6" fill="none" opacity="0.6"/>
	<path d="M6 14 Q12 15 18 14" stroke="#C9A227" stroke-width="0.6" fill="none" opacity="0.5"/>
	<!-- Lotus motif on bell face -->
	<circle cx="12" cy="12" r="1.2" fill="#FFB627" opacity="0.7"/>
	<path d="M12 10.5 Q13 11 12 12 Q11 11 12 10.5Z" fill="#FFB627" opacity="0.6"/>
	<path d="M13.3 11.5 Q13.5 12.5 12 12 Q12.5 11 13.3 11.5Z" fill="#FFB627" opacity="0.6"/>
	<path d="M10.7 11.5 Q10.5 12.5 12 12 Q11.5 11 10.7 11.5Z" fill="#FFB627" opacity="0.6"/>
</svg>
