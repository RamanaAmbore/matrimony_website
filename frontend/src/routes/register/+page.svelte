<script lang="ts">
	import { auth } from '$lib/api';
	import { toastStore } from '$lib/stores/toast.svelte';
	import { goto } from '$app/navigation';
	import { ApiError } from '$lib/api';
	import KalashaDivider from '$lib/components/KalashaDivider.svelte';
	import { T } from '$lib/i18n';

	let email = $state('');
	let password = $state('');
	let confirmPassword = $state('');
	let loading = $state(false);
	let errors = $state<Record<string, string>>({});

	function validate(): boolean {
		const e: Record<string, string> = {};
		if (!email.trim()) e.email = 'Email is required';
		else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) e.email = 'Enter a valid email';
		if (!password) e.password = 'Password is required';
		else if (password.length < 8) e.password = 'At least 8 characters required';
		if (password !== confirmPassword) e.confirmPassword = 'Passwords do not match';
		errors = e;
		return Object.keys(e).length === 0;
	}

	async function handleSubmit(e: Event) {
		e.preventDefault();
		if (!validate()) return;

		loading = true;
		try {
			await auth.register(email.trim(), password);
			toastStore.success('Account created! Please check your email to verify.');
			goto('/login');
		} catch (err) {
			if (err instanceof ApiError) {
				if (err.status === 409) {
					errors = { email: 'An account with this email already exists' };
				} else {
					toastStore.error(err.message.slice(0, 60));
				}
			} else {
				toastStore.error('Registration failed. Try again.');
			}
		} finally {
			loading = false;
		}
	}
</script>

<svelte:head>
	<title>Register — Marathya Kalaynam</title>
</svelte:head>

<div class="mx-auto max-w-md px-4 py-16">
	<div class="text-center">
		<h1 class="font-serif text-3xl font-bold text-maroon">
			{T.register.en}
			<span class="ml-2 text-xl font-normal text-ink/50" lang="te">{T.register.te}</span>
		</h1>
		<p class="mt-1 text-sm text-ink/60">Join the Marathya Kalaynam community</p>
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
				autocomplete="new-password"
				class="input"
				class:border-vermilion={errors.password}
				bind:value={password}
				placeholder="Min. 8 characters"
			/>
			{#if errors.password}
				<p class="mt-1 text-xs text-vermilion">{errors.password}</p>
			{/if}
		</div>

		<!-- Confirm password -->
		<div>
			<label for="confirm-password" class="label block">
				<span class="block">Confirm password</span>
				<span class="block text-xs text-ink/60 font-normal leading-tight" lang="te">పాస్‌వర్డ్ నిర్ధారించు</span>
			</label>
			<input
				id="confirm-password"
				type="password"
				autocomplete="new-password"
				class="input"
				class:border-vermilion={errors.confirmPassword}
				bind:value={confirmPassword}
				placeholder="Re-enter password"
			/>
			{#if errors.confirmPassword}
				<p class="mt-1 text-xs text-vermilion">{errors.confirmPassword}</p>
			{/if}
		</div>

		<button type="submit" class="btn-primary w-full py-3" disabled={loading}>
			{#if loading}
				Creating account…
			{:else}
				{T.register.en} · <span lang="te">{T.register.te}</span>
			{/if}
		</button>
	</form>

	<p class="mt-6 text-center text-sm text-ink/60">
		Already have an account?
		<a href="/login" class="font-medium text-saffron hover:underline">
			{T.login.en} · <span lang="te">{T.login.te}</span>
		</a>
	</p>
</div>
