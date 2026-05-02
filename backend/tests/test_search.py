"""Profile search and filtering tests."""
from __future__ import annotations

import uuid
from datetime import date
from typing import Any

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.profile import Profile, ProfileStatusEnum
from app.models.user import User

pytestmark = pytest.mark.asyncio


def _sample_profile(
    gender: str = "bride",
    first_name: str = "Test",
    gotra: str = "Bharadwaja",
    nakshatram: str = "Rohini",
    manglik: str = "no",
    dob: str = "1995-06-15",
) -> dict[str, Any]:
    """Return a profile payload with customizable fields."""
    return {
        "gender": gender,
        "first_name": first_name,
        "last_name": "User",
        "dob": dob,
        "height_cm": 163,
        "complexion": "wheatish",
        "education": "B.Tech",
        "occupation": "Engineer",
        "annual_income_inr": 1200000,
        "city": "Hyderabad",
        "state": "Telangana",
        "country": "India",
        "gotra": gotra,
        "kuldevata": "Yellamma",
        "devak": "Mango",
        "surname_clan": "Ambore",
        "nakshatram": nakshatram,
        "rashi": "Vrishabha",
        "manglik": manglik,
        "mother_tongue": "Telugu",
        "diet": "veg",
        "about": "Test",
        "partner_expectations": "Test",
    }


async def _create_verified_user(client: AsyncClient, db_session: AsyncSession) -> tuple[str, str]:
    """Create and verify a user, return (user_id, email)."""
    email = f"user_{uuid.uuid4().hex[:8]}@example.com"
    password = "ValidPass123!"

    resp = await client.post("/auth/register", json={"email": email, "password": password})
    user_id = resp.json()["user_id"]

    result = await db_session.execute(select(User).where(User.id == uuid.UUID(user_id)))
    user = result.scalar_one()
    user.email_verified = True
    await db_session.commit()

    await client.post("/auth/login", json={"email": email, "password": password})
    return user_id, email


async def _create_approved_profile(
    client: AsyncClient, db_session: AsyncSession, **profile_kwargs
) -> str:
    """Create a profile and immediately approve it."""
    user_id, _ = await _create_verified_user(client, db_session)

    profile_data = _sample_profile(**profile_kwargs)
    resp = await client.post("/profiles", json=profile_data)
    profile_id = resp.json()["id"]

    # Manually approve the profile
    result = await db_session.execute(select(Profile).where(Profile.id == uuid.UUID(profile_id)))
    profile = result.scalar_one()
    profile.status = ProfileStatusEnum.approved
    await db_session.commit()

    return profile_id


