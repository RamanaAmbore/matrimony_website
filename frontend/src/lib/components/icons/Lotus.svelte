<script lang="ts">
	let { size = 24 }: { size?: number } = $props();
</script>

<!-- Lotus opening — search & connect symbol -->
<svg
	width={size}
	height={size}
	viewBox="0 0 24 24"
	fill="none"
	xmlns="http://www.w3.org/2000/svg"
	aria-label="Lotus flower"
	role="img"
>
	<!-- Water line -->
	<path d="M3 18.5 Q12 17 21 18.5" stroke="#C9A227" stroke-width="0.8" fill="none" opacity="0.5"/>
	<!-- Leaves (green-gold) -->
	<path d="M12 18 Q9 18 7.5 16 Q10 16.5 12 18Z" fill="#C9A227" opacity="0.6"/>
	<path d="M12 18 Q15 18 16.5 16 Q14 16.5 12 18Z" fill="#C9A227" opacity="0.6"/>
	<!-- Outer petals (back row, slightly closed) -->
	<path d="M12 18 Q8 16 7 11 Q9.5 13 12 18Z" fill="#F4A300" opacity="0.65"/>
	<path d="M12 18 Q16 16 17 11 Q14.5 13 12 18Z" fill="#F4A300" opacity="0.65"/>
	<path d="M12 18 Q6 15 6 9 Q9 12 12 18Z" fill="#FFB627" opacity="0.5"/>
	<path d="M12 18 Q18 15 18 9 Q15 12 12 18Z" fill="#FFB627" opacity="0.5"/>
	<!-- Middle petals -->
	<path d="M12 18 Q9 14 9.5 8 Q11 12 12 18Z" fill="#F4A300" opacity="0.8"/>
	<path d="M12 18 Q15 14 14.5 8 Q13 12 12 18Z" fill="#F4A300" opacity="0.8"/>
	<!-- Center front petal (tallest) -->
	<path d="M12 18 Q10.5 12 12 5 Q13.5 12 12 18Z" fill="#FFB627"/>
	<!-- Pollen center -->
	<circle cx="12" cy="15" r="1.8" fill="#C9A227"/>
	<circle cx="12" cy="15" r="0.9" fill="#6B0F1A" opacity="0.6"/>
</svg>
