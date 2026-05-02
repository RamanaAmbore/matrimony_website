<!--
  HeroIllustration.svelte
  Pure inline SVG depicting an Indian wedding scene — no external image URLs.
  Elements: rising sun, mandap silhouette, marigold garland, two kalashas,
  kolam/rangoli floor pattern, drifting petals.
  Palette: saffron #F4A300, marigold #FFB627, maroon #6B0F1A, gold #C9A227, cream #FFF8E7
-->
<svg
	viewBox="0 0 800 480"
	xmlns="http://www.w3.org/2000/svg"
	aria-hidden="true"
	preserveAspectRatio="xMidYMid slice"
	class="h-full w-full"
>
	<defs>
		<!-- Sky gradient: deep maroon at top → saffron at horizon -->
		<linearGradient id="sky-grad" x1="0" y1="0" x2="0" y2="1">
			<stop offset="0%" stop-color="#2B0A0E"/>
			<stop offset="55%" stop-color="#6B0F1A"/>
			<stop offset="100%" stop-color="#F4A300"/>
		</linearGradient>
		<!-- Ground gradient: saffron → warm cream -->
		<linearGradient id="ground-grad" x1="0" y1="0" x2="0" y2="1">
			<stop offset="0%" stop-color="#F4A300" stop-opacity="0.6"/>
			<stop offset="100%" stop-color="#FFF8E7" stop-opacity="0.3"/>
		</linearGradient>
		<!-- Sun radial glow -->
		<radialGradient id="sun-glow" cx="50%" cy="50%" r="50%">
			<stop offset="0%" stop-color="#FFB627"/>
			<stop offset="60%" stop-color="#F4A300"/>
			<stop offset="100%" stop-color="#F4A300" stop-opacity="0"/>
		</radialGradient>
		<!-- Kalasha gradient -->
		<linearGradient id="kalasha-hl" x1="0%" y1="0%" x2="100%" y2="100%">
			<stop offset="0%" stop-color="#FFB627"/>
			<stop offset="100%" stop-color="#C9A227"/>
		</linearGradient>
		<!-- Pillar gradient -->
		<linearGradient id="pillar-grad" x1="0" y1="0" x2="1" y2="0">
			<stop offset="0%" stop-color="#6B0F1A"/>
			<stop offset="50%" stop-color="#8C1024"/>
			<stop offset="100%" stop-color="#6B0F1A"/>
		</linearGradient>
	</defs>

	<!-- ── Sky background ─────────────────────────────────────────────── -->
	<rect width="800" height="480" fill="url(#sky-grad)"/>

	<!-- ── Rising sun (behind mandap) ────────────────────────────────── -->
	<!-- Outer glow halo -->
	<circle cx="400" cy="220" r="130" fill="url(#sun-glow)" opacity="0.35"/>
	<!-- Concentric ray rings -->
	{#each [110, 95, 82] as r, i}
		<circle cx="400" cy="220" r={r} fill="none" stroke="#C9A227" stroke-width="1" opacity={0.15 + i * 0.08}/>
	{/each}
	<!-- Sun disc -->
	<circle cx="400" cy="220" r="70" fill="#F4A300" opacity="0.9"/>
	<circle cx="400" cy="220" r="58" fill="#FFB627"/>
	<!-- Radiating rays (24 rays) -->
	{#each Array.from({ length: 24 }) as _, i}
		{@const angle = (i * 360) / 24}
		{@const rad = (angle * Math.PI) / 180}
		{@const x1 = 400 + Math.cos(rad) * 62}
		{@const y1 = 220 + Math.sin(rad) * 62}
		{@const x2 = 400 + Math.cos(rad) * (i % 3 === 0 ? 115 : 95)}
		{@const y2 = 220 + Math.sin(rad) * (i % 3 === 0 ? 115 : 95)}
		<line {x1} {y1} {x2} {y2} stroke="#C9A227" stroke-width={i % 3 === 0 ? 2 : 1} opacity={0.6}/>
	{/each}

	<!-- ── Ground / floor platform ───────────────────────────────────── -->
	<rect x="0" y="370" width="800" height="110" fill="url(#ground-grad)"/>
	<!-- Platform edge highlight -->
	<rect x="100" y="368" width="600" height="6" rx="3" fill="#C9A227" opacity="0.6"/>

	<!-- ── Kolam / rangoli floor pattern ──────────────────────────────── -->
	<!-- Circular kolam centred under mandap -->
	<g transform="translate(400 370)" opacity="0.7">
		<!-- Outer ring dots -->
		{#each Array.from({ length: 16 }) as _, i}
			{@const a = (i * 360) / 16}
			{@const rx = Math.cos((a * Math.PI) / 180) * 90}
			{@const ry = Math.sin((a * Math.PI) / 180) * 22}
			<circle cx={rx} cy={ry} r="2.5" fill="#C9A227" opacity="0.8"/>
		{/each}
		<!-- Middle ring -->
		{#each Array.from({ length: 12 }) as _, i}
			{@const a = (i * 360) / 12}
			{@const rx = Math.cos((a * Math.PI) / 180) * 62}
			{@const ry = Math.sin((a * Math.PI) / 180) * 15}
			<ellipse cx={rx} cy={ry} rx="3" ry="2" fill="#F4A300" opacity="0.65"/>
		{/each}
		<!-- Petal arcs -->
		{#each Array.from({ length: 8 }) as _, i}
			{@const a = (i * 45) * Math.PI / 180}
			{@const px = Math.cos(a) * 36}
			{@const py = Math.sin(a) * 9}
			<ellipse cx={px} cy={py} rx="12" ry="5" fill="#FFB627" opacity="0.45" transform={`rotate(${i * 45} ${px} ${py})`}/>
		{/each}
		<!-- Center dot -->
		<circle cx="0" cy="0" r="6" fill="#6B0F1A"/>
		<circle cx="0" cy="0" r="3.5" fill="#F4A300"/>
		<circle cx="0" cy="0" r="1.5" fill="#FFF8E7"/>
	</g>

	<!-- ── Mandap (four pillars + canopy roof) ───────────────────────── -->
	<!-- Pillar positions: left-outer=190, left-inner=290, right-inner=510, right-outer=610 -->
	<!-- Pillar base plinths -->
	{#each [178, 278, 498, 598] as bx}
		<rect x={bx} y="358" width="24" height="16" rx="3" fill="#C9A227"/>
	{/each}
	<!-- Pillars -->
	{#each [182, 282, 502, 602] as px}
		<rect x={px} y="185" width="16" height="178" rx="4" fill="url(#pillar-grad)"/>
		<!-- Pillar decorative band -->
		<rect x={px - 2} y="230" width="20" height="8" rx="2" fill="#C9A227" opacity="0.7"/>
		<rect x={px - 2} y="300" width="20" height="8" rx="2" fill="#C9A227" opacity="0.6"/>
	{/each}
	<!-- Canopy / torana top beam -->
	<rect x="180" y="172" width="440" height="18" rx="5" fill="#6B0F1A"/>
	<!-- Gold edging on canopy beam -->
	<rect x="180" y="172" width="440" height="5" rx="3" fill="#C9A227"/>
	<rect x="180" y="183" width="440" height="4" rx="2" fill="#C9A227" opacity="0.5"/>
	<!-- Canopy roof (sloped pyramid) -->
	<path d="M175 172 L400 110 L625 172Z" fill="#6B0F1A"/>
	<path d="M185 172 L400 118 L615 172Z" fill="#8C1024"/>
	<!-- Roof ridge line -->
	<path d="M185 172 L400 118 L615 172" stroke="#C9A227" stroke-width="2" fill="none" opacity="0.7"/>
	<!-- Roof edge scallops -->
	{#each Array.from({ length: 22 }) as _, i}
		<path
			d={`M${185 + i * 20} 172 Q${195 + i * 20} 162 ${205 + i * 20} 172`}
			stroke="#C9A227"
			stroke-width="1.5"
			fill="#FFB627"
			opacity="0.6"
		/>
	{/each}
	<!-- Finial on roof peak -->
	<circle cx="400" cy="108" r="6" fill="#C9A227"/>
	<circle cx="400" cy="100" r="4" fill="#F4A300"/>
	<circle cx="400" cy="94" r="2.5" fill="#C9A227"/>

	<!-- ── Marigold garland draped across canopy beam ─────────────────── -->
	<!-- Left swag (left pillar → centre) -->
	<path d="M190 180 Q290 215 400 195" stroke="#F4A300" stroke-width="4" fill="none" stroke-linecap="round" opacity="0.9"/>
	<!-- Right swag (centre → right pillar) -->
	<path d="M400 195 Q510 215 610 180" stroke="#F4A300" stroke-width="4" fill="none" stroke-linecap="round" opacity="0.9"/>
	<!-- Marigold flower clusters along garland (left swag) -->
	{#each [[220, 194], [260, 207], [310, 214], [355, 207], [400, 196]] as [fx, fy]}
		<circle cx={fx} cy={fy} r="7" fill="#FFB627"/>
		<circle cx={fx} cy={fy} r="4" fill="#F4A300"/>
		<circle cx={fx} cy={fy} r="2" fill="#C9A227"/>
	{/each}
	<!-- Right swag flowers -->
	{#each [[445, 207], [490, 214], [540, 207], [580, 194]] as [fx, fy]}
		<circle cx={fx} cy={fy} r="7" fill="#FFB627"/>
		<circle cx={fx} cy={fy} r="4" fill="#F4A300"/>
		<circle cx={fx} cy={fy} r="2" fill="#C9A227"/>
	{/each}

	<!-- ── Kalasha (left) ─────────────────────────────────────────────── -->
	<g transform="translate(155 290)">
		<!-- Mango leaves -->
		<path d="M18 0 Q14 -8 16 -15 Q20 -12 18 0Z" fill="#C9A227" opacity="0.9"/>
		<path d="M22 -4 Q22 -14 22 -18 Q22 -14 22 -4Z" fill="#C9A227" opacity="0.8"/>
		<path d="M26 0 Q30 -8 28 -15 Q24 -12 26 0Z" fill="#C9A227" opacity="0.9"/>
		<!-- Coconut -->
		<circle cx="22" cy="3" r="7" fill="#C9A227"/>
		<!-- Neck -->
		<rect x="18" y="9" width="8" height="5" rx="2" fill="#C9A227"/>
		<!-- Pot body -->
		<path d="M10 14 Q5 22 5 30 Q5 40 11 44 L33 44 Q39 40 39 30 Q39 22 34 14Z" fill="url(#kalasha-hl)"/>
		<!-- Rim -->
		<path d="M10 14 Q22 11 34 14" stroke="#C9A227" stroke-width="1.5" fill="none"/>
		<!-- Decorative bands -->
		<path d="M7 28 Q22 31 37 28" stroke="#C9A227" stroke-width="0.8" fill="none" opacity="0.7"/>
		<path d="M6 37 Q22 40 38 37" stroke="#C9A227" stroke-width="0.8" fill="none" opacity="0.5"/>
		<!-- Base -->
		<rect x="10" y="44" width="24" height="5" rx="2" fill="#C9A227"/>
		<rect x="8" y="49" width="28" height="3" rx="1.5" fill="#C9A227" opacity="0.6"/>
		<!-- Gold rim dots -->
		{#each [10, 15, 20, 25, 30, 34] as dotx}
			<circle cx={dotx} cy="14" r="1.2" fill="#C9A227" opacity="0.8"/>
		{/each}
	</g>

	<!-- ── Kalasha (right) ────────────────────────────────────────────── -->
	<g transform="translate(601 290)">
		<!-- Mango leaves -->
		<path d="M18 0 Q14 -8 16 -15 Q20 -12 18 0Z" fill="#C9A227" opacity="0.9"/>
		<path d="M22 -4 Q22 -14 22 -18 Q22 -14 22 -4Z" fill="#C9A227" opacity="0.8"/>
		<path d="M26 0 Q30 -8 28 -15 Q24 -12 26 0Z" fill="#C9A227" opacity="0.9"/>
		<!-- Coconut -->
		<circle cx="22" cy="3" r="7" fill="#C9A227"/>
		<!-- Neck -->
		<rect x="18" y="9" width="8" height="5" rx="2" fill="#C9A227"/>
		<!-- Pot body -->
		<path d="M10 14 Q5 22 5 30 Q5 40 11 44 L33 44 Q39 40 39 30 Q39 22 34 14Z" fill="url(#kalasha-hl)"/>
		<!-- Rim -->
		<path d="M10 14 Q22 11 34 14" stroke="#C9A227" stroke-width="1.5" fill="none"/>
		<!-- Decorative bands -->
		<path d="M7 28 Q22 31 37 28" stroke="#C9A227" stroke-width="0.8" fill="none" opacity="0.7"/>
		<path d="M6 37 Q22 40 38 37" stroke="#C9A227" stroke-width="0.8" fill="none" opacity="0.5"/>
		<!-- Base -->
		<rect x="10" y="44" width="24" height="5" rx="2" fill="#C9A227"/>
		<rect x="8" y="49" width="28" height="3" rx="1.5" fill="#C9A227" opacity="0.6"/>
		<!-- Gold rim dots -->
		{#each [10, 15, 20, 25, 30, 34] as dotx}
			<circle cx={dotx} cy="14" r="1.2" fill="#C9A227" opacity="0.8"/>
		{/each}
	</g>

	<!-- ── Drifting petals ────────────────────────────────────────────── -->
	<!-- Static petal positions distributed across the scene; no JS animation needed
	     (CSS animation can be layered via class if desired, but kept perf-safe here) -->
	{#each [
		{ x: 70,  y: 80,  rx: 7, ry: 4,  rot: 20,  op: 0.55, c: '#FFB627' },
		{ x: 140, y: 140, rx: 5, ry: 3,  rot: -30, op: 0.45, c: '#F4A300' },
		{ x: 230, y: 60,  rx: 8, ry: 4,  rot: 45,  op: 0.5,  c: '#FFB627' },
		{ x: 320, y: 100, rx: 5, ry: 3,  rot: -15, op: 0.4,  c: '#C9A227' },
		{ x: 460, y: 75,  rx: 6, ry: 3.5,rot: 60,  op: 0.5,  c: '#F4A300' },
		{ x: 560, y: 120, rx: 7, ry: 4,  rot: -40, op: 0.45, c: '#FFB627' },
		{ x: 670, y: 55,  rx: 5, ry: 3,  rot: 25,  op: 0.55, c: '#C9A227' },
		{ x: 730, y: 150, rx: 8, ry: 4,  rot: -55, op: 0.4,  c: '#F4A300' },
		{ x: 50,  y: 200, rx: 6, ry: 3,  rot: 35,  op: 0.35, c: '#FFB627' },
		{ x: 750, y: 240, rx: 5, ry: 3,  rot: -25, op: 0.35, c: '#F4A300' },
		{ x: 100, y: 300, rx: 7, ry: 3.5,rot: 50,  op: 0.3,  c: '#C9A227' },
		{ x: 690, y: 310, rx: 6, ry: 3,  rot: -45, op: 0.3,  c: '#FFB627' },
		{ x: 200, y: 250, rx: 4, ry: 2.5,rot: 10,  op: 0.4,  c: '#F4A300' },
		{ x: 600, y: 260, rx: 5, ry: 2.5,rot: -20, op: 0.4,  c: '#FFB627' },
		{ x: 350, y: 50,  rx: 6, ry: 3,  rot: 70,  op: 0.5,  c: '#F4A300' }
	] as p}
		<ellipse
			cx={p.x}
			cy={p.y}
			rx={p.rx}
			ry={p.ry}
			fill={p.c}
			opacity={p.op}
			transform={`rotate(${p.rot} ${p.x} ${p.y})`}
		/>
	{/each}
</svg>
