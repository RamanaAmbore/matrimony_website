"""Tests that verify the app structure without needing a running database."""
import pytest


def test_app_imports() -> None:
    """App module tree imports without error."""
    from app.main import app
    assert app is not None


def test_all_routes_registered() -> None:
    """Verify all required API routes are registered."""
    from app.main import app

    paths = {route.path for route in app.routes if hasattr(route, "path")}

    required = {
        "/health",
        "/auth/register",
        "/auth/login",
        "/auth/logout",
        "/auth/verify-email",
        "/auth/me",
        "/profiles",
        "/profiles/{profile_id:str}",
        "/profiles/{profile_id:str}/submit",
        "/profiles/{profile_id:str}/photos",
        "/profiles/{profile_id:str}/photos/{photo_id:str}",
        "/profiles/{profile_id:str}/photos/{photo_id:str}/primary",
        "/profiles/{profile_id:str}/request",
        "/requests/mine",
        "/search",
        "/admin/profiles",
        "/admin/profiles/{profile_id:str}/approve",
        "/admin/profiles/{profile_id:str}/reject",
        "/admin/requests",
        "/admin/requests/{request_id:str}/approve",
        "/admin/requests/{request_id:str}/reject",
        "/admin/users",
        "/admin/users/{user_id:str}/promote",
        "/admin/settings",
        "/admin/stats",
        "/media/{file_path:path}",
    }

    missing = required - paths
    assert not missing, f"Missing routes: {missing}"


def test_models_import() -> None:
    """All ORM models import cleanly."""
    from app.models import Base, User, Profile, Photo, DetailRequest, Setting
    from app.models.profile import GenderEnum, ManglikEnum, DietEnum, ProfileStatusEnum
    from app.models.request import RequestStatusEnum

    assert User.__tablename__ == "users"
    assert Profile.__tablename__ == "profiles"
    assert Photo.__tablename__ == "photos"
    assert DetailRequest.__tablename__ == "detail_requests"
    assert Setting.__tablename__ == "settings"

    assert list(GenderEnum) == [GenderEnum.bride, GenderEnum.groom]
    assert ProfileStatusEnum.draft.value == "draft"
    assert ManglikEnum.unknown.value == "unknown"
    assert DietEnum.veg.value == "veg"


def test_services_import() -> None:
    """All service modules import cleanly."""
    from app.services.auth import hash_password, verify_password, generate_token
    from app.services.settings import settings_service, DEFAULT_SETTINGS
    from app.services.images import process_upload, PhotoValidationError

    assert "owner_email" in DEFAULT_SETTINGS
    assert DEFAULT_SETTINGS["photo_max_kb"] == 500
    assert DEFAULT_SETTINGS["require_face_detection"] is True

    pw = hash_password("testpassword")
    assert verify_password("testpassword", pw)
    assert not verify_password("wrongpassword", pw)

    token = generate_token()
    assert len(token) > 20


def test_photo_pipeline_rejects_garbage() -> None:
    """Photo pipeline raises PhotoValidationError on bad input."""
    from app.services.images import process_upload, PhotoValidationError
    from app.services.settings import settings_service

    with pytest.raises(PhotoValidationError):
        process_upload(b"not an image", "test.jpg")


def test_settings_service_defaults() -> None:
    """SettingsService returns defaults from DEFAULT_SETTINGS when not loaded."""
    from app.services.settings import SettingsService, DEFAULT_SETTINGS

    svc = SettingsService()
    assert svc.get_int("photo_max_kb") == 500
    assert svc.get_str("smtp_from") == "no-reply@marathakalyanam.com"
    assert svc.get_bool("require_face_detection") is True
    assert svc.get_int("upload_max_mb") == 10
