<script lang="ts">
	import { onMount } from 'svelte';
	import { admin as adminApi } from '$lib/api';
	import { ApiError } from '$lib/api';
	import { toastStore } from '$lib/stores/toast.svelte';
	import { goto, invalidateAll } from '$app/navigation';
	import { Loader, Save, Eye, EyeOff } from 'lucide-svelte';

	type FieldType = 'text' | 'password' | 'number' | 'boolean' | 'email';

	interface FieldMeta {
		key: string;
		label: string;
		description: string;
		type: FieldType;
	}

	interface SettingsGroup {
		title: string;
		fields: FieldMeta[];
	}

	const GROUPS: SettingsGroup[] = [
		{
			title: 'System',
			fields: [
				{ key: 'owner_email', label: 'Owner Email', description: 'Admin email — receives profile request notifications', type: 'email' },
				{ key: 'is_prod', label: 'Production mode', description: 'When OFF: relaxed validation, "TEST MODE" prefixed in emails/Telegram, duplicate email/phone allowed for testing. Turn ON for live site.', type: 'boolean' }
			]
		},
		{
			title: 'Email / SMTP',
			fields: [
				{ key: 'smtp_host', label: 'SMTP Host', description: 'Mail server hostname (empty = log to stdout only)', type: 'text' },
				{ key: 'smtp_port', label: 'SMTP Port', description: '465 = TLS · 587 = STARTTLS · 1025 = local Mailhog', type: 'number' },
				{ key: 'smtp_user', label: 'SMTP Username', description: 'Auth username for the mail server', type: 'text' },
				{ key: 'smtp_password', label: 'SMTP Password', description: 'Auth password — masked after save', type: 'password' },
				{ key: 'smtp_from', label: 'From Address', description: 'Email "From:" header for all outbound mail', type: 'email' }
			]
		},
		{
			title: 'Profile Approval',
			fields: [
				{ key: 'require_admin_approval_for_profiles', label: 'Require Admin Approval', description: 'Profiles need review before going live. Disable to auto-approve on submit.', type: 'boolean' },
				{ key: 'require_face_detection', label: 'Require Face Detection', description: 'Enforce single-face validation on uploaded photos. Disable for testing.', type: 'boolean' }
			]
		},
		{
			title: 'Photo Settings',
			fields: [
				{ key: 'upload_max_mb', label: 'Max Upload Size (MB)', description: 'Maximum raw upload file size before processing', type: 'number' },
				{ key: 'photo_max_kb', label: 'Max JPEG Size (KB)', description: 'Target file size after compression', type: 'number' },
				{ key: 'photos_max_per_profile', label: 'Max Photos per Profile', description: 'How many photos a single profile can have', type: 'number' },
				{ key: 'photo_passport_width', label: 'Passport Width (px)', description: 'Width of the full-resolution passport variant', type: 'number' },
				{ key: 'photo_passport_height', label: 'Passport Height (px)', description: 'Height of the full-resolution passport variant', type: 'number' },
				{ key: 'photo_blur_width', label: 'Blurred Variant Width (px)', description: 'Width of the blurred preview shown in search results', type: 'number' },
				{ key: 'photo_blur_radius', label: 'Blur Radius (px)', description: 'Gaussian blur radius applied to search preview photos', type: 'number' },
				{ key: 'photo_thumb_size', label: 'Thumbnail Size (px)', description: 'Square thumbnail dimension used in admin lists', type: 'number' }
			]
		},
		{
			title: 'Telegram Alerts — Matrimony Bot (@MarathaKalaynamAlertsbot)',
			fields: [
				{ key: 'matrimony_tg_enabled', label: 'Enable Telegram Alerts', description: 'Send Telegram notifications on registrations, profile events, and view requests', type: 'boolean' },
				{ key: 'matrimony_tg_token', label: 'Bot Token', description: 'Token from @BotFather — masked after save. Current bot: @MarathaKalaynamAlertsbot', type: 'password' },
				{ key: 'matrimony_tg_chat_id', label: 'Admin Chat ID', description: 'Your Telegram chat ID. Send /chatid to the bot to get it.', type: 'text' }
			]
		}
	];

	const KNOWN_KEYS = new Set(GROUPS.flatMap((g) => g.fields.map((f) => f.key)));

	let values = $state<Record<string, string>>({});
	let loading = $state(true);
	let saving = $state(false);
	let showPasswords = $state<Record<string, boolean>>({});
	let extraKeys = $state<string[]>([]);
	let fieldErrors = $state<Record<string, string>>({});

	// Accept either bare email or RFC display-name form: 'Name <addr@example.com>'
	const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
	const ANGLE_RE = /<([^>]+)>/;

	function isValidEmailLike(value: string): boolean {
		const v = value.trim();
		if (v === '') return true; // empty is allowed (clears the setting)
		const m = ANGLE_RE.exec(v);
		const addr = m ? m[1].trim() : v;
		return EMAIL_RE.test(addr);
	}

	function validateAll(): boolean {
		const errs: Record<string, string> = {};
		for (const group of GROUPS) {
			for (const f of group.fields) {
				const v = values[f.key] ?? '';
				if (f.type === 'email' && !isValidEmailLike(v)) {
					errs[f.key] = "Enter a valid email (e.g. name@example.com or 'Name <name@example.com>')";
				}
			}
		}
		fieldErrors = errs;
		return Object.keys(errs).length === 0;
	}

	function rawToValues(raw: unknown): Record<string, string> {
		const entries: [string, unknown][] = Array.isArray(raw)
			? (raw as { key: string; value: unknown }[]).map((s) => [s.key, s.value])
			: Object.entries(raw as Record<string, unknown>);
		return Object.fromEntries(entries.map(([k, v]) => [k, v == null ? '' : String(v)]));
	}

	onMount(async () => {
		try {
			const raw = await adminApi.settings.get();
			values = rawToValues(raw);
			extraKeys = Object.keys(values).filter((k) => !KNOWN_KEYS.has(k));
		} catch (err) {
			if (err instanceof ApiError) {
				if (err.status === 401) { goto('/login'); return; }
				if (err.status === 403) { goto('/'); return; }
			}
			toastStore.error('Failed to load settings');
		} finally {
			loading = false;
		}
	});

	async function save() {
		if (!validateAll()) {
			toastStore.error('Fix the highlighted fields and try again.');
			return;
		}
		saving = true;
		try {
			const payload: Record<string, unknown> = {};
			const allFields = GROUPS.flatMap((g) => g.fields);
			for (const [k, v] of Object.entries(values)) {
				const field = allFields.find((f) => f.key === k);
				if (field?.type === 'boolean') {
					payload[k] = v === 'true';
				} else if (field?.type === 'number') {
					payload[k] = v === '' ? 0 : Number(v);
				} else {
					payload[k] = v;
				}
			}
			const raw = await adminApi.settings.update(payload as Record<string, string>);
			values = rawToValues(raw);
			fieldErrors = {};
			// Refresh layout data so the navbar Test/Admin chips reflect the
			// new is_prod / role state immediately (no manual reload needed).
			await invalidateAll();
			toastStore.success('Settings saved');
		} catch (err) {
			// Surface backend validation errors when present (e.g. invalid_email)
			const msg = err instanceof ApiError ? err.message : 'Failed to save settings';
			toastStore.error(msg);
		} finally {
			saving = false;
		}
	}
