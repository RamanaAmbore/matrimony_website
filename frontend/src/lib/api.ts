// Typed API client — wraps fetch with credentials, JSON handling, typed errors.
// All paths are relative so the Vite proxy handles /api/* -> localhost:8000.

export class ApiError extends Error {
	constructor(
		public status: number,
		public code: string,
		message: string
	) {
		super(message);
		this.name = 'ApiError';
	}
}

// ─── Entity interfaces ────────────────────────────────────────────────────────

export interface User {
	uuid: string;
	user_id: string;
	email: string;
	phone_number: string;
	full_name: string;
	is_admin: boolean;
	is_super: boolean;
	is_approved: boolean;
	is_revoked: boolean;
	is_paused?: boolean;     // user-set vacation mode
	is_suspended?: boolean;  // admin-set enforcement hold
	email_verified: boolean;
}

export type ProfileStatus = 'draft' | 'pending' | 'approved' | 'revoked';
export type Gender = 'bride' | 'groom';
export type Manglik = 'yes' | 'no' | 'partial' | 'unknown';
export type Diet = 'veg' | 'non-veg' | 'eggetarian' | 'jain' | 'vegan';
export type MaritalStatus = 'never_married' | 'divorced' | 'widowed' | 'awaiting_divorce';
export type Complexion = 'very_fair' | 'fair' | 'wheatish' | 'dusky' | 'dark';
export type BodyType = 'slim' | 'average' | 'athletic' | 'heavy';
export type BloodGroup = 'A+' | 'A-' | 'B+' | 'B-' | 'AB+' | 'AB-' | 'O+' | 'O-' | 'unknown';
export type FamilyType = 'nuclear' | 'joint';
export type FamilyStatus = 'middle_class' | 'upper_middle' | 'affluent' | 'rich';
export type FamilyValues = 'orthodox' | 'traditional' | 'moderate' | 'liberal';
export type SmokeDrink = 'no' | 'occasionally' | 'yes';

export interface Profile {
	id: string;
	profile_number: string;
	owner_user_id: string;
	status: ProfileStatus;
	// Aggregated photo metadata (admin list only) — present on /admin/profiles
	// responses, omitted on owner-facing endpoints.
	photos_count?: number;
	photos_bytes?: number;

	// Basic Information
	gender: Gender;
	first_name: string;
	last_name: string;
	dob: string; // ISO date string YYYY-MM-DD
	marital_status?: MaritalStatus | null;
	mother_tongue: string;
	caste?: string | null;
	sub_caste?: string | null;
	surname_clan: string;

	// Physical
	height_cm: number;
	weight_kg?: number | null;
	complexion?: Complexion | string | null;
	body_type?: BodyType | null;
	blood_group?: BloodGroup | null;

	// Astrology
	gotra: string;
	kuldevata: string;
	devak: string;
	nakshatram: string;
	rashi: string;
	manglik: Manglik;
	time_of_birth?: string | null;
	place_of_birth?: string | null;

	// Education & Career
	education: string;
	college_university?: string | null;
	occupation: string;
	employer?: string | null;
	annual_income_inr?: number | null;
	work_location?: string | null;

	// Family
	father_name?: string | null;
	mother_name?: string | null;
	num_family_members?: number | null;
	father_occupation?: string | null;
	mother_occupation?: string | null;
	num_brothers?: number | null;
	num_sisters?: number | null;
	num_brothers_married?: number | null;
	num_sisters_married?: number | null;
	family_type?: FamilyType | null;
	family_status?: FamilyStatus | null;
	family_values?: FamilyValues | null;
	native_place?: string | null;

	// Lifestyle
	diet: Diet;
	smokes?: SmokeDrink | null;
	drinks?: SmokeDrink | null;
	hobbies?: string | null;

	// Location
	city: string;
	state: string;
	country: string;
	pin_code?: string | null;

	// Per-profile contact (separate from User account phone)
	contact_phone?: string | null;

	// About
	about: string;
	partner_expectations: string;

	created_at: string;
	updated_at: string;
}

export interface Photo {
	id: string;
	profile_id: string;
	is_primary: boolean;
	blurred_url: string;
	passport_url?: string; // only visible to owner
	thumb_url?: string; // admin
	created_at: string;
}

