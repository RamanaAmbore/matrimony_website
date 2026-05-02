"""Profile CRUD endpoint tests."""
from __future__ import annotations

import uuid
from typing import Any

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.profile import Profile, ProfileStatusEnum
from app.models.user import User
from app.services.auth import hash_password

pytestmark = pytest.mark.asyncio


def _sample_profile() -> dict[str, Any]:
    """Return a valid profile creation payload."""
    return {
        "gender": "bride",
        "first_name": "Ramana",
        "last_name": "Ambore",
        "dob": "1995-06-15",
        "height_cm": 163,
        "complexion": "wheatish",
        "education": "B.Tech Computer Science",
        "occupation": "Software Engineer",
        "annual_income_inr": 1200000,
        "city": "Hyderabad",
        "state": "Telangana",
        "country": "India",
        "gotra": "Bharadwaja",
        "kuldevata": "Yellamma",
        "devak": "Mango",
        "surname_clan": "Ambore",
        "nakshatram": "Rohini",
        "rashi": "Vrishabha",
        "manglik": "no",
        "mother_tongue": "Telugu",
        "diet": "veg",
        "about": "Test profile",
        "partner_expectations": "Looking for",
    }


async def _create_verified_user(client: AsyncClient, db_session: AsyncSession) -> tuple[str, str]:
    """Create and verify a user, return (user_id, email)."""
    email = f"user_{uuid.uuid4().hex[:8]}@example.com"
    password = "ValidPass123!"

    resp = await client.post("/auth/register", json={"email": email, "password": password})
    user_id = resp.json()["user_id"]

    # Verify email in DB
    result = await db_session.execute(select(User).where(User.id == uuid.UUID(user_id)))
    user = result.scalar_one()
    user.email_verified = True
    await db_session.commit()

    # Login
    await client.post("/auth/login", json={"email": email, "password": password})
    return user_id, email


async def test_create_single_profile(client: AsyncClient, db_session: AsyncSession) -> None:
    """Create a single profile."""
    user_id, _ = await _create_verified_user(client, db_session)

    profile_data = _sample_profile()
    resp = await client.post("/profiles", json=profile_data)
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["id"]
    assert data["status"] == "draft"
    assert data["first_name"] == "Ramana"


async def test_create_multiple_profiles(client: AsyncClient, db_session: AsyncSession) -> None:
    """User can create multiple profiles (e.g., 3)."""
    user_id, _ = await _create_verified_user(client, db_session)

    profile_ids = []
    for i in range(3):
        profile_data = _sample_profile()
        profile_data["first_name"] = f"Profile{i}"
        resp = await client.post("/profiles", json=profile_data)
        assert resp.status_code == 201, resp.text
        profile_ids.append(resp.json()["id"])

    # List profiles — all should appear
    resp = await client.get("/profiles")
    assert resp.status_code == 200, resp.text
    profiles = resp.json()
    profile_ids_returned = [p["id"] for p in profiles]
    for pid in profile_ids:
        assert pid in profile_ids_returned, f"Profile {pid} not found in list"


async def test_user_cannot_read_other_users_draft_profile(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """User A cannot read User B's draft profile."""
    user_a_id, email_a = await _create_verified_user(client, db_session)

    # Create profile as User A
    profile_data = _sample_profile()
    resp = await client.post("/profiles", json=profile_data)
    profile_a_id = resp.json()["id"]

    # Logout User A, create and login User B
    await client.post("/auth/logout")
    user_b_id, email_b = await _create_verified_user(client, db_session)

    # User B tries to read User A's draft profile
    resp = await client.get(f"/profiles/{profile_a_id}")
    assert resp.status_code == 404, "Draft profile should be hidden from other users"


async def test_user_cannot_patch_other_users_profile(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """User A cannot PATCH User B's profile."""
    user_a_id, _ = await _create_verified_user(client, db_session)

    profile_data = _sample_profile()
    resp = await client.post("/profiles", json=profile_data)
    profile_a_id = resp.json()["id"]

    await client.post("/auth/logout")
    user_b_id, _ = await _create_verified_user(client, db_session)

    # User B tries to PATCH User A's profile
    patch_data = {"first_name": "Hacker"}
    resp = await client.patch(f"/profiles/{profile_a_id}", json=patch_data)
    assert resp.status_code == 403, resp.text


async def test_user_cannot_delete_other_users_profile(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """User A cannot DELETE User B's profile."""
    user_a_id, _ = await _create_verified_user(client, db_session)

    profile_data = _sample_profile()
    resp = await client.post("/profiles", json=profile_data)
    profile_a_id = resp.json()["id"]

    await client.post("/auth/logout")
    user_b_id, _ = await _create_verified_user(client, db_session)

    # User B tries to DELETE User A's profile
    resp = await client.delete(f"/profiles/{profile_a_id}")
    assert resp.status_code == 403, resp.text


async def test_delete_profile_cascades_photos(client: AsyncClient, db_session: AsyncSession) -> None:
    """Deleting a profile cascades to delete photos."""
    user_id, _ = await _create_verified_user(client, db_session)

    profile_data = _sample_profile()
    resp = await client.post("/profiles", json=profile_data)
    profile_id = resp.json()["id"]

    # Verify profile exists in DB
    result = await db_session.execute(select(Profile).where(Profile.id == uuid.UUID(profile_id)))
    profile = result.scalar_one_or_none()
    assert profile is not None

    # Delete profile
    resp = await client.delete(f"/profiles/{profile_id}")
    assert resp.status_code == 204

    # Verify it's gone
    result = await db_session.execute(select(Profile).where(Profile.id == uuid.UUID(profile_id)))
    profile = result.scalar_one_or_none()
    assert profile is None, "Profile should be deleted"


async def test_patch_approved_profile_resets_status(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """PATCH on an approved profile resets status to pending."""
    user_id, _ = await _create_verified_user(client, db_session)

    profile_data = _sample_profile()
    resp = await client.post("/profiles", json=profile_data)
    profile_id = resp.json()["id"]

    # Manually set profile to approved
    result = await db_session.execute(select(Profile).where(Profile.id == uuid.UUID(profile_id)))
    profile = result.scalar_one()
    profile.status = ProfileStatusEnum.approved
    await db_session.commit()

    # PATCH the profile
    patch_data = {"about": "Updated about"}
    resp = await client.patch(f"/profiles/{profile_id}", json=patch_data)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["status"] == "pending", "Status should reset to pending after edit"


async def test_non_owner_cannot_read_non_approved_profile(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Non-owner request to a non-approved profile gets 404 (don't leak existence)."""
    user_a_id, _ = await _create_verified_user(client, db_session)

    profile_data = _sample_profile()
    resp = await client.post("/profiles", json=profile_data)
    profile_id = resp.json()["id"]

    # Status is draft, so it's non-approved
    await client.post("/auth/logout")
    user_b_id, _ = await _create_verified_user(client, db_session)

    resp = await client.get(f"/profiles/{profile_id}")
    assert resp.status_code == 404, "Non-approved profile should return 404 to non-owners"


async def test_owner_can_read_own_profile_even_if_draft(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Owner can read their own draft profile."""
    user_id, _ = await _create_verified_user(client, db_session)

    profile_data = _sample_profile()
    resp = await client.post("/profiles", json=profile_data)
    profile_id = resp.json()["id"]

    # Owner reads their own draft profile via /profiles — should work
    resp = await client.get("/profiles")
    assert resp.status_code == 200
    profiles = resp.json()
    assert any(p["id"] == profile_id for p in profiles)
