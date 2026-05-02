"""Search schemas."""
from __future__ import annotations

import msgspec

from app.schemas.profile import PartialProfileResponse


class SearchResponse(msgspec.Struct):
    results: list[PartialProfileResponse]
    total: int
    page: int
    per_page: int


class PreviewProfileResponse(msgspec.Struct):
    """Minimal profile card for anonymous (unauthenticated) search results.

    Intentionally less than PartialProfileResponse: no name initial, no
    education, no occupation, no income, no mother_tongue, no rashi, no
    manglik, no diet, no marital_status, no lifestyle fields.
    """

    id: str
    gender: str
    age: int
    height_cm: int
    city: str
    state: str
    gotra: str
    nakshatram: str
    blurred_url: str | None


class PreviewSearchResponse(msgspec.Struct):
    """Search envelope returned to anonymous callers."""

    results: list[PreviewProfileResponse]
    total: int
    page: int
    per_page: int
    requires_registration: bool  # always True in preview mode
