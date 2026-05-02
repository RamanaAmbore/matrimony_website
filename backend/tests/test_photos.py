"""Photo upload and management tests."""
from __future__ import annotations

import io
import uuid
from pathlib import Path
from typing import Any

import pytest
from httpx import AsyncClient
from PIL import Image
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import MEDIA_ROOT
from app.models.photo import Photo
from app.models.profile import Profile
from app.models.user import User
from app.services.images import PhotoValidationError, process_upload
from app.services.settings import settings_service

pytestmark = pytest.mark.asyncio


def _sample_profile() -> dict[str, Any]:
    """Return a valid profile creation payload."""
    return {
        "gender": "bride", "first_name": "Test", "last_name": "User",
        "dob": "1995-06-15", "height_cm": 163, "complexion": "wheatish",
        "education": "B.Tech", "occupation": "Engineer", "annual_income_inr": 1200000,
        "city": "Hyderabad", "state": "Telangana", "country": "India",
        "gotra": "Bharadwaja", "kuldevata": "Yellamma", "devak": "Mango",
        "surname_clan": "Ambore", "nakshatram": "Rohini", "rashi": "Vrishabha",
        "manglik": "no", "mother_tongue": "Telugu", "diet": "veg",
        "about": "Test", "partner_expectations": "Test",
    }


async def _create_verified_user(client: AsyncClient, db_session: AsyncSession) -> str:
    """Create and verify a user, return user_id."""
    email = f"user_{uuid.uuid4().hex[:8]}@example.com"
    resp = await client.post("/auth/register", json={"email": email, "password": "ValidPass123!"})
    user_id = resp.json()["user_id"]
    result = await db_session.execute(select(User).where(User.id == uuid.UUID(user_id)))
    user = result.scalar_one()
    user.email_verified = True
    await db_session.commit()
    await client.post("/auth/login", json={"email": email, "password": "ValidPass123!"})
    return user_id


async def _create_profile(client: AsyncClient) -> str:
    """Create a profile and return its ID."""
    resp = await client.post("/profiles", json=_sample_profile())
    return resp.json()["id"]


def _create_test_image(w: int = 800, h: int = 1000, face: bool = True) -> bytes:
    """Create test image with optional synthetic face."""
    img = Image.new("RGB", (w, h), color="white")
    pixels = img.load()
    if face:
        cx, cy, r = w // 2, h // 4, 80
        for x in range(w):
            for y in range(h):
                if (x - cx) ** 2 + (y - cy) ** 2 <= r ** 2:
                    pixels[x, y] = (100, 150, 200)
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


def test_process_upload_valid_portrait_image() -> None:
    """Valid 800×1000 portrait with face accepted."""
    img_bytes = _create_test_image(800, 1000, face=True)
    p_bytes, b_bytes, t_bytes = process_upload(img_bytes, "test.jpg")
    assert len(p_bytes) > 0 and len(b_bytes) > 0 and len(t_bytes) > 0
    assert len(p_bytes) <= 500 * 1024


def test_process_upload_rejects_landscape() -> None:
    """Landscape 1000×600 photo rejected."""
    img_bytes = _create_test_image(1000, 600, face=True)
    with pytest.raises(PhotoValidationError):
        process_upload(img_bytes, "landscape.jpg")


def test_process_upload_rejects_small_face() -> None:
    """Image with face area too small rejected."""
    img = Image.new("RGB", (800, 1000), color="white")
    pixels = img.load()
    cx, cy, r = 400, 250, 10
    for x in range(800):
        for y in range(1000):
            if (x - cx) ** 2 + (y - cy) ** 2 <= r ** 2:
                pixels[x, y] = (100, 150, 200)
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    with pytest.raises(PhotoValidationError):
        process_upload(buf.getvalue(), "tiny_face.jpg")


def test_process_upload_rejects_no_face() -> None:
    """Image with no detected face rejected."""
    img_bytes = _create_test_image(800, 1000, face=False)
    with pytest.raises(PhotoValidationError):
        process_upload(img_bytes, "no_face.jpg")


def test_process_upload_compresses_large_file() -> None:
    """Large image compressed to ≤ 500 KB."""
    img = Image.new("RGB", (4000, 5000), color="white")
    pixels = img.load()
    cx, cy, r = 2000, 1250, 300
    for x in range(4000):
        for y in range(5000):
            if (x - cx) ** 2 + (y - cy) ** 2 <= r ** 2:
                pixels[x, y] = (100, 150, 200)
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=95)
    img_bytes = buf.getvalue()
    assert len(img_bytes) > 500 * 1024
    p_bytes, _, _ = process_upload(img_bytes, "large.jpg")
    assert len(p_bytes) <= 500 * 1024


def test_process_upload_rejects_non_image_file() -> None:
    """Non-image file with .jpg extension rejected."""
    with pytest.raises(PhotoValidationError):
        process_upload(b"not an image", "fake.jpg")


