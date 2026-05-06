<script lang="ts">
	import { onMount } from 'svelte';
	import { auth as authApi, ApiError } from '$lib/api';
	import { toastStore } from '$lib/stores/toast.svelte';
	import { invalidateAll, goto } from '$app/navigation';
	import { T, tx } from '$lib/i18n';
	import { langStore } from '$lib/stores/lang.svelte';
	import { User, Mail, Phone, Lock, Loader } from 'lucide-svelte';

	let { data } = $props();

	const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
	const PHONE_DIGITS_RE = /^\+\d{7,17}$/;
	const PASSWORD_LETTER_RE = /[A-Za-z]/;
	const PASSWORD_DIGIT_RE = /\d/;

	function normalizePhone(value: string): string {
		return value.replace(/[\s\-.]/g, '').trim();
	}

	// ── Email section state ──────────────────────────────────────────────────────
	let emailCurrentPw = $state('');
	let newEmail = $state('');
	let emailErrors = $state<Record<string, string>>({});
	let emailLoading = $state(false);

	function validateEmailForm(): boolean {
		const e: Record<string, string> = {};
		if (!emailCurrentPw) e.current_password = 'Current password is required';
		if (!newEmail.trim()) e.new_email = 'Email address is required';
		else if (!EMAIL_RE.test(newEmail.trim())) e.new_email = 'Enter a valid email address';
		emailErrors = e;
		return Object.keys(e).length === 0;
	}

	async function handleEmailSubmit(ev: Event) {
		ev.preventDefault();
		if (!validateEmailForm()) return;
		emailLoading = true;
		emailErrors = {};
		try {
			const res = await authApi.updateEmail(newEmail.trim(), emailCurrentPw);
			toastStore.success(`Email updated. Check ${res.email} to verify.`);
			emailCurrentPw = '';
			newEmail = '';
			await invalidateAll();
		} catch (err) {
			if (err instanceof ApiError) {
				if (err.status === 403 || err.code === 'wrong_password') {
					emailErrors = { current_password: 'Current password is incorrect' };
				} else if (err.code === 'email_taken') {
					emailErrors = { new_email: 'This email is already in use' };
				} else if (err.code === 'same_email') {
					emailErrors = { new_email: 'Must differ from your current value' };
				} else if (err.code === 'invalid_email') {
					emailErrors = { new_email: err.message };
				} else {
					toastStore.error(err.message.slice(0, 60));
				}
			} else {
				toastStore.error('Update failed. Try again.');
			}
		} finally {
			emailLoading = false;
		}
	}

	function cancelEmail() {
		emailCurrentPw = '';
		newEmail = '';
		emailErrors = {};
	}

	// ── Phone section state ──────────────────────────────────────────────────────
	let phoneCurrentPw = $state('');
	let newPhone = $state('+91 ');
	let phoneErrors = $state<Record<string, string>>({});
	let phoneLoading = $state(false);

	function validatePhoneForm(): boolean {
		const e: Record<string, string> = {};
		if (!phoneCurrentPw) e.current_password = 'Current password is required';
		if (!newPhone.trim()) e.new_phone = 'Phone number is required';
		else if (!PHONE_DIGITS_RE.test(normalizePhone(newPhone))) {
			e.new_phone = "Must start with '+', include country code (e.g. +91 9840770711)";
		}
		phoneErrors = e;
		return Object.keys(e).length === 0;
	}

	async function handlePhoneSubmit(ev: Event) {
		ev.preventDefault();
		if (!validatePhoneForm()) return;
		phoneLoading = true;
		phoneErrors = {};
		try {
			const res = await authApi.updatePhone(normalizePhone(newPhone), phoneCurrentPw);
			toastStore.success(`Phone number updated to ${res.phone_number}.`);
			phoneCurrentPw = '';
			newPhone = '+91 ';
		} catch (err) {
			if (err instanceof ApiError) {
				if (err.status === 403 || err.code === 'wrong_password') {
					phoneErrors = { current_password: 'Current password is incorrect' };
				} else if (err.code === 'phone_taken') {
					phoneErrors = { new_phone: 'This phone number is already in use' };
				} else if (err.code === 'same_phone') {
					phoneErrors = { new_phone: 'Must differ from your current value' };
				} else if (err.code === 'invalid_phone') {
					phoneErrors = { new_phone: err.message };
				} else {
					toastStore.error(err.message.slice(0, 60));
				}
			} else {
				toastStore.error('Update failed. Try again.');
			}
		} finally {
			phoneLoading = false;
		}
	}

	function cancelPhone() {
		phoneCurrentPw = '';
		newPhone = '+91 ';
		phoneErrors = {};
	}

	// ── Password section state ───────────────────────────────────────────────────
	let pwCurrent = $state('');
	let pwNew = $state('');
	let pwConfirm = $state('');
	let pwErrors = $state<Record<string, string>>({});
	let pwLoading = $state(false);

	function validatePasswordForm(): boolean {
		const e: Record<string, string> = {};
		if (!pwCurrent) e.current_password = 'Current password is required';
		if (!pwNew) e.new_password = 'New password is required';
		else if (pwNew.length < 8) e.new_password = 'At least 8 characters required';
		else if (!PASSWORD_LETTER_RE.test(pwNew)) e.new_password = 'Must contain at least one letter';
		else if (!PASSWORD_DIGIT_RE.test(pwNew)) e.new_password = 'Must contain at least one digit';
		if (pwNew && pwConfirm && pwNew !== pwConfirm) e.confirm_password = 'Passwords do not match';
		else if (!pwConfirm) e.confirm_password = 'Please confirm your new password';
		pwErrors = e;
		return Object.keys(e).length === 0;
	}

	async function handlePasswordSubmit(ev: Event) {
		ev.preventDefault();
		if (!validatePasswordForm()) return;
		pwLoading = true;
		pwErrors = {};
		try {
			await authApi.updatePassword(pwCurrent, pwNew);
			toastStore.success('Password updated. Use the new password from now on.');
			pwCurrent = '';
			pwNew = '';
			pwConfirm = '';
		} catch (err) {
			if (err instanceof ApiError) {
				if (err.status === 403 || err.code === 'wrong_password') {
					pwErrors = { current_password: 'Current password is incorrect' };
				} else if (err.code === 'same_password') {
					pwErrors = { new_password: 'Must differ from your current value' };
				} else if (err.code === 'weak_password') {
					pwErrors = { new_password: err.message };
				} else {
					toastStore.error(err.message.slice(0, 60));
				}
			} else {
				toastStore.error('Update failed. Try again.');
			}
		} finally {
			pwLoading = false;
		}
	}

	function cancelPassword() {
		pwCurrent = '';
		pwNew = '';
		pwConfirm = '';
		pwErrors = {};
	}

	// Redirect unauthenticated users — consistent with other protected pages
	onMount(() => {
		if (!data.user) {
			goto('/login');
		}
	});

	let user = $derived(data.user);