export interface ProfileWithPhotos {
	profile: Profile;
	photos: Photo[];
	is_full_access?: boolean;
}

export type RequestStatus = 'pending' | 'approved' | 'revoked';

export interface DetailRequest {
	id: string;
	request_number?: string | null;
	requester_user_id: string;
	profile_id: string;
	profile?: Partial<Profile>;
	status: RequestStatus;
	message?: string;
	admin_notes?: string;
	created_at: string;
	updated_at: string;
	// Enriched fields from /admin/requests list — populated by the backend
	// when DetailRequest.requester and .profile are eager-loaded.
	requester_email?: string | null;
	requester_name?: string | null;
	profile_number?: string | null;
	profile_first_name?: string | null;
	profile_last_name?: string | null;
	profile_gender?: Gender | null;
	profile_city?: string | null;
}

/** Enriched request row returned by GET /requests/mine.
 *  Includes all DetailRequest fields plus denormalised profile snapshot fields
 *  so the user-facing requests grid doesn't need a second fetch per row.
 */
export interface EnrichedRequest extends DetailRequest {
	profile_first_name: string | null;
	profile_last_name: string | null;
	profile_number: string | null;
	profile_gender: Gender | null;
	profile_dob: string | null;
	profile_city: string | null;
	profile_state: string | null;
	profile_status: ProfileStatus | null;
	profile_blurred_url: string | null;
}

export interface SearchResult {
	id: string;
	gender: Gender;
	first_name: string;
	last_name: string;
	dob: string;
	height_cm: number;
	weight_kg?: number | null;
	education: string;
	occupation: string;
	city: string;
	state: string;
	gotra: string;
	nakshatram: string;
	rashi: string;
	manglik: Manglik;
	diet: Diet;
	blurred_photo_url?: string;
}

export interface SearchResponse {
	results: SearchResult[];
	total: number;
	page: number;
	per_page: number;
}

/** Minimal profile card returned to anonymous (unauthenticated) callers. */
export interface PreviewSearchResult {
	id: string;
	gender: Gender;
	age: number;
	height_cm: number;
	weight_kg?: number | null;
	city: string;
	state: string;
	gotra: string;
	nakshatram: string;
	blurred_url: string | null;
}

/** Search envelope returned when the caller has no session. */
export interface PreviewSearchResponse {
	results: PreviewSearchResult[];
	total: number;
	page: number;
	per_page: number;
	/** Always true — discriminates from SearchResponse. */
	requires_registration: true;
}

export interface Setting {
	key: string;
	value: string;
	description?: string;
}

export interface SiteInfo {
	is_prod: boolean;
	site_url: string;
}

// ─── Admin dashboard types ────────────────────────────────────────────────────

export interface PendingProfileSummary {
	id: string;
	profile_number: string;
	owner_email: string;
	gender: Gender;
	first_name: string;
	last_name: string;
	age: number;
	city: string;
	state: string;
	gotra: string;
	nakshatram: string;
	created_at: string;
}

export interface PendingUser {
	id: string;
	email: string;
	email_verified: boolean;
	created_at: string;
}

export interface PendingRequest {
	id: string;
	requester_email: string;
	profile_id: string;
	profile_first_name: string;
	profile_last_name: string;
	message?: string;
	created_at: string;
}

export interface AdminDashboard {
	stats: {
		users: number;
		users_admins: number;
		// Only present when the caller is a super-user — regular admins
		// don't get visibility into the super tier.
		users_super?: number;
		photos_count?: number;
		photos_total_bytes?: number;
		profiles_total: number;
		profiles_pending: number;
		profiles_approved: number;
		profiles_rejected: number;
		profiles_draft: number;
		requests_pending: number;
		requests_approved: number;
		requests_rejected: number;
		requests_total: number;
	};
	pending_profiles: PendingProfileSummary[];
	pending_users: PendingUser[];
	pending_requests: PendingRequest[];
}

// ─── Search params ────────────────────────────────────────────────────────────

