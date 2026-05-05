"""Regression coverage for wizard sections 6 (Location), 7 (About & Expectations),
8 (Photos), plus the combined PATCH that originally hit the enum-name save bug.

NOTE: All four scenarios are run inside a single pytest function. The reason
is a known Python 3.14 + pytest-asyncio + asyncpg interaction where a second
async test in the same session sees "Event loop is closed" while terminating
pooled asyncpg connections from the first test. Combining the scenarios into
one test keeps every interaction on the same event loop and makes cleanup
guarantees explicit. Each scenario is wrapped in its own try/finally so a
failure in one still tidies up its own data.
"""
from __future__ import annotations

import io
import uuid
from pathlib import Path
from typing import Any

import pytest
from httpx import AsyncClient
from PIL import Image
from sqlalchemy import select

from app.config import MEDIA_ROOT
from app.db import AsyncSessionLocal
from app.models.user import User
from app.services.settings import settings_service

pytestmark = pytest.mark.asyncio


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _unique_handle() -> str:
    return f"u{uuid.uuid4().hex[:7]}"


def _unique_phone() -> str:
    return f"+1{uuid.uuid4().int % 10**10:010d}"


def _sample_profile() -> dict[str, Any]:
    return {
        "gender": "bride",
        "first_name": "Test",
        "last_name": "User",
        "surname_clan": "Tester",
        "dob": "1995-06-15",
    }


async def _register_and_login(client: AsyncClient) -> str:
    """Register a fresh user, flip email_verified+is_approved in DB, log in.

    Returns the user UUID. The login sets a JWT cookie on `client` so all
    subsequent requests on this client are authenticated as the new user.
    """
    email = f"botsec_{uuid.uuid4().hex[:8]}@example.com"
    handle = _unique_handle()
    password = "TestPass123!"

    resp = await client.post(
        "/auth/register",
        json={
            "email": email,
            "password": password,
            "user_id": handle,
            "phone_number": _unique_phone(),
            "full_name": "Bottom Section Tester",
        },
    )
    assert resp.status_code == 201, resp.text
    user_uuid = resp.json()["uuid"]

    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).where(User.id == uuid.UUID(user_uuid)))
        user = result.scalar_one()
        user.email_verified = True
        user.is_approved = True
        await session.commit()

    resp = await client.post("/auth/login", json={"identifier": email, "password": password})
    assert resp.status_code == 200, resp.text
    return user_uuid


async def _delete_user(user_uuid: str) -> None:
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).where(User.id == uuid.UUID(user_uuid)))
        u = result.scalar_one_or_none()
        if u is not None:
            await session.delete(u)
            await session.commit()


def _make_jpeg() -> bytes:
    """Detailed JPEG large enough to clear photo_min_kb after compression.

    A solid colour compresses to ~1 KB (JPEG loves uniform regions). We need
    actual variance so the compressed passport size lands well above the
    25 KB floor — generate a pseudo-random RGB pattern via Pillow.
    """
    import random
    rng = random.Random(42)
    img = Image.new("RGB", (1200, 1200))
    pixels = img.load()
    for y in range(1200):
        for x in range(1200):
            pixels[x, y] = (
                rng.randint(80, 230),
                rng.randint(80, 230),
                rng.randint(80, 230),
            )
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=92)
    return buf.getvalue()


def _profile_view(resp_json: dict) -> dict:
    """GET /profiles/{id} returns the profile flat at top-level."""
    return resp_json["profile"] if "profile" in resp_json else resp_json


# ---------------------------------------------------------------------------
# The combined regression test
# ---------------------------------------------------------------------------


