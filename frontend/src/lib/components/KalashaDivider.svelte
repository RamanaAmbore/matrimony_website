<script lang="ts">
	let { class: className = '' }: { class?: string } = $props();
</script>

<div class="flex items-center gap-4 py-4 {className}" role="presentation">
	<!-- Left line -->
	<div class="h-px flex-1 bg-gradient-to-r from-transparent to-gold/40"></div>

	<!-- Diya (sacred oil lamp) SVG motif -->
	<svg
		width="40"
		height="50"
		viewBox="0 0 40 50"
		fill="none"
		xmlns="http://www.w3.org/2000/svg"
		aria-hidden="true"
	>
		<!-- Flame glow (soft outer halo) -->
		<ellipse cx="20" cy="11" rx="5" ry="7" fill="#f4a300" opacity="0.25" />
		<!-- Flame outer (saffron teardrop) -->
		<path d="M20 2 C17 5 15 9 16.5 12 C17.5 14 22.5 14 23.5 12 C25 9 23 5 20 2Z" fill="#f4a300" />
		<!-- Flame inner (cream highlight) -->
		<path
			d="M20 5 C18.5 7.5 18 10 18.8 12 C19.2 12.9 20.8 12.9 21.2 12 C22 10 21.5 7.5 20 5Z"
			fill="#fff8e7"
			opacity="0.75"
		/>
		<!-- Wick -->
		<line x1="20" y1="14" x2="20" y2="18" stroke="#3d2000" stroke-width="1" stroke-linecap="round" />
		<!-- Diya rim (top ellipse — dark gold) -->
		<ellipse cx="20" cy="20" rx="11" ry="3" fill="#b8860b" />
		<!-- Oil well (inner ellipse — darker, semi-transparent) -->
		<ellipse cx="20" cy="20" rx="7.5" ry="1.8" fill="#7a5a00" opacity="0.5" />
		<!-- Diya body (rounded clay cup shape) -->
		<path
			d="M9 20 Q7 26 9 31 Q11 35 20 36 Q29 35 31 31 Q33 26 31 20Z"
			fill="#c9a227"
		/>
		<!-- Decorative arc on body -->
		<path
			d="M12 26 Q20 29 28 26"
			stroke="#b8860b"
			stroke-width="0.8"
			fill="none"
			opacity="0.7"
		/>
		<!-- Base plate top (maroon) -->
		<rect x="11" y="36" width="18" height="4" rx="2" fill="#6b0f1a" />
		<!-- Base plate bottom (maroon, wider) -->
		<rect x="8" y="40" width="24" height="3" rx="1.5" fill="#6b0f1a" />
	</svg>

	<!-- Right line -->
	<div class="h-px flex-1 bg-gradient-to-l from-transparent to-gold/40"></div>
</div>
