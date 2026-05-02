<script lang="ts">
	let { size = 24 }: { size?: number } = $props();
</script>

<!-- Akshat — rice grains with turmeric tint in a circle — verification symbol -->
<svg
	width={size}
	height={size}
	viewBox="0 0 24 24"
	fill="none"
	xmlns="http://www.w3.org/2000/svg"
	aria-label="Akshat rice grains"
	role="img"
>
	<!-- Outer circle -->
	<circle cx="12" cy="12" r="10" stroke="#C9A227" stroke-width="1.2" fill="#FFF8E7"/>
	<!-- Rice grains radiating from center — 8 grains -->
	<ellipse cx="12" cy="5.5" rx="1.2" ry="2.5" fill="#FFB627" opacity="0.85"/>
	<ellipse cx="12" cy="5.5" rx="1.2" ry="2.5" fill="#FFB627" opacity="0.85" transform="rotate(45 12 12)"/>
	<ellipse cx="12" cy="5.5" rx="1.2" ry="2.5" fill="#FFB627" opacity="0.85" transform="rotate(90 12 12)"/>
	<ellipse cx="12" cy="5.5" rx="1.2" ry="2.5" fill="#FFB627" opacity="0.85" transform="rotate(135 12 12)"/>
	<ellipse cx="12" cy="5.5" rx="1.2" ry="2.5" fill="#F4A300" opacity="0.7" transform="rotate(22.5 12 12)"/>
	<ellipse cx="12" cy="5.5" rx="1.2" ry="2.5" fill="#F4A300" opacity="0.7" transform="rotate(67.5 12 12)"/>
	<ellipse cx="12" cy="5.5" rx="1.2" ry="2.5" fill="#F4A300" opacity="0.7" transform="rotate(112.5 12 12)"/>
	<ellipse cx="12" cy="5.5" rx="1.2" ry="2.5" fill="#F4A300" opacity="0.7" transform="rotate(157.5 12 12)"/>
	<!-- Center dot (kumkum) -->
	<circle cx="12" cy="12" r="2" fill="#6B0F1A"/>
	<circle cx="12" cy="12" r="1" fill="#F4A300"/>
</svg>
