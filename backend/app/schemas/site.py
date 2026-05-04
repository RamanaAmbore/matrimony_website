"""Site info schemas."""
from __future__ import annotations

import msgspec


class SiteInfoResponse(msgspec.Struct):
    """Public site configuration returned by GET /site/info."""

    is_prod: bool
    site_url: str
