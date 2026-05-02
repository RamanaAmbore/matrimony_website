<script lang="ts">
	import KalashaDivider from '$lib/components/KalashaDivider.svelte';
</script>

<svelte:head>
	<title>About — Maratha Kalyanam</title>
</svelte:head>

<div class="mx-auto max-w-3xl px-4 py-16">
	<h1 class="mb-2 font-serif text-4xl font-bold text-maroon">About Us</h1>
	<p class="mb-8 text-ink/60"><span lang="te">మరాఠా కల్యాణం</span> — Our Story</p>

	<KalashaDivider />

	<div class="prose-ink prose mt-8 max-w-none">
		<h2 class="font-serif text-2xl font-semibold text-maroon">Our Mission</h2>
		<p class="mt-3 text-ink/80">
			Maratha Kalyanam was founded with a simple purpose: to help Telugu-Maratha families find
			compatible life partners who share their cultural heritage, values, and traditions. We serve
			families across Andhra Pradesh, Telangana, and Maharashtra — and wherever this vibrant
			community has settled worldwide.
		</p>

		<h2 class="mt-8 font-serif text-2xl font-semibold text-maroon">Our Community</h2>
		<p class="mt-3 text-ink/80">
			The Telugu-Maratha community has a rich heritage blending the traditions of both Telangana /
			Andhra Pradesh and Maharashtra. Unique customs around gotra, kuldevata, devak, and nakshatram
			make community-specific matchmaking important. Our platform is designed from the ground up to
			capture and match on these cultural specifics.
		</p>

		<h2 class="mt-8 font-serif text-2xl font-semibold text-maroon">Privacy &amp; Safety</h2>
		<p class="mt-3 text-ink/80">
			We take privacy seriously. Profile photos are blurred in all public listings. Your contact
			details and clear passport photo are shared <em>only</em> after:
		</p>
		<ol class="mt-3 list-decimal space-y-1 pl-6 text-ink/80">
			<li>You express interest by clicking "Request Full Details"</li>
			<li>Our admin team reviews and approves the request</li>
			<li>Details are emailed directly — never displayed on-screen</li>
		</ol>

		<h2 class="mt-8 font-serif text-2xl font-semibold text-maroon">Contact</h2>
		<p class="mt-3 text-ink/80">
			For queries, please email
			<a href="mailto:admin@marathakalyanam.com" class="text-saffron hover:underline">
				admin@marathakalyanam.com
			</a>.
		</p>
	</div>

	<KalashaDivider class="mt-12" />
</div>
