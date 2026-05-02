"""Detail request schemas."""
from __future__ import annotations

import msgspec


class CreateDetailRequest(msgspec.Struct, kw_only=True):
    message: str | None = None


class DetailRequestResponse(msgspec.Struct):
    id: str
    requester_user_id: str
    profile_id: str
    status: str
    message: str | None
    admin_notes: str | None
    responded_at: str | None
    created_at: str
