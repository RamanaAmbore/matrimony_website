<script lang="ts">
	let { size = 24 }: { size?: number } = $props();
</script>

<!-- Conch shell (shankha) — receive details / communication symbol -->
<svg
	width={size}
	height={size}
	viewBox="0 0 24 24"
	fill="none"
	xmlns="http://www.w3.org/2000/svg"
	aria-label="Shankha conch shell"
	role="img"
>
	<!-- Main shell body -->
	<path d="M5 15 Q4 12 6 9 Q8 6 12 5 Q16 5 18 8 Q20 11 19 14 Q18 17 15 18.5 Q12 20 9 19 Q6 18 5 15Z" fill="#FFF8E7" stroke="#C9A227" stroke-width="1"/>
	<!-- Shell spire -->
	<path d="M12 5 Q13 3 14.5 2 Q15.5 3 15 5 Q14 5.5 12 5Z" fill="#FFB627" opacity="0.8"/>
	<path d="M14.5 2 Q16 1.5 17 2.5 Q16.5 4 15 5 Q15.5 3 14.5 2Z" fill="#F4A300" opacity="0.7"/>
	<!-- Shell ridges / growth lines -->
	<path d="M7 13 Q10 16 15 15" stroke="#C9A227" stroke-width="0.7" fill="none" stroke-linecap="round" opacity="0.6"/>
	<path d="M6.5 11 Q9 14.5 14.5 13.5" stroke="#C9A227" stroke-width="0.7" fill="none" stroke-linecap="round" opacity="0.5"/>
	<path d="M7 9 Q9.5 12 14 11" stroke="#C9A227" stroke-width="0.6" fill="none" stroke-linecap="round" opacity="0.4"/>
	<!-- Aperture (opening) -->
	<path d="M5 15 Q5.5 17 7 18 Q8.5 19.5 9 19" stroke="#6B0F1A" stroke-width="0.8" fill="none" stroke-linecap="round"/>
	<!-- Interior highlight -->
	<ellipse cx="11" cy="13" rx="3.5" ry="4" fill="#FFB627" opacity="0.15" transform="rotate(-20 11 13)"/>
	<!-- Decorative dot cluster (auspicious) -->
	<circle cx="16" cy="9" r="0.6" fill="#6B0F1A" opacity="0.4"/>
	<circle cx="17" cy="11" r="0.5" fill="#6B0F1A" opacity="0.3"/>
	<circle cx="15.5" cy="10.5" r="0.4" fill="#6B0F1A" opacity="0.3"/>
</svg>
