<script lang="ts">
	import { admin as adminApi, ApiError } from '$lib/api';
	import { toastStore } from '$lib/stores/toast.svelte';
	import { Loader } from 'lucide-svelte';
	import { tx } from '$lib/i18n';
	import { langStore } from '$lib/stores/lang.svelte';
	import Combobox from '$lib/components/Combobox.svelte';
	import { MOTHER_TONGUES, INDIA_STATES, COUNTRIES_PRIORITY, COUNTRIES_OTHER } from '$lib/profileOptions';

	const COUNTRIES = [...COUNTRIES_PRIORITY, ...COUNTRIES_OTHER];

	let broadcastSubject = $state('');
	let broadcastBody = $state('');

	// Audience filters — user-side flags
	let filterVerifiedOnly = $state(false);
	let filterUnverifiedOnly = $state(false);
	let filterApprovedOnly = $state(false);
	let filterUnapprovedOnly = $state(false);
	let filterAdminOnly = $state(false);
	// Audience filters — profile-side dropdowns
	let filterMotherTongue = $state('');
	let filterState = $state('');
	let filterCountry = $state('');

	let broadcastSending = $state(false);
	let broadcastResult = $state<{ sent: number; failed: number } | null>(null);

	// Mutually-exclusive guards: latest checked wins
	function onVerifiedChange() {
		if (filterVerifiedOnly) filterUnverifiedOnly = false;
	}
	function onUnverifiedChange() {
		if (filterUnverifiedOnly) filterVerifiedOnly = false;
	}
	function onApprovedChange() {
		if (filterApprovedOnly) filterUnapprovedOnly = false;
	}
	function onUnapprovedChange() {
		if (filterUnapprovedOnly) filterApprovedOnly = false;
	}

	let filterSummary = $derived(() => {
		const parts: string[] = [];
		if (filterVerifiedOnly) parts.push('verified emails');
		if (filterUnverifiedOnly) parts.push('unverified emails');
		if (filterApprovedOnly) parts.push('approved users');
		if (filterUnapprovedOnly) parts.push('unapproved users');
		if (filterAdminOnly) parts.push('admin users');
		if (filterMotherTongue) parts.push(`mother tongue ${filterMotherTongue}`);
		if (filterState) parts.push(`state ${filterState}`);
		if (filterCountry) parts.push(`country ${filterCountry}`);
		return parts.length > 0 ? parts.join(', ') : null;
	});

	async function sendBroadcast() {
		if (!broadcastSubject.trim() || !broadcastBody.trim()) {
			toastStore.error('Subject and message body are required.');
			return;
		}
		broadcastSending = true;
		broadcastResult = null;
		try {
			const result = await adminApi.broadcastEmail({
				subject: broadcastSubject.trim(),
				body_html: broadcastBody.trim(),
				filter_verified_only: filterVerifiedOnly || undefined,
				filter_unverified_only: filterUnverifiedOnly || undefined,
				filter_approved_only: filterApprovedOnly || undefined,
				filter_unapproved_only: filterUnapprovedOnly || undefined,
				filter_admin_only: filterAdminOnly || undefined,
				filter_mother_tongue: filterMotherTongue || undefined,
				filter_state: filterState || undefined,
				filter_country: filterCountry || undefined
			});
			broadcastResult = result;
			toastStore.success(`Broadcast sent: ${result.sent} delivered, ${result.failed} failed.`);
		} catch (err) {
			toastStore.error(err instanceof ApiError ? err.message : 'Broadcast failed.');
		} finally {
			broadcastSending = false;
		}
	}
</script>

<svelte:head>
	<title>Admin: Broadcast Email — Maratha Kalyanam</title>
</svelte:head>

