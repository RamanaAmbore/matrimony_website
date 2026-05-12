<script lang="ts">
	import { auth } from '$lib/api';
	import { ApiError } from '$lib/api';
	import { toastStore } from '$lib/stores/toast.svelte';
	import { goto } from '$app/navigation';
	import { T, tx } from '$lib/i18n';
	import { langStore } from '$lib/stores/lang.svelte';
	import PasswordInput from '$lib/components/PasswordInput.svelte';

	const PASSWORD_LETTER_RE = /[A-Za-z]/;
	const PASSWORD_DIGIT_RE = /\d/;

	let { data } = $props();

	let newPassword = $state('');
	let confirmPassword = $state('');
	let loading = $state(false);
	let errors = $state<Record<string, string>>({});
	let tokenError = $state('');

	function validate(): boolean {
		const e: Record<string, string> = {};
		if (!newPassword) {
			e.new_password = 'New password is required';
		} else if (newPassword.length < 8) {
			e.new_password = 'At least 8 characters required';
		} else if (!PASSWORD_LETTER_RE.test(newPassword)) {
			e.new_password = 'Must contain at least one letter';
		} else if (!PASSWORD_DIGIT_RE.test(newPassword)) {
			e.new_password = 'Must contain at least one digit';
		}
		if (newPassword && confirmPassword && newPassword !== confirmPassword) {
			e.confirm_password = tx('passwordsMustMatch', langStore.current);
		} else if (!confirmPassword) {
			e.confirm_password = 'Please confirm your new password';
		}
		errors = e;
		return Object.keys(e).length === 0;
	}

	async function handleSubmit(e: Event) {
		e.preventDefault();
		if (!validate()) return;
		tokenError = '';
		loading = true;
		try {
			await auth.resetPassword({ token: data.token, new_password: newPassword });
			toastStore.success('Password updated. Please log in with your new password.');
			goto('/login');
		} catch (err) {
			if (err instanceof ApiError) {
				if (err.code === 'invalid_or_expired_token') {
					tokenError = tx('invalidOrExpiredToken', langStore.current);
				} else if (err.code === 'weak_password') {
					errors = { new_password: err.message };
				} else {
					toastStore.error(err.message.slice(0, 60));
				}
			} else {
				toastStore.error('Reset failed. Try again.');
			}
		} finally {
			loading = false;
		}
	}
</script>

<svelte:head>
	<title>Reset Password — Maratha Kalyanam</title>
</svelte:head>

<div class="mx-auto max-w-md px-4 py-16">
	<div class="rounded-2xl bg-white shadow-xl ring-1 ring-maroon/10 px-8 py-10">
		<div class="text-center mb-6">
			<h1 class="font-serif text-3xl font-bold text-maroon">
				{T.resetPassword.en}
				<span class="ml-1 text-2xl font-normal" lang={langStore.current}>{tx('resetPassword', langStore.current)}</span>
			</h1>
			<p class="mt-1 text-sm text-ink/60">Enter your new password below</p>
		</div>

		{#if tokenError}
			<div class="mb-5 rounded-lg border border-vermilion/40 bg-vermilion/5 px-4 py-3 text-sm text-vermilion">
				<p class="font-semibold">{tokenError}</p>
				<p class="mt-1">
					<a href="/forgot-password" class="font-medium underline hover:text-vermilion/80">
						{tx('requestNewLink', langStore.current)}
					</a>
				</p>
			</div>
		{/if}

		<form onsubmit={handleSubmit} novalidate class="space-y-5">
			<div>
				<label for="rp-new" class="label block">
					<span class="block">{T.newPassword.en}</span>
					<span class="block leading-tight" lang={langStore.current}>{tx('newPassword', langStore.current)}</span>
				</label>
				<PasswordInput
					id="rp-new"
					name="rp-new"
					autocomplete="new-password"
					placeholder="Min. 8 chars · letter + digit"
					bind:value={newPassword}
					hasError={!!errors.new_password}
				/>
				{#if errors.new_password}
					<p class="mt-1 text-xs text-vermilion">{errors.new_password}</p>
				{:else}
					<p class="mt-1 text-xs text-ink/50">At least 8 characters · must contain a letter and a digit</p>
				{/if}
			</div>

			<div>
				<label for="rp-confirm" class="label block">
					<span class="block">{T.confirmPassword.en}</span>
					<span class="block leading-tight" lang={langStore.current}>{tx('confirmPassword', langStore.current)}</span>
				</label>
				<PasswordInput
					id="rp-confirm"
					name="rp-confirm"
					autocomplete="new-password"
					placeholder="Re-enter new password"
					bind:value={confirmPassword}
					hasError={!!errors.confirm_password}
				/>
				{#if errors.confirm_password}
					<p class="mt-1 text-xs text-vermilion">{errors.confirm_password}</p>
				{/if}
			</div>

			<button
				type="submit"
				class="btn-primary w-full flex flex-col items-center justify-center text-center leading-tight py-2 min-h-[52px] whitespace-normal"
				disabled={loading}
			>
				<span class="text-sm">{loading ? 'Updating…' : T.resetPassword.en}</span>
				{#if !loading}
					<span lang={langStore.current} class="text-[10px] opacity-90" style="color:inherit">{tx('resetPassword', langStore.current)}</span>
				{/if}
			</button>
		</form>

		<p class="mt-6 text-center text-sm text-ink/60">
			<a href="/forgot-password" class="font-medium text-saffron hover:underline">
				{tx('requestNewLink', langStore.current)}
			</a>
		</p>
	</div>
</div>
