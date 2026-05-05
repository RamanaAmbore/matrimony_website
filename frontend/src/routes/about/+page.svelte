<script lang="ts">
	import { tx } from '$lib/i18n';
	import { langStore } from '$lib/stores/lang.svelte';
</script>

<svelte:head>
	<title>About — Maratha Kalyanam</title>
</svelte:head>

<div class="mx-auto max-w-3xl px-4 py-16">
	<h1 class="mb-1 font-serif text-4xl font-bold text-maroon">
		About Us
		<span class="block" lang={langStore.current}>{tx('aboutHeading', langStore.current)}</span>
	</h1>
	<p class="mb-8 text-ink/60">Maratha Kalyanam · <span lang={langStore.current}>{tx('brand', langStore.current)}</span> — Our Story</p>

	<div class="card p-6 space-y-8">
		<section>
			<h2 class="mb-3 font-serif text-2xl font-semibold text-maroon">
				Our Mission
				<span class="block" lang={langStore.current}>{tx('aboutMissionHeading', langStore.current)}</span>
			</h2>
			<p class="mt-1 text-ink/80">
				Maratha Kalyanam was founded with a simple purpose: to help Maratha families find compatible
				life partners who share their cultural heritage, values, and traditions. We serve families
				across Andhra Pradesh, Telangana, Maharashtra and other states — and wherever this vibrant
				community has settled worldwide.
				<span class="block mt-2" lang={langStore.current}>{tx('aboutMissionDesc', langStore.current)}</span>
			</p>
		</section>

		<div class="border-t border-gold/20"></div>

		<section>
			<h2 class="mb-3 font-serif text-2xl font-semibold text-maroon">
				Our Community
				<span class="block" lang={langStore.current}>{tx('aboutCommunityHeading', langStore.current)}</span>
			</h2>
			<p class="mt-1 text-ink/80">
				The Maratha community in Andhra, Telangana, Maharashtra and other states has a rich cultural
				heritage. Unique customs around gotra, kuldevata, devak, and nakshatram make community-specific
				matchmaking important. Our platform is designed from the ground up to capture and match on these
				cultural specifics.
				<span class="block mt-2" lang={langStore.current}>{tx('aboutCommunityDesc', langStore.current)}</span>
			</p>
		</section>

		<div class="border-t border-gold/20"></div>

		<section>
			<h2 class="mb-3 font-serif text-2xl font-semibold text-maroon">
				Privacy &amp; Safety
				<span class="block" lang={langStore.current}>{tx('aboutPrivacyHeading', langStore.current)}</span>
			</h2>
			<p class="mt-1 text-ink/80">
				We take privacy seriously. Profile photos are blurred in all public listings. Your contact
				details and clear passport photo are shared <em>only</em> after:
			</p>
			<ol class="mt-3 list-decimal space-y-1 pl-6 text-ink/80">
				<li>You express interest by clicking "Request Full Details"</li>
				<li>Our admin team reviews and approves the request</li>
				<li>Details are emailed directly — never displayed on-screen</li>
			</ol>
			<p class="mt-2 text-ink/80" lang={langStore.current}>
				{tx('aboutPrivacyDesc', langStore.current)}
			</p>
		</section>

		<div class="border-t border-gold/20"></div>

		<section>
			<h2 class="mb-3 font-serif text-2xl font-semibold text-maroon">
				Contact
				<span class="block" lang={langStore.current}>{tx('aboutContactHeading', langStore.current)}</span>
			</h2>
			<p class="mt-1 text-ink/80">
				For queries, please email
				<a href="mailto:admin.marathakalyanam@gmail.com" class="text-saffron hover:underline">
					admin.marathakalyanam@gmail.com
				</a>.
				<span class="block mt-2" lang={langStore.current}>{tx('aboutContactDesc', langStore.current)}</span>
			</p>
		</section>
	</div>
</div>