async def test_photo_upload_http_multipart(client: AsyncClient, db_session: AsyncSession) -> None:
    """HTTP multipart upload creates 3 files on disk."""
    await _create_verified_user(client, db_session)
    profile_id = await _create_profile(client)
    img_bytes = _create_test_image(800, 1000, face=True)
    resp = await client.post(
        f"/profiles/{profile_id}/photos",
        files={"data": ("portrait.jpg", io.BytesIO(img_bytes), "image/jpeg")},
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()
    photo_id = data["id"]
    photo_dir = MEDIA_ROOT / "profiles" / profile_id / photo_id
    assert (photo_dir / "passport.jpg").exists()
    assert (photo_dir / "blurred.jpg").exists()
    assert (photo_dir / "thumb.jpg").exists()
    assert data["passport_url"] and data["blurred_url"] and data["thumb_url"]


async def test_photo_byte_size_matches_passport(client: AsyncClient, db_session: AsyncSession) -> None:
    """Photo byte_size field matches actual passport.jpg size."""
    await _create_verified_user(client, db_session)
    profile_id = await _create_profile(client)
    img_bytes = _create_test_image(800, 1000, face=True)
    resp = await client.post(
        f"/profiles/{profile_id}/photos",
        files={"data": ("portrait.jpg", io.BytesIO(img_bytes), "image/jpeg")},
    )
    data = resp.json()
    photo_id = data["id"]
    photo_dir = MEDIA_ROOT / "profiles" / profile_id / photo_id
    actual_size = (photo_dir / "passport.jpg").stat().st_size
    assert data["byte_size"] == actual_size


async def test_delete_photo_removes_all_files(client: AsyncClient, db_session: AsyncSession) -> None:
    """Deleting a photo removes all 3 variant files from disk."""
    await _create_verified_user(client, db_session)
    profile_id = await _create_profile(client)
    img_bytes = _create_test_image(800, 1000, face=True)
    resp = await client.post(
        f"/profiles/{profile_id}/photos",
        files={"data": ("portrait.jpg", io.BytesIO(img_bytes), "image/jpeg")},
    )
    photo_id = resp.json()["id"]
    photo_dir = MEDIA_ROOT / "profiles" / profile_id / photo_id
    resp = await client.delete(f"/profiles/{profile_id}/photos/{photo_id}")
    assert resp.status_code == 204
    assert not (photo_dir / "passport.jpg").exists()
    assert not (photo_dir / "blurred.jpg").exists()
    assert not (photo_dir / "thumb.jpg").exists()


async def test_cannot_exceed_photos_per_profile_limit(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Cannot upload more than photos_max_per_profile."""
    await _create_verified_user(client, db_session)
    profile_id = await _create_profile(client)
    settings_service._cache["photos_max_per_profile"] = 2
    img_bytes = _create_test_image(800, 1000, face=True)
    for i in range(2):
        resp = await client.post(
            f"/profiles/{profile_id}/photos",
            files={"data": (f"photo{i}.jpg", io.BytesIO(img_bytes), "image/jpeg")},
        )
        assert resp.status_code == 201
    resp = await client.post(
        f"/profiles/{profile_id}/photos",
        files={"data": ("photo3.jpg", io.BytesIO(img_bytes), "image/jpeg")},
    )
    assert resp.status_code == 409
    assert resp.json()["detail"]["code"] == "photo_limit"


async def test_mark_primary_unsets_previous_primary(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Setting a photo as primary unsets the previous primary."""
    await _create_verified_user(client, db_session)
    profile_id = await _create_profile(client)
    img_bytes = _create_test_image(800, 1000, face=True)
    photo_ids = []
    for i in range(2):
        resp = await client.post(
            f"/profiles/{profile_id}/photos",
            files={"data": (f"photo{i}.jpg", io.BytesIO(img_bytes), "image/jpeg")},
        )
        photo_ids.append(resp.json()["id"])
    result = await db_session.execute(select(Photo).where(Photo.id == uuid.UUID(photo_ids[0])))
    photo1 = result.scalar_one()
    assert photo1.is_primary is True
    resp = await client.post(f"/profiles/{profile_id}/photos/{photo_ids[1]}/primary")
    assert resp.status_code == 200
    await db_session.refresh(photo1)
    result = await db_session.execute(select(Photo).where(Photo.id == uuid.UUID(photo_ids[1])))
    photo2 = result.scalar_one()
    assert photo1.is_primary is False and photo2.is_primary is True


async def test_first_photo_is_automatically_primary(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """First uploaded photo is automatically marked as primary."""
    await _create_verified_user(client, db_session)
    profile_id = await _create_profile(client)
    img_bytes = _create_test_image(800, 1000, face=True)
    resp = await client.post(
        f"/profiles/{profile_id}/photos",
        files={"data": ("first.jpg", io.BytesIO(img_bytes), "image/jpeg")},
    )
    assert resp.status_code == 201 and resp.json()["is_primary"] is True