export interface SearchParams {
	gender?: Gender;
	age_min?: number;
	age_max?: number;
	height_min?: number;
	height_max?: number;
	weight_min?: number;
	weight_max?: number;
	gotra?: string;
	nakshatram?: string;
	rashi?: string;
	city?: string;
	state?: string;
	country?: string;
	pin_code?: string;
	mother_tongue?: string;
	manglik?: Manglik;
	diet?: Diet;
	page?: number;
	per_page?: number;
}

// ─── Core fetch wrapper ───────────────────────────────────────────────────────

type FetchLike = typeof fetch;

async function request<T>(
	path: string,
	options: RequestInit & { fetch?: FetchLike } = {}
): Promise<T> {
	const headers: Record<string, string> = {
		...(options.body && !(options.body instanceof FormData)
			? { 'Content-Type': 'application/json' }
			: {}),
		...(options.headers as Record<string, string>)
	};

	// Use the caller-supplied fetch (SvelteKit's `event.fetch` during SSR
	// load, browser fetch otherwise) so the same client works in both
	// contexts. SvelteKit's fetch resolves relative paths, forwards cookies
	// for same-origin, and inlines responses for prerendered pages.
	const f = options.fetch ?? fetch;
	const { fetch: _fetch, ...fetchOpts } = options;
	void _fetch;

	const res = await f(path, {
		...fetchOpts,
		credentials: 'include',
		headers
	});

	if (res.status === 204) {
		return undefined as T;
	}

	let body: unknown;
	const ct = res.headers.get('content-type') ?? '';
	if (ct.includes('application/json')) {
		body = await res.json();
	} else {
		body = await res.text();
	}

	if (!res.ok) {
		// Try to extract structured error from backend
		const err = body as { detail?: string | { message?: string }; error?: { code?: string; message?: string }; message?: string };
		let code = 'unknown_error';
		let message = 'An unexpected error occurred';

		if (err?.error?.code) code = err.error.code;
		if (err?.error?.message) message = err.error.message;
		else if (typeof err?.detail === 'string') message = err.detail;
		else if (typeof err?.detail === 'object' && err.detail?.message) message = err.detail.message;
		else if (err?.message) message = err.message;

		throw new ApiError(res.status, code, message);
	}

	return body as T;
}

function buildQuery(params: Record<string, unknown>): string {
	const q = new URLSearchParams();
	for (const [k, v] of Object.entries(params)) {
		if (v !== undefined && v !== null && v !== '') {
			q.set(k, String(v));
		}
	}
	const s = q.toString();
	return s ? `?${s}` : '';
}

// ─── Site ─────────────────────────────────────────────────────────────────────

export const site = {
	async info(fetch?: FetchLike): Promise<SiteInfo> {
		return request('/api/site/info', { fetch });
	}
};

// ─── Auth ─────────────────────────────────────────────────────────────────────

export const auth = {
	async register(
		full_name: string,
		email: string,
		password: string,
		user_id: string,
		phone_number: string
	): Promise<{ uuid: string }> {
		return request('/api/auth/register', {
			method: 'POST',
			body: JSON.stringify({ email, password, user_id, phone_number, full_name })
		});
	},

	async login(identifier: string, password: string): Promise<User> {
		return request('/api/auth/login', {
			method: 'POST',
			body: JSON.stringify({ identifier, password })
		});
	},

	async logout(): Promise<void> {
		return request('/api/auth/logout', { method: 'POST' });
	},

	async verifyEmail(token: string): Promise<void> {
		return request('/api/auth/verify-email', {
			method: 'POST',
			body: JSON.stringify({ token })
		});
	},

	async me(fetch?: FetchLike): Promise<User> {
		return request('/api/auth/me', { fetch });
	},

	async updateEmail(new_email: string, current_password: string): Promise<{ message: string; email: string }> {
		return request('/api/auth/me/email', { method: 'POST', body: JSON.stringify({ new_email, current_password }) });
	},

	async updatePhone(new_phone: string, current_password: string): Promise<{ message: string; phone_number: string }> {
		return request('/api/auth/me/phone', { method: 'POST', body: JSON.stringify({ new_phone, current_password }) });
	},

	async updatePassword(current_password: string, new_password: string): Promise<{ message: string }> {
		return request('/api/auth/me/password', { method: 'POST', body: JSON.stringify({ current_password, new_password }) });
	},

	async deleteAccount(current_password: string, confirmation: string): Promise<{ deleted: boolean; email: string }> {
		return request('/api/auth/me/delete', {
			method: 'POST',
			body: JSON.stringify({ current_password, confirmation })
		});
	},

	async resendMyVerification(): Promise<{ message: string }> {
		return request('/api/auth/me/resend-verification', { method: 'POST' });
	},

	// Self-service vacation mode (pause = hide my profiles + block new
	// profile creation; unpause = restore). Distinct from admin-set
	// suspend, which only an admin can lift.
	async pauseAccount(): Promise<{ is_paused: boolean; message: string }> {
		return request('/api/auth/me/pause', { method: 'POST' });
	},

	async unpauseAccount(): Promise<{ is_paused: boolean; is_suspended: boolean; message: string }> {
		return request('/api/auth/me/unpause', { method: 'POST' });
	}
};

