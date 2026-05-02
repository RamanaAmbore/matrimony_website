<script lang="ts">
	import { page } from '$app/stores';
	import { auth } from '$lib/api';
	import { ApiError } from '$lib/api';
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { CheckCircle, XCircle, Loader } from 'lucide-svelte';

	type Step = 'loading' | 'success' | 'error';
	let step = $state<Step>('loading');
	let errorMessage = $state('');

	onMount(async () => {
		const token = $page.url.searchParams.get('token');
		if (!token) {
			step = 'error';
			errorMessage = 'No verification token found in the URL.';
			return;
		}
		try {
			await auth.verifyEmail(token);
			step = 'success';
			setTimeout(() => goto('/login'), 3000);
		} catch (err) {
			step = 'error';
			if (err instanceof ApiError) {
				errorMessage = err.message;
			} else {
				errorMessage = 'Verification failed. The link may have expired.';
			}
		}
	});
</script>

<svelte:head>
	<title>Verify Email — Maratha Kalyanam</title>
</svelte:head>

<div class="flex min-h-[60vh] flex-col items-center justify-center px-4 py-16">
	{#if step === 'loading'}
		<Loader size={48} class="animate-spin text-saffron" />
		<p class="mt-4 text-ink/60">Verifying your email…</p>
	{:else if step === 'success'}
		<CheckCircle size={56} class="text-green-600" />
		<h1 class="mt-4 font-serif text-2xl font-semibold text-maroon">Email Verified!</h1>
		<p class="mt-2 text-ink/60">Your email has been verified. Redirecting to login…</p>
		<a href="/login" class="btn-primary mt-6">Go to Login</a>
	{:else}
		<XCircle size={56} class="text-vermilion" />
		<h1 class="mt-4 font-serif text-2xl font-semibold text-maroon">Verification Failed</h1>
		<p class="mt-2 max-w-sm text-center text-ink/60">{errorMessage}</p>
		<a href="/register" class="btn-secondary mt-6">Back to Register</a>
	{/if}
</div>
