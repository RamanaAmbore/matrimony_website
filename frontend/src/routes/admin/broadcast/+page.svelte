<script lang="ts">
	import { admin as adminApi, ApiError } from '$lib/api';
	import { toastStore } from '$lib/stores/toast.svelte';
	import { Loader } from 'lucide-svelte';

	let broadcastSubject = $state('');
	let broadcastBody = $state('');
	let broadcastVerifiedOnly = $state(true);
	let broadcastApprovedOnly = $state(false);
	let broadcastSending = $state(false);
	let broadcastResult = $state<{ sent: number; failed: number } | null>(null);

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
				filter_verified_only: broadcastVerifiedOnly,
				filter_approved_only: broadcastApprovedOnly
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
		<a href="/admin" class="btn-secondary text-sm">← Dashboard</a>
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

			<div class="flex flex-wrap items-center gap-4">
				<label class="flex cursor-pointer items-center gap-2 text-sm">
					<input type="checkbox" bind:checked={broadcastVerifiedOnly} class="rounded accent-maroon" />
					Verified emails only
				</label>
				<label class="flex cursor-pointer items-center gap-2 text-sm">
					<input type="checkbox" bind:checked={broadcastApprovedOnly} class="rounded accent-maroon" />
					Approved users only
				</label>
			</div>

			<div class="flex flex-wrap items-center justify-end gap-2 border-t border-gold/30 pt-4">
				<a href="/admin" class="btn-secondary text-sm px-4 py-2">Cancel</a>
				<button
					class="btn-primary text-sm px-6 py-2"
					disabled={broadcastSending}
					onclick={sendBroadcast}
				>
					{#if broadcastSending}
						<Loader size={14} class="mr-1 inline animate-spin" />Sending…
					{:else}
						Send Broadcast
					{/if}
				</button>
			</div>
		</div>
	</div>
</div>