// ─── Profiles ─────────────────────────────────────────────────────────────────

export type ProfilePayload = Omit<Profile, 'id' | 'profile_number' | 'owner_user_id' | 'status' | 'created_at' | 'updated_at'>;

export const profiles = {
	async list(): Promise<Profile[]> {
		return request('/api/profiles');
	},

	async create(data: Partial<ProfilePayload>): Promise<Profile> {
		return request('/api/profiles', {
			method: 'POST',
			body: JSON.stringify(data)
		});
	},

	async get(id: string): Promise<ProfileWithPhotos> {
		return request(`/api/profiles/${id}`);
	},

	async update(id: string, data: Partial<ProfilePayload>): Promise<Profile> {
		return request(`/api/profiles/${id}`, {
			method: 'PATCH',
			body: JSON.stringify(data)
		});
	},

	async delete(id: string): Promise<void> {
		return request(`/api/profiles/${id}`, { method: 'DELETE' });
	},

	async submit(id: string): Promise<Profile> {
		return request(`/api/profiles/${id}/submit`, { method: 'POST' });
	},

	async requestDetails(id: string, message?: string): Promise<DetailRequest> {
		return request(`/api/profiles/${id}/request`, {
			method: 'POST',
			body: JSON.stringify({ message })
		});
	}
};

// ─── Photos ───────────────────────────────────────────────────────────────────

export const photos = {
	async upload(profileId: string, file: File): Promise<Photo> {
		const form = new FormData();
		form.append('file', file);
		return request(`/api/profiles/${profileId}/photos`, {
			method: 'POST',
			body: form
		});
	},

	async delete(profileId: string, photoId: string): Promise<void> {
		return request(`/api/profiles/${profileId}/photos/${photoId}`, {
			method: 'DELETE'
		});
	},

	async setPrimary(profileId: string, photoId: string): Promise<void> {
		return request(`/api/profiles/${profileId}/photos/${photoId}/primary`, {
			method: 'POST'
		});
	}
};

// ─── Search ───────────────────────────────────────────────────────────────────

export const search = {
	async query(params: SearchParams): Promise<SearchResponse | PreviewSearchResponse> {
		return request(`/api/search${buildQuery(params as Record<string, unknown>)}`);
	}
};

// ─── Requests ─────────────────────────────────────────────────────────────────

export const requests = {
	/** @deprecated Use listMine() for the enriched shape. */
	async mine(): Promise<DetailRequest[]> {
		return request('/api/requests/mine');
	},

	async listMine(): Promise<EnrichedRequest[]> {
		return request('/api/requests/mine');
	},

	async delete(id: string): Promise<void> {
		return request(`/api/requests/${id}`, { method: 'DELETE' });
	}
};

// ─── Admin ────────────────────────────────────────────────────────────────────

