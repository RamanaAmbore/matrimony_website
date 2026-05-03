<script lang="ts">
	import { auth } from '$lib/api';
	import { toastStore } from '$lib/stores/toast.svelte';
	import { goto } from '$app/navigation';
	import { ApiError } from '$lib/api';
	import { T } from '$lib/i18n';
	import { asciiOnly } from '$lib/inputFilters';

	const HANDLE_RE = /^[A-Za-z][A-Za-z0-9_]{2,29}$/;
	const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
	const PHONE_DIGITS_RE = /^\+\d{7,17}$/;
	const PASSWORD_LETTER_RE = /[A-Za-z]/;
	const PASSWORD_DIGIT_RE = /\d/;

	let user_handle = $state('');
	let email = $state('');
	let phone_number = $state('+');
	let password = $state('');
	let confirmPassword = $state('');
	let loading = $state(false);
	let errors = $state<Record<string, string>>({});

	function validateHandle(value: string): string {
		if (!value.trim()) return 'User ID is required';
		if (!HANDLE_RE.test(value)) {
			if (value.length < 3) return 'Must be at least 3 characters';
			if (value.length > 30) return 'Must be 30 characters or fewer';
			if (!/^[A-Za-z]/.test(value)) return 'Must start with a letter';
			return 'Only letters, digits and underscore allowed';
		}
		return '';
	}

	function normalizePhone(value: string): string {
		return value.replace(/[\s\-.]/g, '').trim();
	}

	function validatePhone(value: string): string {
		if (!value.trim()) return 'Phone number is required';
		if (!PHONE_DIGITS_RE.test(normalizePhone(value))) {
			return "Must start with '+', include country code (e.g. +91 9840770711)";
		}
		return '';
	}

	function validatePassword(value: string): string {
		if (!value) return 'Password is required';
		if (value.length < 8) return 'At least 8 characters required';
		if (!PASSWORD_LETTER_RE.test(value)) return 'Must contain at least one letter';
		if (!PASSWORD_DIGIT_RE.test(value)) return 'Must contain at least one digit';
		return '';
	}

	function handleBlur() {
		const msg = validateHandle(user_handle);
		if (msg) {
			errors = { ...errors, user_handle: msg };
		} else {
			const { user_handle: _, ...rest } = errors;
			errors = rest;
		}
	}

	function validate(): boolean {
		const e: Record<string, string> = {};
		const handleMsg = validateHandle(user_handle);
		if (handleMsg) e.user_handle = handleMsg;
		if (!email.trim()) e.email = 'Email is required';
		else if (!EMAIL_RE.test(email)) e.email = 'Enter a valid email';
		const phoneMsg = validatePhone(phone_number);
		if (phoneMsg) e.phone_number = phoneMsg;
		const pwMsg = validatePassword(password);
		if (pwMsg) e.password = pwMsg;
		if (password !== confirmPassword) e.confirmPassword = 'Passwords do not match';
		errors = e;
		return Object.keys(e).length === 0;
	}

	async function handleSubmit(e: Event) {
		e.preventDefault();
		if (!validate()) return;

		loading = true;
		try {
			await auth.register(
				email.trim(),
				password,
				user_handle.trim(),
				phone_number.trim()
			);
			toastStore.success('Account created! Please check your email to verify.');
			goto('/login');
		} catch (err) {
			if (err instanceof ApiError) {
				if (err.status === 409) {
					if (err.code === 'handle_taken') {
						errors = { user_handle: 'This user ID is already taken — pick another' };
					} else if (err.code === 'phone_taken') {
						errors = { phone_number: 'This phone number is already registered' };
					} else {
						// email_taken or generic 409
						errors = { email: 'An account with this email already exists — login or use a different email' };
					}
				} else if (err.status === 422) {
					if (err.code === 'invalid_email') errors = { email: err.message };
					else if (err.code === 'invalid_phone') errors = { phone_number: err.message };
					else if (err.code === 'weak_password') errors = { password: err.message };
					else if (err.code === 'invalid_handle') errors = { user_handle: err.message };
					else toastStore.error(err.message.slice(0, 80));
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
	<title>Register — Maratha Kalyanam</title>
</svelte:head>

<div class="mx-auto max-w-md px-4 py-16">
	<div class="rounded-2xl bg-white shadow-xl ring-1 ring-maroon/10 px-8 py-10">
	<div class="text-center">
		<h1 class="font-serif text-3xl font-bold text-maroon">
			{T.register.en}
			<span class="ml-2 text-xl font-normal" lang="te">{T.register.te}</span>
		</h1>
		<p class="mt-1 text-sm text-ink/60">Join the Maratha Kalyanam community</p>
	</div>


	<form onsubmit={handleSubmit} novalidate class="mt-6 space-y-5">
		<!-- User ID / handle -->
		<div>
			<label for="user_handle" class="label block">
				<span class="block">{T.userHandle.en}</span>
				<span class="block text-xs font-normal leading-tight" lang="te">{T.userHandle.te}</span>
			</label>
			<input
				id="user_handle"
				type="text"
				autocomplete="username"
				class="input font-mono"
				class:border-vermilion={errors.user_handle}
				bind:value={user_handle}
				oninput={(ev) => { user_handle = asciiOnly((ev.currentTarget as HTMLInputElement).value); }}
				onblur={handleBlur}
				placeholder="ramana_ambore"
				maxlength="30"
				spellcheck="false"
			/>
			{#if errors.user_handle}
				<p class="mt-1 text-xs text-vermilion">{errors.user_handle}</p>
			{:else}
				<p class="mt-1 text-xs text-ink/50 leading-snug">
					3–30 characters · letters, digits, underscore · must start with a letter<br />
					<span lang="te">3–30 అక్షరాలు · అక్షరాలు, అంకెలు, అండర్‌స్కోర్ · అక్షరంతో ప్రారంభం</span>
				</p>
			{/if}
		</div>

		<!-- Email -->
		<div>
			<label for="email" class="label block">
				<span class="block">Email address</span>
				<span class="block text-xs font-normal leading-tight" lang="te">ఇమెయిల్ చిరునామా</span>
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

		<!-- Phone number -->
		<div>
			<label for="phone_number" class="label block">
				<span class="block">Phone number</span>
				<span class="block text-xs font-normal leading-tight" lang="te">ఫోన్ నంబర్</span>
			</label>
			<input
				id="phone_number"
				type="tel"
				autocomplete="tel"
				inputmode="tel"
				class="input"
				class:border-vermilion={errors.phone_number}
				bind:value={phone_number}
				placeholder="+91 9840770711  or  +1 2125551234"
				spellcheck="false"
			/>
			{#if errors.phone_number}
				<p class="mt-1 text-xs text-vermilion">{errors.phone_number}</p>
			{:else}
				<p class="mt-1 text-xs text-ink/50 leading-snug">
					Include country code, e.g. <span class="font-mono">+91 9840770711</span> or <span class="font-mono">+1 2125551234</span>
				</p>
			{/if}
		</div>

		<!-- Password -->
		<div>
			<label for="password" class="label block">
				<span class="block">Password</span>
				<span class="block text-xs font-normal leading-tight" lang="te">పాస్‌వర్డ్</span>
			</label>
			<input
				id="password"
				type="password"
				autocomplete="new-password"
				class="input"
				class:border-vermilion={errors.password}
				bind:value={password}
				placeholder="Min. 8 chars · letter + digit"
			/>
			{#if errors.password}
				<p class="mt-1 text-xs text-vermilion">{errors.password}</p>
			{:else}
				<p class="mt-1 text-xs text-ink/50 leading-snug">
					At least 8 characters · must contain a letter and a digit
				</p>
			{/if}
		</div>

		<!-- Confirm password -->
		<div>
			<label for="confirm-password" class="label block">
				<span class="block">Confirm password</span>
				<span class="block text-xs font-normal leading-tight" lang="te">పాస్‌వర్డ్ నిర్ధారించు</span>
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
</div>
