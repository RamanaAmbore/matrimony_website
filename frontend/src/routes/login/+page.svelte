<script lang="ts">
	import { auth } from '$lib/api';
	import { toastStore } from '$lib/stores/toast.svelte';
	import { goto } from '$app/navigation';
	import { ApiError } from '$lib/api';
	import KalashaDivider from '$lib/components/KalashaDivider.svelte';
	import { invalidateAll } from '$app/navigation';
	import { T } from '$lib/i18n';
	import { asciiOnly } from '$lib/inputFilters';

	let email = $state('');
	let password = $state('');
	let loading = $state(false);
	let errors = $state<Record<string, string>>({});

	function validate(): boolean {
		const e: Record<string, string> = {};
		if (!email.trim()) e.email = 'Email is required';
		if (!password) e.password = 'Password is required';
		errors = e;
		return Object.keys(e).length === 0;
	}

	async function handleSubmit(e: Event) {
		e.preventDefault();
		if (!validate()) return;

		loading = true;
		try {
			await auth.login(email.trim(), password);
			await invalidateAll();
			toastStore.success('Welcome back!');
			goto('/dashboard');
		} catch (err) {
			if (err instanceof ApiError) {
				if (err.status === 401) {
					errors = { password: 'Invalid email or password' };
				} else if (err.status === 403) {
					toastStore.error('Please verify your email first');
				} else {
					toastStore.error(err.message.slice(0, 60));
				}
			} else {
				toastStore.error('Login failed. Try again.');
			}
		} finally {
			loading = false;
		}
	}
</script>

<svelte:head>
	<title>Login — Telugu–Maratha Kalyana Vedika</title>
</svelte:head>

<div class="mx-auto max-w-md px-4 py-16">
	<div class="text-center">
		<h1 class="font-serif text-3xl font-bold text-maroon">
			{T.login.en}
			<span class="ml-2 text-xl font-normal text-ink/50" lang="te">{T.login.te}</span>
		</h1>
		<p class="mt-1 text-sm text-ink/60">Sign in to your Telugu–Maratha Kalyana Vedika account</p>
	</div>

	<KalashaDivider />

	<form onsubmit={handleSubmit} novalidate class="mt-6 space-y-5">
		<!-- Email -->
		<div>
			<label for="email" class="label block">
				<span class="block">Email address</span>
				<span class="block text-xs text-ink/60 font-normal leading-tight" lang="te">ఇమెయిల్ చిరునామా</span>
			</label>
			<input
				id="email"
				type="email"
				autocomplete="email"
				class="input"
				class:border-vermilion={errors.email}
				bind:value={email}
				placeholder="you@example.com"
			/>
			{#if errors.email}
				<p class="mt-1 text-xs text-vermilion">{errors.email}</p>
			{/if}
		</div>

		<!-- Password -->
		<div>
			<label for="password" class="label block">
				<span class="block">Password</span>
				<span class="block text-xs text-ink/60 font-normal leading-tight" lang="te">పాస్‌వర్డ్</span>
			</label>
			<input
				id="password"
				type="password"
				autocomplete="current-password"
				class="input"
				class:border-vermilion={errors.password}
				bind:value={password}
			/>
			{#if errors.password}
				<p class="mt-1 text-xs text-vermilion">{errors.password}</p>
			{/if}
		</div>

		<button type="submit" class="btn-primary w-full py-3" disabled={loading}>
			{loading ? 'Signing in…' : `${T.login.en} · `}<span lang="te">{loading ? '' : T.login.te}</span>
		</button>
	</form>

	<p class="mt-6 text-center text-sm text-ink/60">
		Don't have an account?
		<a href="/register" class="font-medium text-saffron hover:underline">
			{T.register.en} · <span lang="te">{T.register.te}</span>
		</a>
	</p>
</div>
