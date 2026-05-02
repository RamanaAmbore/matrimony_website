<script lang="ts">
	let { size = 24 }: { size?: number } = $props();
</script>

<!-- Kalasha with a tilaka/checkmark — admin-verified symbol -->
<svg
	width={size}
	height={size}
	viewBox="0 0 24 24"
	fill="none"
	xmlns="http://www.w3.org/2000/svg"
	aria-label="Verified kalasha"
	role="img"
>
	<!-- Mango leaves -->
	<path d="M9 5 Q8 3 9 1.5 Q10.5 2 9 5Z" fill="#C9A227" opacity="0.9"/>
	<path d="M12 4 Q12 2 12 1 Q12 2 12 4Z" fill="#C9A227" opacity="0.8"/>
	<path d="M15 5 Q16 3 15 1.5 Q13.5 2 15 5Z" fill="#C9A227" opacity="0.9"/>
	<!-- Coconut -->
	<circle cx="12" cy="5.5" r="2" fill="#C9A227"/>
	<!-- Neck -->
	<rect x="10.5" y="7" width="3" height="2" rx="0.7" fill="#C9A227"/>
	<!-- Pot body -->
	<path d="M8 9 Q6.5 11 6.5 13 Q6.5 16 8.5 17 L15.5 17 Q17.5 16 17.5 13 Q17.5 11 16 9Z" fill="#F4A300"/>
	<!-- Pot rim -->
	<path d="M8 9 Q12 7.8 16 9" stroke="#C9A227" stroke-width="0.8" fill="none" stroke-linecap="round"/>
	<!-- Decorative band -->
	<path d="M7 13 Q12 14 17 13" stroke="#C9A227" stroke-width="0.5" fill="none" opacity="0.7"/>
	<!-- Base -->
	<rect x="8.5" y="17" width="7" height="1.5" rx="0.6" fill="#C9A227"/>
	<rect x="7.5" y="18.5" width="9" height="1" rx="0.5" fill="#C9A227" opacity="0.6"/>
	<!-- Checkmark badge (bottom-right) — maroon circle + cream tick -->
	<circle cx="17" cy="18" r="3.5" fill="#6B0F1A"/>
	<path d="M15.2 18 L16.5 19.3 L18.8 16.8" stroke="#FFF8E7" stroke-width="1.1" stroke-linecap="round" stroke-linejoin="round" fill="none"/>
</svg>