export const admin = {
	async dashboard(): Promise<AdminDashboard> {
		return request('/api/admin/dashboard');
	},

	profiles: {
		async list(status?: string): Promise<Profile[]> {
			const q = status ? `?status=${status}` : '';
			return request(`/api/admin/profiles${q}`);
		},
		async approve(id: string, admin_notes?: string): Promise<void> {
			return request(`/api/admin/profiles/${id}/approve`, {
				method: 'POST',
				body: JSON.stringify({ admin_notes })
			});
		},
		async reject(id: string, admin_notes?: string): Promise<Profile> {
			return request(`/api/admin/profiles/${id}/reject`, {
				method: 'POST',
				body: JSON.stringify({ admin_notes })
			});
		},
		async reinstate(id: string): Promise<Profile> {
			return request(`/api/admin/profiles/${id}/reinstate`, { method: 'POST' });
		},
		async delete(
			id: string
		): Promise<{ deleted: { id: string; profile_number: string; first_name: string; last_name: string } }> {
			return request(`/api/admin/profiles/${id}/delete`, { method: 'POST' });
		}
	},

	requests: {
		async list(status?: string): Promise<DetailRequest[]> {
			const q = status ? `?status=${status}` : '';
			return request(`/api/admin/requests${q}`);
		},
		async approve(id: string, admin_notes?: string): Promise<void> {
			return request(`/api/admin/requests/${id}/approve`, {
				method: 'POST',
				body: JSON.stringify({ admin_notes })
			});
		},
		async reject(id: string, admin_notes?: string): Promise<DetailRequest> {
			return request(`/api/admin/requests/${id}/reject`, {
				method: 'POST',
				body: JSON.stringify({ admin_notes })
			});
		},
		async reinstate(id: string): Promise<DetailRequest> {
			return request(`/api/admin/requests/${id}/reinstate`, { method: 'POST' });
		},
		async delete(
			id: string
		): Promise<{ deleted: { id: string; request_number: string; status: string } }> {
			return request(`/api/admin/requests/${id}/delete`, { method: 'POST' });
		}
	},

	users: {
		async list(): Promise<User[]> {
			return request('/api/admin/users');
		},
		async promote(id: string): Promise<void> {
			return request(`/api/admin/users/${id}/promote`, { method: 'POST' });
		},
		async approve(id: string): Promise<User> {
			return request(`/api/admin/users/${id}/approve`, { method: 'POST' });
		},
		async unapprove(id: string): Promise<User> {
			return request(`/api/admin/users/${id}/unapprove`, { method: 'POST' });
		},
		async verifyEmail(userId: string): Promise<void> {
			return request(`/api/admin/users/${userId}/verify_email`, { method: 'POST' });
		},
		async resendVerification(userId: string): Promise<User> {
			return request(`/api/admin/users/${userId}/resend_verification`, { method: 'POST' });
		},
		async demote(id: string): Promise<User> {
			return request(`/api/admin/users/${id}/demote`, { method: 'POST' });
		},
		async revoke(id: string): Promise<User> {
			return request(`/api/admin/users/${id}/revoke`, { method: 'POST' });
		},
		async reinstate(id: string): Promise<User> {
			return request(`/api/admin/users/${id}/reinstate`, { method: 'POST' });
		},
		async suspend(id: string): Promise<User> {
			return request(`/api/admin/users/${id}/suspend`, { method: 'POST' });
		},
		async unsuspend(id: string): Promise<User> {
			return request(`/api/admin/users/${id}/unsuspend`, { method: 'POST' });
		},
		async delete(id: string): Promise<{ deleted: { uuid: string; user_id: string; email: string; is_admin: boolean } }> {
			return request(`/api/admin/users/${id}/delete`, { method: 'POST' });
		}
	},

	settings: {
		async get(): Promise<Setting[]> {
			return request('/api/admin/settings');
		},
		async update(settings: Record<string, string>): Promise<Setting[]> {
			return request('/api/admin/settings', {
				method: 'PUT',
				body: JSON.stringify(settings)
			});
		}
	},

	async broadcastEmail(payload: {
		subject: string;
		body_html: string;
		filter_verified_only?: boolean;
		filter_approved_only?: boolean;
		filter_admin_only?: boolean;
		filter_unapproved_only?: boolean;
		filter_unverified_only?: boolean;
		filter_mother_tongue?: string;
		filter_state?: string;
		filter_country?: string;
	}): Promise<{ sent: number; failed: number }> {
		return request('/api/admin/broadcast-email', {
			method: 'POST',
			body: JSON.stringify(payload)
		});
	}
};
