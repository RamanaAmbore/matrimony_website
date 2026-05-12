<script lang="ts">
	import { auth } from '$lib/api';
	import { ApiError } from '$lib/api';
	import { toastStore } from '$lib/stores/toast.svelte';
	import { T, tx } from '$lib/i18n';
	import { langStore } from '$lib/stores/lang.svelte';
	import { Mail } from 'lucide-svelte';

	let email = $state('');
	let loading = $state(false);
	let submitted = $state(false);
	let errorMsg = $state('');

	async function handleSubmit(e: Event) {
		e.preventDefault();
		if (!email.trim()) {
			errorMsg = 'Email address is required';
			return;
		}
		errorMsg = '';
		loading = true;
		try {
			await auth.forgotPassword({ email: email.trim() });
			submitted = true;
		} catch (err) {
			// Backend always returns 200 — any error here is a network/server fault
			if (err instanceof ApiError) {
				toastStore.error(err.message.slice(0, 60));
			} else {
				toastStore.error('Request failed. Try again.');
			}
		} finally {
			loading = false;
		}
	}
</script>

<svelte:head>
	<title>Forgot Password — Maratha Kalyanam</title>
</svelte:head>

<div class="mx-auto max-w-md px-4 py-16">
	<div class="rounded-2xl bg-white shadow-xl ring-1 ring-maroon/10 px-8 py-10">
		{#if submitted}
			<!-- Success state -->
			<div class="text-center space-y-4">
				<div class="mx-auto flex h-14 w-14 items-center justify-center rounded-full bg-saffron/15">
					<Mail size={28} class="text-saffron" />
				</div>
				<h1 class="font-serif text-2xl font-bold text-maroon">Check your inbox</h1>
				<p class="text-sm text-ink/70 leading-relaxed">
					{tx('passwordResetSent', langStore.current)}
				</p>
				<p class="text-xs text-ink/50">The link expires in 1 hour. Check your spam folder if you don't see it.</p>
				<a href="/login" class="inline-block mt-2 text-sm font-medium text-saffron hover:underline">
					Back to login
				</a>
			</div>
		{:else}
			<div class="text-center mb-6">
				<h1 class="font-serif text-3xl font-bold text-maroon">
					{T.forgotPassword.en}
					<span class="ml-1 text-2xl font-normal" lang={langStore.current}>{tx('forgotPassword', langStore.current)}</span>
				</h1>
				<p class="mt-1 text-sm text-ink/60">Enter your email to receive a password reset link</p>
			</div>

			<form onsubmit={handleSubmit} novalidate class="space-y-5">
				<div>
					<label for="fp-email" class="label block">
						<span class="block">Email address</span>
						<span class="block leading-tight" lang={langStore.current}>{tx('emailAddress', langStore.current)}</span>
					</label>
					<div class="relative">
						<Mail size={16} class="absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none text-ink/40" />
						<input
							id="fp-email"
							type="email"
							autocomplete="email"
							class="input pl-10"
							class:border-vermilion={!!errorMsg}
							bind:value={email}
							placeholder="you@example.com"
						/>
					</div>
					{#if errorMsg}
						<p class="mt-1 text-xs text-vermilion">{errorMsg}</p>
					{/if}
				</div>

				<button
					type="submit"
					class="btn-primary w-full flex flex-col items-center justify-center text-center leading-tight py-2 min-h-[52px] whitespace-normal"
					disabled={loading}
				>
					<span class="text-sm">{loading ? 'Sending…' : T.resetPassword.en}</span>
					{#if !loading}
						<span lang={langStore.current} class="text-[10px] opacity-90" style="color:inherit">{tx('resetPassword', langStore.current)}</span>
					{/if}
				</button>
			</form>

			<p class="mt-6 text-center text-sm text-ink/60">
				<a href="/login" class="font-medium text-saffron hover:underline">
					← Back to login
				</a>
			</p>
		{/if}
	</div>
</div>
