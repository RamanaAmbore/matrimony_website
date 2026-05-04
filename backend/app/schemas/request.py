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
    request_number: str | None = None
    requester_email: str | None = None
    requester_name: str | None = None
    profile_number: str | None = None
    profile_first_name: str | None = None
    profile_last_name: str | None = None
    profile_gender: str | None = None
    profile_city: str | None = None