</script>

<svelte:head>
	<title>Admin: Settings — Maratha Kalyanam</title>
</svelte:head>

<div class="mx-auto max-w-2xl px-4 py-10">
	<div class="flex flex-wrap items-center justify-between gap-3 mb-2">
		<h1 class="font-serif text-3xl font-bold text-maroon">Settings</h1>
		<a href="/admin" class="btn-secondary text-sm">← Dashboard</a>
	</div>
	<p class="text-sm text-ink/60 mb-8">Runtime configuration — changes take effect immediately.</p>

	{#if loading}
		<div class="flex items-center justify-center py-20">
			<Loader size={36} class="animate-spin text-saffron" />
		</div>
	{:else}
		<form onsubmit={(e) => { e.preventDefault(); save(); }} class="space-y-6">

			{#each GROUPS as group}
				<div class="card p-0 overflow-hidden">
					<div class="px-5 py-3 border-b border-gold/20" style="background: rgba(107,15,26,0.06);">
						<h2 class="font-serif text-base font-semibold text-maroon">{group.title}</h2>
					</div>
					<div class="divide-y divide-gold/15">
						{#each group.fields as field}
							<div class="px-5 py-4">
								<label for="s-{field.key}" class="label mb-0.5">{field.label}</label>
								<p class="text-xs text-ink/50 mb-1.5">{field.description}</p>

								{#if field.type === 'boolean'}
									<label class="flex items-center gap-2 cursor-pointer w-fit">
										<input
											id="s-{field.key}"
											type="checkbox"
											class="h-4 w-4 rounded accent-maroon"
											checked={values[field.key] === 'true'}
											onchange={(e) => { values[field.key] = e.currentTarget.checked ? 'true' : 'false'; }}
										/>
										<span class="text-sm text-ink/70">{values[field.key] === 'true' ? 'Enabled' : 'Disabled'}</span>
									</label>

								{:else if field.type === 'password'}
									<div class="relative">
										<input
											id="s-{field.key}"
											type={showPasswords[field.key] ? 'text' : 'password'}
											class="input pr-10 font-mono text-sm"
											bind:value={values[field.key]}
											placeholder={values[field.key] === '***' ? '(set — enter new value to change)' : ''}
											onfocus={() => { if (values[field.key] === '***') values[field.key] = ''; }}
										/>
										<button
											type="button"
											class="absolute right-2.5 top-1/2 -translate-y-1/2 text-ink/40 hover:text-ink"
											onclick={() => { showPasswords[field.key] = !showPasswords[field.key]; }}
											aria-label="Toggle visibility"
										>
											{#if showPasswords[field.key]}
												<EyeOff size={16} />
											{:else}
												<Eye size={16} />
											{/if}
										</button>
									</div>

								{:else if field.type === 'number'}
									<input
										id="s-{field.key}"
										type="number"
										class="input font-mono text-sm"
										bind:value={values[field.key]}
									/>

								{:else}
									<input
										id="s-{field.key}"
										type="text"
										class="input font-mono text-sm {fieldErrors[field.key] ? 'border-vermilion' : ''}"
										bind:value={values[field.key]}
										onblur={() => { if (field.type === 'email') validateAll(); }}
									/>
									{#if fieldErrors[field.key]}
										<p class="mt-1 text-xs text-vermilion">{fieldErrors[field.key]}</p>
									{/if}
								{/if}
							</div>
						{/each}
					</div>
				</div>
			{/each}

			{#if extraKeys.length > 0}
				<div class="card p-0 overflow-hidden">
					<div class="px-5 py-3 border-b border-gold/20" style="background: rgba(0,0,0,0.03);">
						<h2 class="font-serif text-base font-semibold text-ink/60">Other Settings</h2>
					</div>
					<div class="divide-y divide-gold/15">
						{#each extraKeys as key}
							<div class="px-5 py-4">
								<label for="s-{key}" class="label font-mono text-xs mb-1">{key}</label>
								<input id="s-{key}" type="text" class="input font-mono text-sm" bind:value={values[key]} />
							</div>
						{/each}
					</div>
				</div>
			{/if}

			<div class="flex justify-end">
				<button type="submit" class="btn-primary flex items-center gap-2" disabled={saving}>
					<Save size={16} />
					{saving ? 'Saving…' : 'Save Settings'}
				</button>
			</div>
		</form>

		<div class="mt-8 rounded-lg border border-saffron/30 bg-saffron/5 p-4 text-sm">
			<p class="font-semibold text-maroon mb-2">Setting up Telegram alerts</p>
			<ol class="list-decimal list-inside space-y-1 text-ink/70">
				<li>Paste the bot token into <span class="font-mono text-xs bg-cream px-1 rounded">matrimony_tg_token</span> and save.</li>
				<li>Message <span class="font-mono text-xs bg-cream px-1 rounded">@MarathaKalaynamAlertsbot</span> on Telegram: send <span class="font-mono text-xs bg-cream px-1 rounded">/chatid</span></li>
				<li>The bot replies with your chat ID — paste it into <span class="font-mono text-xs bg-cream px-1 rounded">matrimony_tg_chat_id</span> and save.</li>
				<li>Enable the <span class="font-mono text-xs bg-cream px-1 rounded">matrimony_tg_enabled</span> toggle.</li>
			</ol>
		</div>
	{/if}
</div>
