<script lang="ts">
	let { size = 'sm' }: { size?: 'sm' | 'lg' } = $props();

	const dim = $derived(size === 'lg' ? 96 : 32);
</script>

<!--
  Kalasha logo: central sacred pot with coconut + mango leaf garland,
  flanked by abstract bride (left) and groom (right) silhouettes.
  All paths hand-coded; no external assets.
-->
<svg
	width={dim}
	height={dim}
	viewBox="0 0 96 96"
	fill="none"
	xmlns="http://www.w3.org/2000/svg"
	aria-label="Maratha Kalyanam logo — kalasha with bride and groom"
	role="img"
>
	<defs>
		<linearGradient id="kalasha-grad" x1="0%" y1="0%" x2="100%" y2="100%">
			<stop offset="0%" stop-color="#FF8C32" />
			<stop offset="100%" stop-color="#FFB627" />
		</linearGradient>
		<linearGradient id="figure-grad" x1="0%" y1="0%" x2="0%" y2="100%">
			<stop offset="0%" stop-color="#FFC857" />
			<stop offset="100%" stop-color="#FF8C32" />
		</linearGradient>
	</defs>

	<!-- ── Bride silhouette (left) ─────────────────────────────────────── -->
	<!-- Head -->
	<circle cx="18" cy="28" r="6" fill="url(#figure-grad)" />
	<!-- Dupatta arc over head -->
	<path d="M10 26 Q18 18 26 26" stroke="#C9A227" stroke-width="1.5" fill="none" stroke-linecap="round" />
	<!-- Body / sari drape -->
	<path d="M14 34 Q12 44 13 56 Q15 60 18 60 Q21 60 23 56 Q24 44 22 34 Z" fill="url(#figure-grad)" opacity="0.9" />
	<!-- Sari border (decorative stripe) -->
	<path d="M13.5 55 Q18 57 22.5 55" stroke="#C9A227" stroke-width="1" fill="none" stroke-linecap="round" />
	<!-- Arms — palms together (namaste) -->
	<path d="M14 40 Q10 44 11 48" stroke="#FF8C32" stroke-width="2" stroke-linecap="round" fill="none" />
	<path d="M22 40 Q14 44 11 48" stroke="#FFB627" stroke-width="1.5" stroke-linecap="round" fill="none" />

	<!-- ── Groom silhouette (right) ────────────────────────────────────── -->
	<!-- Head -->
	<circle cx="78" cy="28" r="6" fill="url(#figure-grad)" />
	<!-- Sherwani neckline / collar -->
	<path d="M73 35 L78 33 L83 35" stroke="#C9A227" stroke-width="1.5" fill="none" stroke-linejoin="round" />
	<!-- Sherwani body — straight, formal -->
	<path d="M73 35 Q71 44 72 56 Q74 60 78 60 Q82 60 84 56 Q85 44 83 35 Z" fill="url(#figure-grad)" opacity="0.9" />
	<!-- Sherwani buttons (center line) -->
	<line x1="78" y1="36" x2="78" y2="56" stroke="#C9A227" stroke-width="0.8" stroke-dasharray="2 2" />
	<!-- Pagdi (turban hint) -->
	<path d="M72 24 Q78 20 84 24" stroke="#C9A227" stroke-width="2" fill="none" stroke-linecap="round" />

	<!-- ── Kalasha (centre) ────────────────────────────────────────────── -->
	<!-- Mango leaves left -->
	<path d="M40 22 Q36 16 38 10 Q43 13 40 22Z" fill="#C9A227" opacity="0.85" />
	<path d="M44 18 Q42 11 44 8 Q47 11 44 18Z" fill="#C9A227" opacity="0.75" />
	<!-- Mango leaves right -->
	<path d="M56 22 Q60 16 58 10 Q53 13 56 22Z" fill="#C9A227" opacity="0.85" />
	<path d="M52 18 Q54 11 52 8 Q49 11 52 18Z" fill="#C9A227" opacity="0.75" />
	<!-- Centre leaf -->
	<path d="M48 16 Q48 8 48 6 Q48 8 48 16Z" fill="#C9A227" opacity="0.8" />

	<!-- Coconut on top -->
	<circle cx="48" cy="20" r="6" fill="#C9A227" />
	<!-- Coconut tuft -->
	<path d="M45 15 Q48 11 51 15" stroke="#C9A227" stroke-width="1" fill="none" stroke-linecap="round" />

	<!-- Kalasha neck -->
	<rect x="43" y="25" width="10" height="5" rx="1.5" fill="#C9A227" />

	<!-- Kalasha body — bulbous pot -->
	<path
		d="M38 30 Q33 36 32 44 Q31 52 34 58 L62 58 Q65 52 64 44 Q63 36 58 30 Z"
		fill="url(#kalasha-grad)"
	/>

	<!-- Garland ring around pot rim -->
	<path
		d="M38 30 Q48 27 58 30"
		stroke="#C9A227"
		stroke-width="1.5"
		fill="none"
		stroke-linecap="round"
	/>

	<!-- Decorative horizontal lines on pot body -->
	<path d="M35 38 Q48 41 61 38" stroke="#C9A227" stroke-width="0.8" fill="none" opacity="0.7" />
	<path d="M34 46 Q48 49 62 46" stroke="#C9A227" stroke-width="0.8" fill="none" opacity="0.6" />
	<path d="M34 53 Q48 56 62 53" stroke="#C9A227" stroke-width="0.8" fill="none" opacity="0.5" />

	<!-- Pot base plate -->
	<rect x="36" y="58" width="24" height="4" rx="1.5" fill="#C9A227" />
	<rect x="33" y="62" width="30" height="3" rx="1.5" fill="#C9A227" opacity="0.7" />

	<!-- Small decorative dot on pot belly -->
	<circle cx="48" cy="44" r="2.5" fill="#C9A227" opacity="0.5" />

	<!-- ── Connecting garland swag ──────────────────────────────────────── -->
	<!-- Left swag from bride to kalasha -->
	<path
		d="M24 42 Q30 50 38 46"
		stroke="#C9A227"
		stroke-width="1"
		fill="none"
		stroke-dasharray="2 2"
		opacity="0.6"
	/>
	<!-- Right swag from groom to kalasha -->
	<path
		d="M72 42 Q66 50 58 46"
		stroke="#C9A227"
		stroke-width="1"
		fill="none"
		stroke-dasharray="2 2"
		opacity="0.6"
	/>

	<!-- ── Ground line ─────────────────────────────────────────────────── -->
	<line x1="10" y1="65" x2="86" y2="65" stroke="#C9A227" stroke-width="0.8" opacity="0.4" />
</svg>
