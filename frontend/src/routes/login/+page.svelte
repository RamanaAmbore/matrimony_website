<script lang="ts">
	import { auth } from '$lib/api';
	import { toastStore } from '$lib/stores/toast.svelte';
	import { goto } from '$app/navigation';
	import { ApiError } from '$lib/api';
	import { invalidateAll } from '$app/navigation';
	import { T, tx } from '$lib/i18n';
	import { langStore } from '$lib/stores/lang.svelte';
	import { asciiOnly } from '$lib/inputFilters';
	import { Mail, Lock } from 'lucide-svelte';

	let identifier = $state('');
	let password = $state('');
	let loading = $state(false);
	let errors = $state<Record<string, string>>({});

	function validate(): boolean {
		const e: Record<string, string> = {};
		if (!identifier.trim()) e.identifier = 'User ID or email is required';
		if (!password) e.password = 'Password is required';
		errors = e;
		return Object.keys(e).length === 0;
	}

	async function handleSubmit(e: Event) {
		e.preventDefault();
		if (!validate()) return;

		loading = true;
		try {
			const me = await auth.login(identifier.trim(), password);
			await invalidateAll();
			toastStore.success('Welcome back!');
			// Admins (incl. super) land on the dashboard; everyone else on /dashboard (their profiles).
			goto(me.is_admin ? '/admin' : '/dashboard');
		} catch (err) {
			if (err instanceof ApiError) {
				if (err.status === 401) {
					errors = { password: 'Invalid user ID / email or password' };
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
	<title>Login — Maratha Kalyanam</title>
</svelte:head>

<div class="mx-auto max-w-md px-4 py-16">
	<div class="rounded-2xl bg-white shadow-xl ring-1 ring-maroon/10 px-8 py-10">
		<div class="text-center">
			<h1 class="font-serif text-3xl font-bold text-maroon">
				{T.login.en}
				<span class="ml-2" lang={langStore.current}>{tx('login', langStore.current)}</span>
			</h1>
			<p class="mt-1 text-sm text-ink/60">Sign in to your Maratha Kalyanam account</p>
		</div>


		<form onsubmit={handleSubmit} novalidate class="mt-6 space-y-5">
			<!-- User ID or Email -->
			<div>
				<label for="identifier" class="label block">
					<span class="block">{T.identifier.en}</span>
					<span class="block leading-tight" lang={langStore.current}>{tx('identifier', langStore.current)}</span>
				</label>
				<div class="relative">
					<Mail size={16} class="absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none text-ink/40" />
					<input
						id="identifier"
						type="text"
						autocomplete="username"
						class="input pl-10"
						class:border-vermilion={errors.identifier}
						bind:value={identifier}
						oninput={(ev) => { identifier = asciiOnly((ev.currentTarget as HTMLInputElement).value); }}
						placeholder="ramana_ambore  or  you@example.com"
						spellcheck="false"
					/>
				</div>
				{#if errors.identifier}
					<p class="mt-1 text-xs text-vermilion">{errors.identifier}</p>
				{/if}
			</div>

			<!-- Password -->
			<div>
				<label for="password" class="label block">
					<span class="block">Password</span>
					<span class="block leading-tight" lang={langStore.current}>{tx('password', langStore.current)}</span>
				</label>
				<div class="relative">
					<Lock size={16} class="absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none text-ink/40" />
					<input
						id="password"
						type="password"
						autocomplete="current-password"
						class="input pl-10"
						class:border-vermilion={errors.password}
						bind:value={password}
					/>
				</div>
				{#if errors.password}
					<p class="mt-1 text-xs text-vermilion">{errors.password}</p>
				{/if}
			</div>

			<button type="submit" class="btn-primary w-full flex flex-col items-center justify-center text-center leading-tight py-2 min-h-[52px] whitespace-normal" disabled={loading}>
				<span class="text-sm">{loading ? 'Signing in…' : T.login.en}</span>
				{#if !loading}<span lang={langStore.current} class="text-[10px] opacity-90" style="color:inherit">{tx('login', langStore.current)}</span>{/if}
			</button>
		</form>

		<p class="mt-6 text-center text-sm text-ink/60">
			Don't have an account?
			<a href="/register" class="font-medium text-saffron hover:underline">
				{T.register.en} · <span lang={langStore.current}>{tx('register', langStore.current)}</span>
			</a>
		</p>
	</div>
</div>