</script>

<svelte:head>
	<title>Account Settings — Maratha Kalyanam</title>
</svelte:head>

<div class="mx-auto max-w-2xl px-4 py-10 space-y-6">
	<!-- Page heading -->
	<div class="flex items-center gap-3">
		<User size={28} class="text-maroon shrink-0" />
		<div>
			<h1 class="font-serif text-3xl font-bold text-maroon">
				{T.accountSettings.en}
				<span class="ml-2" lang={langStore.current}>{tx('accountSettings', langStore.current)}</span>
			</h1>
			<p class="mt-0.5 text-sm text-ink/60">Manage your email, phone, and password</p>
		</div>
	</div>

	<!-- Post-email-change warning: shown when email_verified is false -->
	{#if user && !user.email_verified}
		<div class="flex items-start gap-3 rounded-lg border border-saffron/40 bg-saffron/10 px-5 py-4">
			<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="mt-0.5 shrink-0 text-saffron" aria-hidden="true"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
			<div class="text-sm text-ink/80">
				<p class="font-semibold text-saffron">Email verification required.</p>
				<p>Your email address is not yet verified. Please check your inbox and click the verification link. Your account will also need admin re-approval before you can create or update profiles.</p>
			</div>
		</div>
	{/if}

	<!-- ── Update Email card ─────────────────────────────────────────────────── -->
	<div class="rounded-xl border border-gold/30 bg-white p-5 shadow-sm">
		<h2 class="font-serif text-xl font-semibold text-maroon mb-3 flex items-center gap-2">
			<Mail size={18} />
			{T.updateEmail.en}
			<span class="ml-1 font-normal text-base text-ink/50" lang={langStore.current}>{tx('updateEmail', langStore.current)}</span>
		</h2>

		{#if user}
			<p class="mb-4 text-sm text-ink/60">
				Current email: <span class="font-medium text-ink">{user.email}</span>
			</p>
		{/if}

		<form onsubmit={handleEmailSubmit} novalidate class="space-y-4">
			<!-- Current password -->
			<div>
				<label for="email-current-pw" class="label block">
					<span class="block">{T.currentPassword.en}</span>
					<span class="block leading-tight text-xs text-ink/50" lang={langStore.current}>{tx('currentPassword', langStore.current)}</span>
				</label>
				<div class="relative">
					<Lock size={16} class="absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none text-ink/40" />
					<input
						id="email-current-pw"
						type="password"
						autocomplete="current-password"
						class="input pl-10"
						class:border-vermilion={emailErrors.current_password}
						bind:value={emailCurrentPw}
						placeholder="Your current password"
					/>
				</div>
				{#if emailErrors.current_password}
					<p class="text-vermilion text-xs mt-1">{emailErrors.current_password}</p>
				{/if}
			</div>

			<!-- New email -->
			<div>
				<label for="new-email" class="label block">
					<span class="block">{T.newEmail.en}</span>
					<span class="block leading-tight text-xs text-ink/50" lang={langStore.current}>{tx('newEmail', langStore.current)}</span>
				</label>
				<div class="relative">
					<Mail size={16} class="absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none text-ink/40" />
					<input
						id="new-email"
						type="email"
						autocomplete="email"
						class="input pl-10"
						class:border-vermilion={emailErrors.new_email}
						bind:value={newEmail}
						placeholder="new@example.com"
					/>
				</div>
				{#if emailErrors.new_email}
					<p class="text-vermilion text-xs mt-1">{emailErrors.new_email}</p>
				{:else}
					<p class="text-xs text-ink/50 mt-1">Changing email will require re-verification and admin re-approval.</p>
				{/if}
			</div>

			<div class="flex gap-3 pt-1">
				<button
					type="submit"
					class="btn-primary flex flex-col items-center justify-center text-center leading-tight px-4 py-2 min-h-[44px] whitespace-normal disabled:opacity-50"
					disabled={emailLoading}
				>
					{#if emailLoading}
						<Loader size={16} class="animate-spin text-saffron" />
					{:else}
						<span class="text-sm">{T.save.en}</span>
						<span lang={langStore.current} class="text-[10px] opacity-90">{tx('save', langStore.current)}</span>
					{/if}
				</button>
				<button
					type="button"
					class="btn-secondary flex flex-col items-center justify-center text-center leading-tight px-4 py-2 min-h-[44px] whitespace-normal"
					onclick={cancelEmail}
				>
					<span class="text-sm">{T.cancel.en}</span>
					<span lang={langStore.current} class="text-[10px] opacity-90">{tx('cancel', langStore.current)}</span>
				</button>
			</div>
		</form>
	</div>

	<!-- ── Update Phone card ─────────────────────────────────────────────────── -->
	<div class="rounded-xl border border-gold/30 bg-white p-5 shadow-sm">
		<h2 class="font-serif text-xl font-semibold text-maroon mb-3 flex items-center gap-2">
			<Phone size={18} />
			{T.updatePhone.en}
			<span class="ml-1 font-normal text-base text-ink/50" lang={langStore.current}>{tx('updatePhone', langStore.current)}</span>
		</h2>

		{#if user}
			<p class="mb-4 text-sm text-ink/60">
				Current phone: <span class="font-medium text-ink">{user.phone_number}</span>
			</p>
		{/if}

		<form onsubmit={handlePhoneSubmit} novalidate class="space-y-4">
			<!-- Current password -->
			<div>
				<label for="phone-current-pw" class="label block">
					<span class="block">{T.currentPassword.en}</span>
					<span class="block leading-tight text-xs text-ink/50" lang={langStore.current}>{tx('currentPassword', langStore.current)}</span>
				</label>
				<div class="relative">
					<Lock size={16} class="absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none text-ink/40" />
					<input
						id="phone-current-pw"
						type="password"
						autocomplete="current-password"
						class="input pl-10"
						class:border-vermilion={phoneErrors.current_password}
						bind:value={phoneCurrentPw}
						placeholder="Your current password"
					/>
				</div>
				{#if phoneErrors.current_password}
					<p class="text-vermilion text-xs mt-1">{phoneErrors.current_password}</p>
				{/if}
			</div>

			<!-- New phone -->
			<div>
				<label for="new-phone" class="label block">
					<span class="block">{T.newPhone.en}</span>
					<span class="block leading-tight text-xs text-ink/50" lang={langStore.current}>{tx('newPhone', langStore.current)}</span>
				</label>
				<div class="relative">
					<Phone size={16} class="absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none text-ink/40" />
					<input
						id="new-phone"
						type="tel"
						autocomplete="tel"
						inputmode="tel"
						class="input pl-10"
						class:border-vermilion={phoneErrors.new_phone}
						bind:value={newPhone}
						placeholder="+91 9840770711"
						spellcheck="false"
					/>
				</div>
				{#if phoneErrors.new_phone}
					<p class="text-vermilion text-xs mt-1">{phoneErrors.new_phone}</p>
				{:else}
					<p class="text-xs text-ink/50 mt-1">
						Include country code, e.g. <span class="font-mono">+91 9840770711</span>
					</p>
				{/if}
			</div>

			<div class="flex gap-3 pt-1">
				<button
					type="submit"
					class="btn-primary flex flex-col items-center justify-center text-center leading-tight px-4 py-2 min-h-[44px] whitespace-normal disabled:opacity-50"
					disabled={phoneLoading}
				>
					{#if phoneLoading}
						<Loader size={16} class="animate-spin text-saffron" />
					{:else}
						<span class="text-sm">{T.save.en}</span>
						<span lang={langStore.current} class="text-[10px] opacity-90">{tx('save', langStore.current)}</span>
					{/if}
				</button>
				<button
					type="button"
					class="btn-secondary flex flex-col items-center justify-center text-center leading-tight px-4 py-2 min-h-[44px] whitespace-normal"
					onclick={cancelPhone}
				>
					<span class="text-sm">{T.cancel.en}</span>
					<span lang={langStore.current} class="text-[10px] opacity-90">{tx('cancel', langStore.current)}</span>
				</button>
			</div>
		</form>
	</div>

	<!-- ── Update Password card ──────────────────────────────────────────────── -->
	<div class="rounded-xl border border-gold/30 bg-white p-5 shadow-sm">
		<h2 class="font-serif text-xl font-semibold text-maroon mb-3 flex items-center gap-2">
			<Lock size={18} />
			{T.updatePassword.en}
			<span class="ml-1 font-normal text-base text-ink/50" lang={langStore.current}>{tx('updatePassword', langStore.current)}</span>
		</h2>

		<form onsubmit={handlePasswordSubmit} novalidate class="space-y-4">
			<!-- Current password -->
			<div>
				<label for="pw-current" class="label block">
					<span class="block">{T.currentPassword.en}</span>
					<span class="block leading-tight text-xs text-ink/50" lang={langStore.current}>{tx('currentPassword', langStore.current)}</span>
				</label>
				<div class="relative">
					<Lock size={16} class="absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none text-ink/40" />
					<input
						id="pw-current"
						type="password"
						autocomplete="current-password"
						class="input pl-10"
						class:border-vermilion={pwErrors.current_password}
						bind:value={pwCurrent}
						placeholder="Your current password"
					/>
				</div>
				{#if pwErrors.current_password}
					<p class="text-vermilion text-xs mt-1">{pwErrors.current_password}</p>
				{/if}
			</div>

			<!-- New password -->
			<div>
				<label for="pw-new" class="label block">
					<span class="block">{T.newPassword.en}</span>
					<span class="block leading-tight text-xs text-ink/50" lang={langStore.current}>{tx('newPassword', langStore.current)}</span>
				</label>
				<div class="relative">
					<Lock size={16} class="absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none text-ink/40" />
					<input
						id="pw-new"
						type="password"
						autocomplete="new-password"
						class="input pl-10"
						class:border-vermilion={pwErrors.new_password}
						bind:value={pwNew}
						placeholder="Min. 8 chars · letter + digit"
					/>
				</div>
				{#if pwErrors.new_password}
					<p class="text-vermilion text-xs mt-1">{pwErrors.new_password}</p>
				{:else}
					<p class="text-xs text-ink/50 mt-1">At least 8 characters · must contain a letter and a digit</p>
				{/if}
			</div>

			<!-- Confirm new password -->
			<div>
				<label for="pw-confirm" class="label block">
					<span class="block">{T.confirmNewPassword.en}</span>
					<span class="block leading-tight text-xs text-ink/50" lang={langStore.current}>{tx('confirmNewPassword', langStore.current)}</span>
				</label>
				<div class="relative">
					<Lock size={16} class="absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none text-ink/40" />
					<input
						id="pw-confirm"
						type="password"
						autocomplete="new-password"
						class="input pl-10"
						class:border-vermilion={pwErrors.confirm_password}
						bind:value={pwConfirm}
						placeholder="Re-enter new password"
					/>
				</div>
				{#if pwErrors.confirm_password}
					<p class="text-vermilion text-xs mt-1">{pwErrors.confirm_password}</p>
				{/if}
			</div>

			<div class="flex gap-3 pt-1">
				<button
					type="submit"
					class="btn-primary flex flex-col items-center justify-center text-center leading-tight px-4 py-2 min-h-[44px] whitespace-normal disabled:opacity-50"
					disabled={pwLoading}
				>
					{#if pwLoading}
						<Loader size={16} class="animate-spin text-saffron" />
					{:else}
						<span class="text-sm">{T.save.en}</span>
						<span lang={langStore.current} class="text-[10px] opacity-90">{tx('save', langStore.current)}</span>
					{/if}
				</button>
				<button
					type="button"
					class="btn-secondary flex flex-col items-center justify-center text-center leading-tight px-4 py-2 min-h-[44px] whitespace-normal"
					onclick={cancelPassword}
				>
					<span class="text-sm">{T.cancel.en}</span>
					<span lang={langStore.current} class="text-[10px] opacity-90">{tx('cancel', langStore.current)}</span>
				</button>
			</div>
		</form>
	</div>
</div>
