"""SettingsService — in-process cached runtime configuration from DB."""
from __future__ import annotations

import asyncio
import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.setting import Setting

# Default settings seeded on first startup
DEFAULT_SETTINGS: dict[str, Any] = {
    "owner_email": "admin.marathakalyanam@gmail.com",
    "smtp_host": "localhost",
    "smtp_port": 1025,
    "smtp_user": "",
    "smtp_password": "",
    "smtp_from": "no-reply@marathakalyanam.com",
    # Photo settings — balanced for storage vs functional quality.
    #
    # Functionality the photos actually serve:
    #   passport — admin reviews at 413×531; needs facial recognition
    #              clarity. JPEG q85-90 yields ~60-80 KB. 180 KB cap is
    #              comfortable headroom without bloat.
    #   blurred  — public-search obfuscation; Gaussian-blurred so
    #              entropy is low and JPEG compresses to ~25-40 KB
    #              easily. 50 KB cap.
    #   thumb    — 150×150 admin-grid avatar; typical 5-8 KB. 12 KB cap.
    #
    # Per profile (2 photos) ~ 240–500 KB on disk. 1000 active profiles
    # ≈ 0.5 GB total. That's the sweet spot for a small matrimony site
    # on cheap block storage without surprising the operator.
    #
    # Face detection is OFF by default — over-rejects on group/lifestyle/
    # poorly-lit phone shots; admins prefer manual judgement at review.
    #
    # All three output variants share the iterative JPEG quality-stepper
    # in services/images.py:_encode_jpeg.
    "photo_max_kb": 180,           # passport JPEG cap (413×531)
    "photo_min_kb": 12,            # passport JPEG floor — guards quality
    "photo_blur_max_kb": 50,       # blurred variant cap (≈600 wide, blurred)
    "photo_thumb_max_kb": 12,      # square 150×150 thumb cap
    # Two photo slots, two different crop targets:
    #   slot 1 (primary)  — passport-style face headshot at 413×531
    #   slot 2 (secondary) — full-body shot at 600×900 (taller aspect
    #                        keeps head-to-toe in frame)
    "photo_passport_width": 413,
    "photo_passport_height": 531,
    "photo_body_width": 600,
    "photo_body_height": 900,
    "photo_blur_width": 600,
    "photo_blur_radius": 14,
    "photo_thumb_size": 150,
    "photo_min_dimension_px": 600, # shortest source side; below pixelates on crop
    "photo_max_dimension_px": 3500,# longest source side; pre-downscale beyond this
    "photos_max_per_profile": 2,
    "upload_max_mb": 6,            # raw upload cap — covers 99% of phone photos
    "upload_min_kb": 20,           # raw upload floor — rejects thumbs / icons
    "require_face_detection": False,
    "require_admin_approval_for_profiles": True,
    "matrimony_tg_token": "",
    "matrimony_tg_chat_id": "",
    "matrimony_tg_enabled": True,
    "is_prod": False,
}

SENSITIVE_KEYS = {"smtp_password", "matrimony_tg_token"}


class SettingsService:
    """In-process cache for the settings table. Refresh on write."""

    def __init__(self) -> None:
        self._cache: dict[str, Any] = {}
        self._lock = asyncio.Lock()
        self._loaded = False

    async def load(self, session: AsyncSession) -> None:
        """Load all settings from DB into cache."""
        async with self._lock:
            rows = await session.execute(select(Setting))
            self._cache = {row.key: row.value for row in rows.scalars()}
            self._loaded = True

    async def ensure_loaded(self, session: AsyncSession) -> None:
        if not self._loaded:
            await self.load(session)

    def get(self, key: str, default: Any = None) -> Any:
        return self._cache.get(key, DEFAULT_SETTINGS.get(key, default))

    def get_str(self, key: str, default: str = "") -> str:
        return str(self.get(key, default))

    def get_int(self, key: str, default: int = 0) -> int:
        return int(self.get(key, default))

    def get_float(self, key: str, default: float = 0.0) -> float:
        return float(self.get(key, default))

    def get_bool(self, key: str, default: bool = False) -> bool:
        val = self.get(key, default)
        if isinstance(val, bool):
            return val
        if isinstance(val, str):
            return val.lower() in ("true", "1", "yes")
        return bool(val)

    async def set(self, key: str, value: Any, session: AsyncSession, updated_by: uuid.UUID | None = None) -> None:
        """Upsert a single setting and refresh cache."""
        existing = await session.get(Setting, key)
        if existing is None:
            setting = Setting(key=key, value=value, updated_by=updated_by)
            session.add(setting)
        else:
            existing.value = value
            existing.updated_by = updated_by
        async with self._lock:
            self._cache[key] = value

    async def set_many(self, updates: dict[str, Any], session: AsyncSession, updated_by: uuid.UUID | None = None) -> None:
        """Batch upsert settings."""
        for key, value in updates.items():
            await self.set(key, value, session, updated_by)

    def all_public(self) -> dict[str, Any]:
        """Return all settings, masking sensitive values."""
        merged = {**DEFAULT_SETTINGS, **self._cache}
        result = {}
        for k, v in merged.items():
            if k in SENSITIVE_KEYS:
                result[k] = "***" if v else ""
            else:
                result[k] = v
        return result

    def invalidate(self) -> None:
        """Force reload on next access."""
        self._loaded = False

    async def seed_defaults(self, session: AsyncSession) -> None:
        """Insert default settings if not present."""
        for key, value in DEFAULT_SETTINGS.items():
            existing = await session.get(Setting, key)
            if existing is None:
                session.add(Setting(key=key, value=value))
        await session.commit()
        await self.load(session)


# Global singleton
settings_service = SettingsService()