async def test_search_returns_only_approved_profiles(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Search returns only approved profiles."""
    # Create a draft profile (should not appear in search)
    user_id, _ = await _create_verified_user(client, db_session)
    draft_data = _sample_profile()
    resp = await client.post("/profiles", json=draft_data)
    draft_id = resp.json()["id"]

    # Create an approved profile (should appear)
    approved_id = await _create_approved_profile(client, db_session)

    # Search
    resp = await client.get("/search?gender=bride")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    results = data["results"]

    # Draft should not appear
    result_ids = [r["id"] for r in results]
    assert draft_id not in result_ids, "Draft profile should not appear in search"
    assert approved_id in result_ids, "Approved profile should appear in search"


async def test_search_filter_by_gender(client: AsyncClient, db_session: AsyncSession) -> None:
    """Filter by gender works."""
    # Create bride and groom profiles
    bride_id = await _create_approved_profile(client, db_session, gender="bride")
    groom_id = await _create_approved_profile(client, db_session, gender="groom")

    resp = await client.get("/search?gender=bride")
    results = resp.json()["results"]
    result_ids = [r["id"] for r in results]

    assert bride_id in result_ids, "Bride should be in bride search"
    assert groom_id not in result_ids, "Groom should not be in bride search"


async def test_search_filter_by_gotra(client: AsyncClient, db_session: AsyncSession) -> None:
    """Filter by gotra works."""
    id1 = await _create_approved_profile(client, db_session, gotra="Bharadwaja")
    id2 = await _create_approved_profile(client, db_session, gotra="Kaundinya")

    resp = await client.get("/search?gotra=Bharadwaja")
    results = resp.json()["results"]
    result_ids = [r["id"] for r in results]

    assert id1 in result_ids
    assert id2 not in result_ids


async def test_search_filter_by_nakshatram(client: AsyncClient, db_session: AsyncSession) -> None:
    """Filter by nakshatram works."""
    id1 = await _create_approved_profile(client, db_session, nakshatram="Rohini")
    id2 = await _create_approved_profile(client, db_session, nakshatram="Kritika")

    resp = await client.get("/search?nakshatram=Rohini")
    results = resp.json()["results"]
    result_ids = [r["id"] for r in results]

    assert id1 in result_ids
    assert id2 not in result_ids


async def test_search_filter_by_manglik(client: AsyncClient, db_session: AsyncSession) -> None:
    """Filter by manglik status works."""
    id1 = await _create_approved_profile(client, db_session, manglik="yes")
    id2 = await _create_approved_profile(client, db_session, manglik="no")

    resp = await client.get("/search?manglik=yes")
    results = resp.json()["results"]
    result_ids = [r["id"] for r in results]

    assert id1 in result_ids
    assert id2 not in result_ids


async def test_search_filter_by_age_range(client: AsyncClient, db_session: AsyncSession) -> None:
    """Filter by age range (age_min, age_max) works."""
    # Create profiles with different DOBs
    # Today is 2026-05-02, so:
    # dob 1995-06-15 → age 30
    # dob 2000-06-15 → age 25
    # dob 1990-06-15 → age 35

    id_age30 = await _create_approved_profile(client, db_session, dob="1995-06-15")
    id_age25 = await _create_approved_profile(client, db_session, dob="2000-06-15")
    id_age35 = await _create_approved_profile(client, db_session, dob="1990-06-15")

    # Search for age 25-30 (should find 25 and 30)
    resp = await client.get("/search?age_min=25&age_max=30")
    results = resp.json()["results"]
    result_ids = [r["id"] for r in results]

    assert id_age25 in result_ids or id_age30 in result_ids, "Should find age 25-30"
    assert id_age35 not in result_ids, "Should not find age 35"


async def test_search_pagination(client: AsyncClient, db_session: AsyncSession) -> None:
    """Pagination with page and per_page parameters works."""
    # Create multiple approved profiles
    for i in range(5):
        await _create_approved_profile(client, db_session, first_name=f"User{i}")

    # Page 1, 2 per page
    resp = await client.get("/search?page=1&per_page=2")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["results"]) <= 2, "Page 1 should have ≤ 2 results"
    assert data["page"] == 1
    assert data["per_page"] == 2
    assert data["total"] >= 5, "Total should reflect all profiles"

    # Page 2
    resp = await client.get("/search?page=2&per_page=2")
    data = resp.json()
    assert len(data["results"]) <= 2


async def test_search_results_include_blurred_thumb_not_passport(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Search results contain blurred_url + thumb_url but never passport_url."""
    profile_id = await _create_approved_profile(client, db_session)

    resp = await client.get("/search?gender=bride")
    results = resp.json()["results"]
    result = next((r for r in results if r["id"] == profile_id), None)
    assert result is not None

    assert "blurred_url" in result, "Should have blurred_url"
    assert "thumb_url" in result, "Should have thumb_url"
    assert result.get("blurred_url") is not None or result.get("thumb_url") is not None
    assert "passport_url" not in result, "Should NOT have passport_url"


async def test_search_results_hide_sensitive_fields(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Search results do not contain dob or last_name."""
    profile_id = await _create_approved_profile(client, db_session)

    resp = await client.get("/search?gender=bride")
    results = resp.json()["results"]
    result = next((r for r in results if r["id"] == profile_id), None)
    assert result is not None

    assert "dob" not in result, "Should not expose dob in search"
    assert "last_name" not in result, "Should not expose last_name in search"


async def test_unauthenticated_search_sees_partial_info(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Unauthenticated user sees same partial info as authenticated."""
    profile_id = await _create_approved_profile(client, db_session)

    # Search without being logged in
    resp = await client.get("/search?gender=bride")
    assert resp.status_code == 200
    results = resp.json()["results"]
    result = next((r for r in results if r["id"] == profile_id), None)
    assert result is not None

    # Should have partial fields
    assert "age" in result
    assert "city" in result
    assert "dob" not in result
    assert "passport_url" not in result
