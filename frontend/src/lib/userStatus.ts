import type { User } from '$lib/api';

export type UserStatus = 'pending' | 'approved';

export function userStatus(u: Pick<User, 'email_verified' | 'is_approved'>): UserStatus {
	return u.email_verified && u.is_approved ? 'approved' : 'pending';
}
