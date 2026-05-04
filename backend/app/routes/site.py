"""Public site-info route."""
from __future__ import annotations

from litestar import Controller, get

from app.schemas.site import SiteInfoResponse
from app.services.settings import settings_service


class SiteController(Controller):
    path = "/site"
    tags = ["site"]

    @get("/info", tags=["site"])
    async def get_site_info(self) -> SiteInfoResponse:
        """Return public site configuration (no auth required)."""
        return SiteInfoResponse(
            is_prod=settings_service.get_bool("is_prod", False),
            site_url=settings_service.get_str("site_url", "https://marathakalyanam.com"),
        )