async def test_sections_6_7_8_save_and_retrieve(client: AsyncClient) -> None:
    # === Section 6: Location ================================================
    user_uuid = await _register_and_login(client)
    profile_id: str | None = None
    try:
        resp = await client.post("/profiles", json=_sample_profile())
        assert resp.status_code == 201, resp.text
        profile_id = resp.json()["id"]

        location = {
            "city": "Hyderabad",
            "state": "Telangana",
            "country": "India",
            "pin_code": "500001",
        }
        resp = await client.patch(f"/profiles/{profile_id}", json=location)
        assert resp.status_code == 200, f"Section 6 PATCH failed: {resp.text}"

        resp = await client.get(f"/profiles/{profile_id}")
        assert resp.status_code == 200
        body = _profile_view(resp.json())
        for k, v in location.items():
            assert body.get(k) == v, f"Section 6: {k} expected {v!r}, got {body.get(k)!r}"
    finally:
        if profile_id:
            await client.delete(f"/profiles/{profile_id}")
        await _delete_user(user_uuid)

    # === Section 7: About & Expectations ====================================
    user_uuid = await _register_and_login(client)
    profile_id = None
    try:
        resp = await client.post("/profiles", json=_sample_profile())
        assert resp.status_code == 201, resp.text
        profile_id = resp.json()["id"]

        about_payload = {
            "about": (
                "I enjoy cooking, hiking on weekends, and reading historical "
                "fiction. I value family, honesty, and a sense of humour."
            ),
            "partner_expectations": (
                "Looking for a kind, family-oriented partner who shares my "
                "interest in travel and is willing to grow together over time."
            ),
        }
        resp = await client.patch(f"/profiles/{profile_id}", json=about_payload)
        assert resp.status_code == 200, f"Section 7 PATCH failed: {resp.text}"

        resp = await client.get(f"/profiles/{profile_id}")
        assert resp.status_code == 200
        body = _profile_view(resp.json())
        assert body.get("about") == about_payload["about"]
        assert body.get("partner_expectations") == about_payload["partner_expectations"]
    finally:
        if profile_id:
            await client.delete(f"/profiles/{profile_id}")
        await _delete_user(user_uuid)

    # === Section 8: Photos ==================================================
    # Disable face detection — synthetic JPEGs aren't reliably detected.
    async with AsyncSessionLocal() as session:
        await settings_service.set("require_face_detection", False, session)

    user_uuid = await _register_and_login(client)
    profile_id = None
    photo_dir: Path | None = None
    try:
        resp = await client.post("/profiles", json=_sample_profile())
        assert resp.status_code == 201, resp.text
        profile_id = resp.json()["id"]

        files = {"data": ("test.jpg", _make_jpeg(), "image/jpeg")}
        resp = await client.post(f"/profiles/{profile_id}/photos", files=files)
        assert resp.status_code == 201, f"Photo upload failed: {resp.text}"
        photo = resp.json()
        photo_id = photo["id"]
        assert photo["is_primary"] is True
        assert photo["byte_size"] > 0
        assert photo["passport_url"].endswith("/passport.jpg")

        photo_dir = MEDIA_ROOT / "profiles" / profile_id / photo_id
        assert (photo_dir / "passport.jpg").exists()
        assert (photo_dir / "blurred.jpg").exists()
        assert (photo_dir / "thumb.jpg").exists()

        resp = await client.get(f"/profiles/{profile_id}")
        assert resp.status_code == 200
        body = resp.json()
        photos = body.get("photos") or _profile_view(body).get("photos") or []
        assert len(photos) == 1, f"Expected 1 photo, got {len(photos)}"
        assert photos[0]["id"] == photo_id
    finally:
        if profile_id:
            await client.delete(f"/profiles/{profile_id}")
            if photo_dir is not None:
                # The route should have removed on-disk variants — verify cleanup.
                assert not (photo_dir / "passport.jpg").exists(), "passport.jpg leaked"
                assert not (photo_dir / "blurred.jpg").exists(), "blurred.jpg leaked"
                assert not (photo_dir / "thumb.jpg").exists(), "thumb.jpg leaked"
        await _delete_user(user_uuid)
        async with AsyncSessionLocal() as session:
            await settings_service.set("require_face_detection", True, session)

    # === Combined PATCH (the original bug shape) ============================
    # Pre-fix: 500'd because DietEnum.non_veg serialised as 'non_veg' (name)
    # but Postgres diet_enum stores 'non-veg' (value). Same for BloodGroupEnum.
    user_uuid = await _register_and_login(client)
    profile_id = None
    try:
        resp = await client.post("/profiles", json=_sample_profile())
        assert resp.status_code == 201, resp.text
        profile_id = resp.json()["id"]

        combined = {
            "diet": "non-veg",
            "smokes": "no",
            "drinks": "no",
            "hobbies": "Reading and hiking",
            "blood_group": "A+",
            "city": "Pune",
            "state": "Maharashtra",
            "country": "India",
            "pin_code": "411001",
            "about": "Software engineer, family-oriented, enjoys travel.",
            "partner_expectations": "Looking for an honest, caring partner.",
        }
        resp = await client.patch(f"/profiles/{profile_id}", json=combined)
        assert resp.status_code == 200, f"Combined PATCH failed: {resp.text}"

        resp = await client.get(f"/profiles/{profile_id}")
        assert resp.status_code == 200
        body = _profile_view(resp.json())
        for k, v in combined.items():
            assert body.get(k) == v, f"Combined: {k} expected {v!r}, got {body.get(k)!r}"
    finally:
        if profile_id:
            await client.delete(f"/profiles/{profile_id}")
        await _delete_user(user_uuid)
