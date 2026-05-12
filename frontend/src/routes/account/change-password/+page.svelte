<script lang="ts">
	import { auth as authApi, ApiError } from '$lib/api';
	import { toastStore } from '$lib/stores/toast.svelte';
	import { goto, invalidateAll } from '$app/navigation';
	import { onMount } from 'svelte';
	import { T, tx } from '$lib/i18n';
	import { langStore } from '$lib/stores/lang.svelte';
	import { Lock, ShieldAlert } from 'lucide-svelte';
	import PasswordInput from '$lib/components/PasswordInput.svelte';

	const PASSWORD_LETTER_RE = /[A-Za-z]/;
	const PASSWORD_DIGIT_RE = /\d/;

	let { data } = $props();

	let user = $derived(data.user);
	let isForced = $derived(!!(user?.must_change_password));

	let current = $state('');
	let newPw = $state('');
	let confirm = $state('');
	let loading = $state(false);
	let errors = $state<Record<string, string>>({});

	onMount(() => {
		if (!data.user) goto('/login');
	});

	function validate(): boolean {
		const e: Record<string, string> = {};
		if (!current) e.current = 'Current password is required';
		if (!newPw) {
			e.new_pw = 'New password is required';
		} else if (newPw.length < 8) {
			e.new_pw = 'At least 8 characters required';
		} else if (!PASSWORD_LETTER_RE.test(newPw)) {
			e.new_pw = 'Must contain at least one letter';
		} else if (!PASSWORD_DIGIT_RE.test(newPw)) {
			e.new_pw = 'Must contain at least one digit';
		}
		if (newPw && confirm && newPw !== confirm) {
			e.confirm = tx('passwordsMustMatch', langStore.current);
		} else if (!confirm) {
			e.confirm = 'Please confirm your new password';
		}
		errors = e;
		return Object.keys(e).length === 0;
	}

	async function handleSubmit(ev: Event) {
		ev.preventDefault();
		if (!validate()) return;
		loading = true;
		errors = {};
		try {
			await authApi.updatePassword(current, newPw);
			toastStore.success('Password updated successfully.');
			await invalidateAll();
			goto('/dashboard');
		} catch (err) {
			if (err instanceof ApiError) {
				if (err.code === 'wrong_password') {
					errors = { current: 'Current password is incorrect' };
				} else if (err.code === 'same_password') {
					errors = { new_pw: 'New password must differ from the current one' };
				} else if (err.code === 'weak_password') {
					errors = { new_pw: err.message };
				} else {
					toastStore.error(err.message.slice(0, 60));
				}
			} else {
				toastStore.error('Update failed. Try again.');
			}
		} finally {
			loading = false;
		}
	}
</script>

<svelte:head>
	<title>Change Password — Maratha Kalyanam</title>
</svelte:head>

<div class="mx-auto max-w-md px-4 py-10 space-y-6">
	{#if isForced}
		<!-- Sticky banner explaining why they're here -->
		<div class="flex items-start gap-3 rounded-lg border-2 border-amber-500 bg-amber-50 px-5 py-4">
			<ShieldAlert size={18} class="mt-0.5 shrink-0 text-amber-700" />
			<p class="text-sm font-semibold text-amber-700">
				{tx('mustChangePassword', langStore.current)}
			</p>
		</div>
	{/if}

	<div class="rounded-xl border border-gold/30 bg-white p-6 shadow-sm">
		<h1 class="font-serif text-2xl font-bold text-maroon mb-5 flex items-center gap-2">
			<Lock size={22} />
			{T.changePassword.en}
			<span class="ml-1 font-normal text-lg text-ink/50" lang={langStore.current}>{tx('changePassword', langStore.current)}</span>
		</h1>

		<form onsubmit={handleSubmit} novalidate class="space-y-4">
			<div>
				<label for="cp-current" class="label block">
					<span class="block">{T.currentPassword.en}</span>
					<span class="block leading-tight text-xs text-ink/50" lang={langStore.current}>{tx('currentPassword', langStore.current)}</span>
				</label>
				<PasswordInput
					id="cp-current"
					name="cp-current"
					autocomplete="current-password"
					placeholder="Your current password"
					bind:value={current}
					hasError={!!errors.current}
				/>
				{#if errors.current}
					<p class="mt-1 text-xs text-vermilion">{errors.current}</p>
				{/if}
			</div>

			<div>
				<label for="cp-new" class="label block">
					<span class="block">{T.newPassword.en}</span>
					<span class="block leading-tight text-xs text-ink/50" lang={langStore.current}>{tx('newPassword', langStore.current)}</span>
				</label>
				<PasswordInput
					id="cp-new"
					name="cp-new"
					autocomplete="new-password"
					placeholder="Min. 8 chars · letter + digit"
					bind:value={newPw}
					hasError={!!errors.new_pw}
				/>
				{#if errors.new_pw}
					<p class="mt-1 text-xs text-vermilion">{errors.new_pw}</p>
				{:else}
					<p class="mt-1 text-xs text-ink/50">At least 8 characters · must contain a letter and a digit</p>
				{/if}
			</div>

			<div>
				<label for="cp-confirm" class="label block">
					<span class="block">{T.confirmNewPassword.en}</span>
					<span class="block leading-tight text-xs text-ink/50" lang={langStore.current}>{tx('confirmNewPassword', langStore.current)}</span>
				</label>
				<PasswordInput
					id="cp-confirm"
					name="cp-confirm"
					autocomplete="new-password"
					placeholder="Re-enter new password"
					bind:value={confirm}
					hasError={!!errors.confirm}
				/>
				{#if errors.confirm}
					<p class="mt-1 text-xs text-vermilion">{errors.confirm}</p>
				{/if}
			</div>

			<div class="flex gap-3 pt-2">
				<button
					type="submit"
					class="btn-primary flex flex-col items-center justify-center text-center leading-tight px-4 py-2 min-h-[44px] whitespace-normal disabled:opacity-50"
					disabled={loading}
				>
					<span class="text-sm">{loading ? 'Updating…' : T.save.en}</span>
					{#if !loading}
						<span lang={langStore.current} class="text-[10px] opacity-90">{tx('save', langStore.current)}</span>
					{/if}
				</button>
				{#if !isForced}
					<a
						href="/account"
						class="btn-secondary flex items-center justify-center px-4 py-2 min-h-[44px] text-sm"
					>
						{T.cancel.en}
					</a>
				{/if}
			</div>
		</form>
	</div>
</div>
