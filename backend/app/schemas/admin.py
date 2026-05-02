"""Admin schemas."""
from __future__ import annotations

import msgspec


class AdminApproveProfile(msgspec.Struct, kw_only=True):
    admin_notes: str | None = None


class AdminRejectProfile(msgspec.Struct, kw_only=True):
    admin_notes: str


class AdminApproveRequest(msgspec.Struct, kw_only=True):
    admin_notes: str | None = None


class AdminRejectRequest(msgspec.Struct, kw_only=True):
    admin_notes: str | None = None


class AdminStatsResponse(msgspec.Struct):
    users: int
    profiles_total: int
    profiles_pending: int
    profiles_approved: int
    requests_pending: int


class AdminUserResponse(msgspec.Struct):
    id: str
    email: str
    is_admin: bool
    email_verified: bool
    created_at: str