<div class="mx-auto max-w-2xl px-4 py-10">
	<div class="mb-2 flex flex-wrap items-center justify-between gap-3">
		<h1 class="font-serif text-3xl font-bold text-maroon">Broadcast Email</h1>
		<a href="/admin" class="btn-secondary flex flex-col items-center justify-center text-center leading-tight text-sm px-3 py-1.5 min-h-[44px] whitespace-normal">
			<span>← Dashboard</span>
			<span lang={langStore.current} class="text-[10px] opacity-90">{tx('dashboardBack', langStore.current)}</span>
		</a>
	</div>
	<p class="mb-8 text-sm text-ink/60">Send an HTML email to a filtered subset of registered users.</p>

	<div class="rounded-lg border border-gold/30 bg-white p-5 shadow-sm">
		{#if broadcastResult}
			<div class="mb-4 rounded border border-green-300 bg-green-50 px-4 py-2 text-sm text-green-800">
				Sent: {broadcastResult.sent} · Failed: {broadcastResult.failed}
			</div>
		{/if}

		<div class="space-y-4">
			<div>
				<label class="label" for="bc-subject">Subject</label>
				<input
					id="bc-subject"
					type="text"
					class="input w-full"
					placeholder="e.g. New profiles available on Maratha Kalyanam"
					bind:value={broadcastSubject}
				/>
			</div>

			<div>
				<label class="label" for="bc-body">HTML Body</label>
				<textarea
					id="bc-body"
					class="input w-full resize-y font-mono text-sm"
					style="min-height: 10rem;"
					placeholder="<p>Dear member,</p>…"
					bind:value={broadcastBody}
				></textarea>
			</div>

			<!-- Audience filters -->
			<div class="rounded-lg border border-gold/20 bg-cream/40 px-4 py-3">
				<p class="mb-3 text-xs font-semibold uppercase tracking-wider text-ink/50">Audience</p>
				<div class="grid grid-cols-1 gap-2 sm:grid-cols-2">
					<label class="flex cursor-pointer items-center gap-2 text-sm">
						<input
							type="checkbox"
							bind:checked={filterVerifiedOnly}
							onchange={onVerifiedChange}
							class="rounded accent-maroon"
						/>
						Verified emails only
					</label>
					<label class="flex cursor-pointer items-center gap-2 text-sm">
						<input
							type="checkbox"
							bind:checked={filterUnverifiedOnly}
							onchange={onUnverifiedChange}
							class="rounded accent-maroon"
						/>
						Unverified emails only
					</label>
					<label class="flex cursor-pointer items-center gap-2 text-sm">
						<input
							type="checkbox"
							bind:checked={filterApprovedOnly}
							onchange={onApprovedChange}
							class="rounded accent-maroon"
						/>
						Approved users only
					</label>
					<label class="flex cursor-pointer items-center gap-2 text-sm">
						<input
							type="checkbox"
							bind:checked={filterUnapprovedOnly}
							onchange={onUnapprovedChange}
							class="rounded accent-maroon"
						/>
						Unapproved users only
					</label>
					<label class="flex cursor-pointer items-center gap-2 text-sm sm:col-span-2">
						<input
							type="checkbox"
							bind:checked={filterAdminOnly}
							class="rounded accent-maroon"
						/>
						Admin users only
					</label>
				</div>

				<!-- Profile-side filters: restrict audience to users whose profile
				     matches all selected criteria. Empty = no restriction. -->
				<div class="mt-4 border-t border-gold/20 pt-3">
					<p class="mb-3 text-xs font-semibold uppercase tracking-wider text-ink/50">Recipient</p>
					<div class="grid grid-cols-1 gap-3 sm:grid-cols-3">
						<div>
							<label for="bc-tongue" class="label text-xs">Mother tongue</label>
							<Combobox id="bc-tongue" bind:value={filterMotherTongue} options={['', ...MOTHER_TONGUES]} placeholder="Any" />
						</div>
						<div>
							<label for="bc-state" class="label text-xs">State</label>
							<Combobox id="bc-state" bind:value={filterState} options={['', ...INDIA_STATES]} allowCustom={true} placeholder="Any" />
						</div>
						<div>
							<label for="bc-country" class="label text-xs">Country</label>
							<Combobox id="bc-country" bind:value={filterCountry} options={['', ...COUNTRIES]} allowCustom={true} placeholder="Any" />
						</div>
					</div>
				</div>
				<p class="mt-3 text-xs text-ink/60">
					{#if filterSummary()}
						Sending to: <span class="font-medium text-maroon">{filterSummary()}</span>
					{:else}
						Sending to: <span class="font-medium text-ink/80">all registered users</span>
					{/if}
				</p>
			</div>

			<div class="flex flex-wrap items-center justify-end gap-2 border-t border-gold/30 pt-4">
				<a href="/admin" class="btn-secondary flex flex-col items-center justify-center text-center leading-tight text-sm px-4 py-1.5 min-h-[44px] whitespace-normal">
					<span>Cancel</span>
					<span lang={langStore.current} class="text-[10px] opacity-90">{tx('cancel', langStore.current)}</span>
				</a>
				<button
					class="btn-primary flex flex-col items-center justify-center text-center leading-tight text-sm px-6 py-1.5 min-h-[44px] whitespace-normal"
					disabled={broadcastSending}
					onclick={sendBroadcast}
				>
					{#if broadcastSending}
						<span class="flex items-center gap-1"><Loader size={13} class="animate-spin" />Sending…</span>
					{:else}
						<span>Send Broadcast</span>
						<span lang={langStore.current} class="text-[10px] opacity-90">{tx('sendBroadcast', langStore.current)}</span>
					{/if}
				</button>
			</div>
		</div>
	</div>
</div>
