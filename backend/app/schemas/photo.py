"""Photo schemas."""
from __future__ import annotations

import msgspec


class PhotoResponse(msgspec.Struct):
    id: str
    profile_id: str
    original_filename: str
    passport_url: str
    blurred_url: str
    thumb_url: str
    byte_size: int
    is_primary: bool
    created_at: str
