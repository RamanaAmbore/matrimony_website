// Toast notification store using Svelte 5 runes

export type ToastKind = 'success' | 'error' | 'info';

export interface Toast {
	id: number;
	kind: ToastKind;
	message: string;
}

function createToastStore() {
	let toasts = $state<Toast[]>([]);
	let next = 0;

	function add(kind: ToastKind, message: string, duration = 4000) {
		const id = next++;
		toasts = [...toasts, { id, kind, message }];
		if (duration > 0) {
			setTimeout(() => remove(id), duration);
		}
		return id;
	}

	function remove(id: number) {
		toasts = toasts.filter((t) => t.id !== id);
	}

	function success(message: string) {
		return add('success', message);
	}

	function error(message: string) {
		return add('error', message);
	}

	function info(message: string) {
		return add('info', message);
	}

	return {
		get toasts() {
			return toasts;
		},
		add,
		remove,
		success,
		error,
		info
	};
}

export const toastStore = createToastStore();
