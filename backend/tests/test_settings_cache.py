"""Settings service cache tests."""
from __future__ import annotations

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.setting import Setting
from app.services.settings import SettingsService, DEFAULT_SETTINGS

pytestmark = pytest.mark.asyncio


async def test_settings_service_returns_defaults_when_not_loaded() -> None:
    """SettingsService returns defaults when cache is empty."""
    svc = SettingsService()

    assert svc.get_int("photo_max_kb") == 500
    assert svc.get_str("smtp_from") == "no-reply@marathakalyanam.com"
    assert svc.get_bool("require_face_detection") is True


async def test_settings_service_cache_reflects_writes(
    db_session: AsyncSession,
) -> None:
    """Cache reflects writes immediately."""
    svc = SettingsService()

    # Load from DB (empty, will use defaults)
    await svc.load(db_session)

    # Set a value
    await svc.set("photo_max_kb", 600, db_session)

    # Read it back
    assert svc.get_int("photo_max_kb") == 600


async def test_get_int_typed_accessor(db_session: AsyncSession) -> None:
    """get_int returns correct type and respects defaults."""
    svc = SettingsService()
    await svc.load(db_session)

    value = svc.get_int("photos_max_per_profile", 5)
    assert isinstance(value, int)
    assert value > 0


async def test_get_bool_typed_accessor(db_session: AsyncSession) -> None:
    """get_bool returns correct type."""
    svc = SettingsService()
    await svc.load(db_session)

    value = svc.get_bool("require_face_detection", False)
    assert isinstance(value, bool)
    assert value is True  # Default is True


async def test_get_str_typed_accessor(db_session: AsyncSession) -> None:
    """get_str returns correct type and respects defaults."""
    svc = SettingsService()
    await svc.load(db_session)

    value = svc.get_str("smtp_from", "default@example.com")
    assert isinstance(value, str)
    assert len(value) > 0


async def test_settings_service_seed_defaults(db_session: AsyncSession) -> None:
    """Seed defaults creates all default settings in DB."""
    svc = SettingsService()

    await svc.seed_defaults(db_session)

    # Verify all defaults were seeded
    result = await db_session.execute(select(Setting))
    settings = result.scalars().all()
    setting_keys = {s.key for s in settings}

    for key in DEFAULT_SETTINGS.keys():
        assert key in setting_keys, f"Setting {key} should be seeded"


async def test_set_many_batches_updates(db_session: AsyncSession) -> None:
    """set_many updates multiple settings at once."""
    svc = SettingsService()
    await svc.load(db_session)

    updates = {
        "photo_max_kb": 750,
        "upload_max_mb": 15,
        "photos_max_per_profile": 3,
    }

    await svc.set_many(updates, db_session)

    assert svc.get_int("photo_max_kb") == 750
    assert svc.get_int("upload_max_mb") == 15
    assert svc.get_int("photos_max_per_profile") == 3


async def test_all_public_masks_sensitive_keys(db_session: AsyncSession) -> None:
    """all_public masks sensitive keys like smtp_password."""
    svc = SettingsService()
    await svc.load(db_session)

    # Set an actual password
    await svc.set("smtp_password", "secret123", db_session)

    public = svc.all_public()

    assert public["smtp_password"] == "***", "Password should be masked"
    assert public["photo_max_kb"] == 500, "Non-sensitive should be visible"


async def test_get_bool_parses_string_values(db_session: AsyncSession) -> None:
    """get_bool correctly parses string representations."""
    svc = SettingsService()

    # Test string parsing
    svc._cache["test_bool_true"] = "true"
    assert svc.get_bool("test_bool_true") is True

    svc._cache["test_bool_yes"] = "yes"
    assert svc.get_bool("test_bool_yes") is True

    svc._cache["test_bool_1"] = "1"
    assert svc.get_bool("test_bool_1") is True

    svc._cache["test_bool_false"] = "false"
    assert svc.get_bool("test_bool_false") is False


async def test_get_float_returns_correct_type(db_session: AsyncSession) -> None:
    """get_float returns float type."""
    svc = SettingsService()

    svc._cache["test_float"] = "3.14"
    value = svc.get_float("test_float")
    assert isinstance(value, float)
    assert 3.1 < value < 3.2
