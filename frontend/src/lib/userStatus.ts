import type { User } from '$lib/api';

export type UserStatus = 'pending' | 'approved' | 'revoked';

export function userStatus(u: Pick<User, 'email_verified' | 'is_approved' | 'is_revoked'>): UserStatus {
	if (u.is_revoked) return 'revoked';
	return u.email_verified && u.is_approved ? 'approved' : 'pending';
}
