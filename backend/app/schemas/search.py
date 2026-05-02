"""Search schemas."""
from __future__ import annotations

import msgspec

from app.schemas.profile import PartialProfileResponse


class SearchResponse(msgspec.Struct):
    results: list[PartialProfileResponse]
    total: int
    page: int
    per_page: int
