<script lang="ts">
	let { class: className = '' }: { class?: string } = $props();
</script>

<div class="flex items-center gap-4 py-4 {className}" role="presentation">
	<!-- Left line -->
	<div class="h-px flex-1 bg-gradient-to-r from-transparent to-gold/40"></div>

	<!-- Kalasha (sacred pot) SVG motif -->
	<svg
		width="48"
		height="48"
		viewBox="0 0 48 48"
		fill="none"
		xmlns="http://www.w3.org/2000/svg"
		aria-hidden="true"
	>
		<!-- Mango leaves -->
		<path d="M16 10 Q12 6 14 2 Q18 4 16 10Z" fill="#c9a227" opacity="0.7" />
		<path d="M24 8 Q24 2 24 0 Q24 2 24 8Z" fill="#c9a227" opacity="0.7" />
		<path d="M32 10 Q36 6 34 2 Q30 4 32 10Z" fill="#c9a227" opacity="0.7" />
		<!-- Coconut on top -->
		<circle cx="24" cy="12" r="4" fill="#c9a227" />
		<!-- Kalasha body -->
		<path
			d="M18 16 Q14 20 13 26 Q12 32 14 36 L34 36 Q36 32 35 26 Q34 20 30 16Z"
			fill="#f4a300"
			opacity="0.8"
		/>
		<!-- Neck -->
		<rect x="20" y="13" width="8" height="4" rx="1" fill="#c9a227" />
		<!-- Base -->
		<rect x="16" y="36" width="16" height="3" rx="1" fill="#6b0f1a" />
		<rect x="14" y="39" width="20" height="2" rx="1" fill="#6b0f1a" />
		<!-- Decorative lines on pot -->
		<path d="M16 22 Q24 24 32 22" stroke="#6b0f1a" stroke-width="0.5" fill="none" opacity="0.5" />
		<path d="M15 28 Q24 30 33 28" stroke="#6b0f1a" stroke-width="0.5" fill="none" opacity="0.5" />
	</svg>

	<!-- Right line -->
	<div class="h-px flex-1 bg-gradient-to-l from-transparent to-gold/40"></div>
</div>
