<script lang="ts">
	let { size = 'sm' }: { size?: 'sm' | 'lg' } = $props();

	const dim = $derived(size === 'lg' ? 96 : 32);
</script>

<!--
  Kalasha logo: elaborate sacred pot with coconut, three distinct mango leaves,
  gold rim dots, flanked by an Indian bride (sari pallu over head, bindi, jhumka)
  and an Indian groom (pheta turban, kurta-pajama outline).
  Palette: maroon #6B0F1A, saffron #F4A300, marigold #FFB627, gold #C9A227, cream #FFF8E7.
  No external image assets — all inline paths.
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
		<linearGradient id="kalasha-g" x1="0%" y1="0%" x2="100%" y2="100%">
			<stop offset="0%" stop-color="#F4A300"/>
			<stop offset="100%" stop-color="#C9A227"/>
		</linearGradient>
		<linearGradient id="bride-g" x1="0%" y1="0%" x2="0%" y2="100%">
			<stop offset="0%" stop-color="#F4A300"/>
			<stop offset="100%" stop-color="#6B0F1A"/>
		</linearGradient>
		<linearGradient id="groom-g" x1="0%" y1="0%" x2="0%" y2="100%">
			<stop offset="0%" stop-color="#FFB627"/>
			<stop offset="100%" stop-color="#6B0F1A"/>
		</linearGradient>
	</defs>

	<!-- ══ BRIDE (left) ══════════════════════════════════════════════ -->
	<!-- Head -->
	<circle cx="17" cy="27" r="5.5" fill="url(#bride-g)"/>
	<!-- Pallu / dupatta draped over head — curved arc -->
	<path d="M9 24 Q17 16 25 22" stroke="#6B0F1A" stroke-width="2.5" fill="none" stroke-linecap="round"/>
	<path d="M9 24 Q17 17 25 22" stroke="#C9A227" stroke-width="1" fill="none" stroke-linecap="round" opacity="0.8"/>
	<!-- Pallu drape falling left of head -->
	<path d="M9 24 Q7 30 8 38" stroke="#6B0F1A" stroke-width="2" fill="none" stroke-linecap="round"/>
	<!-- Bindi dot on forehead -->
	<circle cx="17" cy="25" r="1.1" fill="#6B0F1A"/>
	<!-- Jhumka (teardrop earring hint) -->
	<path d="M11.5 28 Q10.5 30.5 11.5 31.5" stroke="#C9A227" stroke-width="1.2" fill="none" stroke-linecap="round"/>
	<circle cx="11.5" cy="32" r="1" fill="#C9A227"/>
	<!-- Sari body — wrapped drape shape -->
	<path d="M12.5 32 Q10 42 11 55 Q13 60 17 61 Q21 60 23 55 Q24 42 21.5 32 Z" fill="url(#bride-g)" opacity="0.9"/>
	<!-- Sari decorative border (zari strip) -->
	<path d="M11.2 54 Q17 57 22.8 54" stroke="#C9A227" stroke-width="1.2" fill="none" stroke-linecap="round"/>
	<!-- Pallu horizontal band across hip -->
	<path d="M12.5 42 Q17 43.5 21.5 42" stroke="#C9A227" stroke-width="0.8" fill="none" stroke-linecap="round" opacity="0.6"/>
	<!-- Arms folded (namaste hint) -->
	<path d="M13 38 Q9 43 10 47" stroke="#F4A300" stroke-width="1.8" stroke-linecap="round" fill="none"/>
	<path d="M21 38 Q13 43 10 47" stroke="#C9A227" stroke-width="1.2" stroke-linecap="round" fill="none" opacity="0.7"/>

	<!-- ══ GROOM (right) ══════════════════════════════════════════════ -->
	<!-- Head -->
	<circle cx="79" cy="27" r="5.5" fill="url(#groom-g)"/>
	<!-- Pheta turban — wrapped layers -->
	<path d="M73 24 Q79 19 85 24" stroke="#6B0F1A" stroke-width="3" fill="none" stroke-linecap="round"/>
	<path d="M73 24 Q79 20 85 24" stroke="#F4A300" stroke-width="1.5" fill="none" stroke-linecap="round"/>
	<!-- Turban fan / pag end -->
	<path d="M85 24 Q88 21 87 19 Q86 18 85 20" fill="#6B0F1A"/>
	<!-- Turban jewel -->
	<circle cx="79" cy="21" r="1.3" fill="#C9A227"/>
	<!-- Kurta collar / neckline -->
	<path d="M74.5 33.5 L79 31 L83.5 33.5" stroke="#C9A227" stroke-width="1.5" fill="none" stroke-linejoin="round"/>
	<!-- Kurta body — straight, formal cut -->
	<path d="M74 33.5 Q72 43 73 55 Q75 60 79 61 Q83 60 85 55 Q86 43 84 33.5 Z" fill="url(#groom-g)" opacity="0.9"/>
	<!-- Center button placket -->
	<line x1="79" y1="34" x2="79" y2="57" stroke="#C9A227" stroke-width="0.9" stroke-dasharray="2.5 2"/>
	<!-- Kurta side seam (kurta shape) -->
	<path d="M73.5 33.5 Q71.5 43 72.5 55" stroke="#C9A227" stroke-width="0.6" fill="none" opacity="0.4"/>
	<path d="M84.5 33.5 Q86.5 43 85.5 55" stroke="#C9A227" stroke-width="0.6" fill="none" opacity="0.4"/>
	<!-- Arms at sides -->
	<path d="M74 40 Q70 46 71 50" stroke="#FFB627" stroke-width="1.8" stroke-linecap="round" fill="none"/>
	<path d="M84 40 Q88 46 87 50" stroke="#FFB627" stroke-width="1.8" stroke-linecap="round" fill="none"/>

	<!-- ══ KALASHA (centre) ════════════════════════════════════════════ -->
	<!-- Three distinct mango leaves above rim -->
	<!-- Left leaf -->
	<path d="M40 23 Q35 15 37.5 9 Q42 12.5 40 23Z" fill="#C9A227" opacity="0.9"/>
	<!-- Right leaf -->
	<path d="M56 23 Q61 15 58.5 9 Q54 12.5 56 23Z" fill="#C9A227" opacity="0.9"/>
	<!-- Centre leaf (taller) -->
	<path d="M48 21 Q47 12 48 7 Q49 12 48 21Z" fill="#C9A227" opacity="0.85"/>
	<!-- Small left-tilt leaf -->
	<path d="M44 19 Q41 13 43 9 Q46 11.5 44 19Z" fill="#C9A227" opacity="0.7"/>
	<!-- Small right-tilt leaf -->
	<path d="M52 19 Q55 13 53 9 Q50 11.5 52 19Z" fill="#C9A227" opacity="0.7"/>

	<!-- Coconut — layered for dimension -->
	<circle cx="48" cy="21" r="7" fill="#C9A227"/>
	<circle cx="48" cy="21" r="5" fill="#FFB627" opacity="0.6"/>
	<!-- Coconut eye marks -->
	<circle cx="46" cy="20" r="0.8" fill="#6B0F1A" opacity="0.5"/>
	<circle cx="48.5" cy="19.5" r="0.8" fill="#6B0F1A" opacity="0.5"/>
	<circle cx="50.5" cy="20.5" r="0.8" fill="#6B0F1A" opacity="0.5"/>

	<!-- Neck — proper bulge with tapered sides -->
	<path d="M43.5 27 Q43 26 44.5 25 L51.5 25 Q53 26 52.5 27 Q52 29.5 51 30 L45 30 Q44 29.5 43.5 27Z" fill="#C9A227"/>

	<!-- Pot body — bulbous with defined bulge -->
	<path d="M38 30 Q32 37 31 46 Q30 54 33 60 L63 60 Q66 54 65 46 Q64 37 58 30 Z" fill="url(#kalasha-g)"/>

	<!-- Rim arc (join neck to pot) -->
	<path d="M38 30 Q48 27.5 58 30" stroke="#C9A227" stroke-width="1.5" fill="none" stroke-linecap="round"/>

	<!-- Gold rim dots -->
	{#each [38, 42, 48, 54, 58] as dotx}
		<circle cx={dotx} cy="30" r="1.3" fill="#C9A227" opacity="0.9"/>
	{/each}

	<!-- Decorative meander lines on pot belly -->
	<path d="M34 40 Q48 43.5 62 40" stroke="#C9A227" stroke-width="0.9" fill="none" opacity="0.7"/>
	<path d="M33 49 Q48 52.5 63 49" stroke="#C9A227" stroke-width="0.9" fill="none" opacity="0.6"/>
	<path d="M33 56 Q48 59 63 56" stroke="#C9A227" stroke-width="0.8" fill="none" opacity="0.45"/>

	<!-- Central kalasha motif (lotus on belly) -->
	<circle cx="48" cy="46" r="3.5" fill="#6B0F1A" opacity="0.3"/>
	<circle cx="48" cy="46" r="2" fill="#C9A227" opacity="0.6"/>

	<!-- Base plate — double ring for elegance -->
	<rect x="36" y="60" width="24" height="4.5" rx="2" fill="#C9A227"/>
	<rect x="33" y="64" width="30" height="3" rx="1.5" fill="#C9A227" opacity="0.65"/>
	<!-- Base dots -->
	{#each [36, 41, 48, 55, 60] as dotx}
		<circle cx={dotx} cy="62" r="0.8" fill="#FFB627" opacity="0.6"/>
	{/each}

	<!-- ══ Connecting garland swags ════════════════════════════════════ -->
	<!-- Left swag: bride → kalasha -->
	<path d="M25 45 Q31 53 37.5 49" stroke="#C9A227" stroke-width="1.2" fill="none" stroke-dasharray="3 2" opacity="0.65"/>
	<!-- Right swag: kalasha → groom -->
	<path d="M58.5 49 Q65 53 73 45" stroke="#C9A227" stroke-width="1.2" fill="none" stroke-dasharray="3 2" opacity="0.65"/>
	<!-- Small marigold flowers on swags -->
	<circle cx="31" cy="51" r="2" fill="#FFB627" opacity="0.7"/>
	<circle cx="65" cy="51" r="2" fill="#FFB627" opacity="0.7"/>

	<!-- ══ Ground line ═════════════════════════════════════════════════ -->
	<line x1="8" y1="67" x2="88" y2="67" stroke="#C9A227" stroke-width="0.9" opacity="0.4"/>
</svg>
