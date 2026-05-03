<script lang="ts">
	import { untrack } from 'svelte';
	import { photos as photosApi, type Photo } from '$lib/api';
	import { ApiError } from '$lib/api';
	import { toastStore } from '$lib/stores/toast.svelte';
	import { Upload, Trash2, Star, ImagePlus } from 'lucide-svelte';

	let {
		profileId,
		initialPhotos = [],
		maxPhotos = 5,
		isOwner = true,
		onCountChange = undefined
	}: {
		profileId: string;
		initialPhotos?: Photo[];
		maxPhotos?: number;
		isOwner?: boolean;
		onCountChange?: (count: number) => void;
	} = $props();

	// Seed local list from prop once; uploads/deletes mutate local state only.
	let photoList = $state<Photo[]>(untrack(() => initialPhotos));

	$effect(() => { onCountChange?.(photoList.length); });
	let uploading = $state(false);
	let uploadError = $state('');
	let dragging = $state(false);
	let fileInputEl = $state<HTMLInputElement | null>(null);

	// Sync when parent pushes fresh photos (e.g. after edit-page re-fetch)
	$effect(() => {
		if (initialPhotos !== untrack(() => photoList)) {
			photoList = initialPhotos;
		}
	});

	async function handleFiles(files: FileList | null) {
		if (!files || files.length === 0) return;
		if (photoList.length >= maxPhotos) {
			toastStore.error(`Max ${maxPhotos} photos allowed`);
			return;
		}
		uploading = true;
		uploadError = '';
		try {
			const photo = await photosApi.upload(profileId, files[0]);
			photoList = [...photoList, photo];
			toastStore.success('Photo uploaded!');
		} catch (err) {
			if (err instanceof ApiError) {
				if (err.code === 'photo_validation_failed') {
					uploadError = err.message;
				} else {
					uploadError = err.message;
				}
			} else {
				uploadError = 'Upload failed. Please try again.';
			}
		} finally {
			uploading = false;
			if (fileInputEl) fileInputEl.value = '';
		}
	}

	function handleDrop(e: DragEvent) {
		e.preventDefault();
		dragging = false;
		handleFiles(e.dataTransfer?.files ?? null);
	}

	function handleDragOver(e: DragEvent) {
		e.preventDefault();
		dragging = true;
	}

	function handleDragLeave() {
		dragging = false;
	}

	async function setPrimary(photo: Photo) {
		try {
			await photosApi.setPrimary(profileId, photo.id);
			photoList = photoList.map((p) => ({ ...p, is_primary: p.id === photo.id }));
		} catch {
			toastStore.error('Could not set primary photo');
		}
	}

	async function deletePhoto(photo: Photo) {
		if (!confirm('Delete this photo?')) return;
		try {
			await photosApi.delete(profileId, photo.id);
			photoList = photoList.filter((p) => p.id !== photo.id);
			toastStore.success('Photo deleted');
		} catch {
			toastStore.error('Could not delete photo');
		}
	}
</script>

<div class="card mt-6">
	<div class="mb-4 flex items-center justify-between">
		<h2 class="font-serif text-xl font-semibold text-maroon">Photos</h2>
		<span class="text-sm text-ink/50">{photoList.length} / {maxPhotos}</span>
	</div>

	<!-- Upload zone -->
	{#if isOwner && photoList.length < maxPhotos}
		<!-- svelte-ignore a11y_no_static_element_interactions -->
		<div
			class="mb-4 rounded-lg border-2 border-dashed transition-colors duration-200 p-6 text-center cursor-pointer
				{dragging ? 'border-saffron bg-saffron/5' : 'border-gold/40 hover:border-saffron/60'}"
			ondrop={handleDrop}
			ondragover={handleDragOver}
			ondragleave={handleDragLeave}
			onclick={() => fileInputEl?.click()}
			onkeydown={(e) => { if (e.key === 'Enter' || e.key === ' ') fileInputEl?.click(); }}
			role="button"
			tabindex="0"
			aria-label="Upload photo"
		>
			<input
				bind:this={fileInputEl}
				type="file"
				accept="image/jpeg,image/png,image/webp"
				class="sr-only"
				onchange={(e) => handleFiles((e.target as HTMLInputElement).files)}
			/>
			{#if uploading}
				<div class="flex flex-col items-center gap-2 text-ink/50">
					<Upload size={28} class="animate-bounce text-saffron" />
					<p class="text-sm">Uploading…</p>
				</div>
			{:else}
				<div class="flex flex-col items-center gap-2 text-ink/50">
					<ImagePlus size={28} class="text-gold" />
					<p class="text-sm font-medium">Drag & drop or click to upload</p>
					<p class="text-xs">Passport-style photo — one face clearly visible · JPEG/PNG/WebP</p>
				</div>
			{/if}
		</div>

		{#if uploadError}
			<div class="mb-4 rounded-lg border border-vermilion/30 bg-vermilion/5 p-3 text-sm text-vermilion">
				{uploadError}
			</div>
		{/if}
	{/if}

	<!-- Photo grid -->
	{#if photoList.length === 0}
		<p class="py-6 text-center text-sm text-ink/40">No photos uploaded yet.</p>
	{:else}
		<div class="grid grid-cols-2 gap-3 sm:grid-cols-3 md:grid-cols-4">
			{#each photoList as photo (photo.id)}
				<div class="group relative aspect-[3/4] overflow-hidden rounded-lg border border-gold/20">
					<!-- Blurred photo (public view) — owner sees passport_url if available -->
					<img
						src={photo.passport_url ?? photo.blurred_url}
						alt=""
						role="presentation"
						class="h-full w-full object-cover"
						loading="lazy"
					/>

					{#if photo.is_primary}
						<span class="absolute top-1 left-1 rounded bg-gold px-1.5 py-0.5 text-xs font-bold text-ink">
							Primary
						</span>
					{/if}

					{#if isOwner}
						<div class="absolute inset-0 flex items-end justify-center gap-2 bg-ink/50 p-2 opacity-0 transition-opacity duration-200 group-hover:opacity-100 group-focus-within:opacity-100">
							{#if !photo.is_primary}
								<button
									onclick={() => setPrimary(photo)}
									class="rounded bg-gold p-1.5 text-ink hover:bg-marigold"
									title="Set as primary"
									aria-label="Set as primary photo"
								>
									<Star size={14} />
								</button>
							{/if}
							<button
								onclick={() => deletePhoto(photo)}
								class="rounded bg-vermilion p-1.5 text-white hover:bg-vermilion/80"
								title="Delete photo"
								aria-label="Delete photo"
							>
								<Trash2 size={14} />
							</button>
						</div>
					{/if}
				</div>
			{/each}
		</div>
	{/if}
</div>
