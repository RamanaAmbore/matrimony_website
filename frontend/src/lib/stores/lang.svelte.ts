// Reactive language preference, persisted to localStorage. The English line
// in the bilingual UI is constant; this store controls which translation
// is shown alongside it (Telugu / Marathi / Kannada / Tamil / Hindi).

export type Lang = 'te' | 'mr' | 'kn' | 'ta' | 'hi';

export const LANGS: { code: Lang; label: string; native: string }[] = [
	{ code: 'te',  label: 'Telugu',    native: 'తెలుగు' },
	{ code: 'mr',  label: 'Marathi',   native: 'मराठी' },
	{ code: 'kn',  label: 'Kannada',   native: 'ಕನ್ನಡ' },
	{ code: 'ta',  label: 'Tamil',     native: 'தமிழ்' },
	{ code: 'hi',  label: 'Hindi',     native: 'हिन्दी' }
];

const STORAGE_KEY = 'mk_lang';
const DEFAULT_LANG: Lang = 'te';

function readInitial(): Lang {
	if (typeof window === 'undefined') return DEFAULT_LANG;
	try {
		const raw = window.localStorage.getItem(STORAGE_KEY);
		if (raw && LANGS.some((l) => l.code === raw)) return raw as Lang;
	} catch {
		// localStorage may be disabled (private mode) — silently fall back
	}
	return DEFAULT_LANG;
}

class LangStore {
	current = $state<Lang>(readInitial());

	set(lang: Lang) {
		this.current = lang;
		if (typeof window !== 'undefined') {
			try {
				window.localStorage.setItem(STORAGE_KEY, lang);
			} catch {
				// localStorage may be disabled — change still applies in-memory
			}
		}
	}
}

export const langStore = new LangStore();
