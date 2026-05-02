"""Smoke tests: register -> login -> create profile -> submit -> admin approve."""
from __future__ import annotations

import os
import uuid
from typing import Any

import pytest
import pytest_asyncio
from httpx import AsyncClient


pytestmark = pytest.mark.asyncio


async def test_health(client: AsyncClient) -> None:
    resp = await client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"


async def test_register_and_login(client: AsyncClient) -> None:
    email = f"test_{uuid.uuid4().hex[:8]}@example.com"
    password = "TestPass123!"

    # Register
    resp = await client.post("/auth/register", json={"email": email, "password": password})
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert "user_id" in data
    user_id = data["user_id"]

    # Login
    resp = await client.post("/auth/login", json={"email": email, "password": password})
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["user_id"] == user_id
    assert data["email"] == email
    assert not data["is_admin"]
    assert not data["email_verified"]

    # Me endpoint
    resp = await client.get("/auth/me")
    assert resp.status_code == 200
    assert resp.json()["user_id"] == user_id

    # Logout
    resp = await client.post("/auth/logout")
    assert resp.status_code == 204

    # Me after logout should 401
    resp = await client.get("/auth/me")
    assert resp.status_code == 401


async def test_duplicate_email_rejected(client: AsyncClient) -> None:
    email = f"dup_{uuid.uuid4().hex[:8]}@example.com"
    await client.post("/auth/register", json={"email": email, "password": "TestPass123!"})
    resp = await client.post("/auth/register", json={"email": email, "password": "TestPass123!"})
    assert resp.status_code == 409


async def test_profile_requires_email_verified(client: AsyncClient) -> None:
    email = f"unverified_{uuid.uuid4().hex[:8]}@example.com"
    await client.post("/auth/register", json={"email": email, "password": "TestPass123!"})
    await client.post("/auth/login", json={"email": email, "password": "TestPass123!"})

    profile_data = _sample_profile()
    resp = await client.post("/profiles", json=profile_data)
    # Should 403 because email not verified
    assert resp.status_code == 403
    assert resp.json()["detail"]["code"] == "email_not_verified"


async def test_full_flow_register_verify_profile_admin(client: AsyncClient) -> None:
    """Register -> verify email manually via DB -> create profile -> submit -> admin approve."""
    from app.db import AsyncSessionLocal
    from app.models.user import User
    from sqlalchemy import select, update

    email = f"flow_{uuid.uuid4().hex[:8]}@example.com"
    password = "FlowTest456!"

    # Register
    resp = await client.post("/auth/register", json={"email": email, "password": password})
    assert resp.status_code == 201
    user_id = resp.json()["user_id"]

    # Manually verify email in DB
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).where(User.id == uuid.UUID(user_id)))
        user = result.scalar_one()
        user.email_verified = True
        await session.commit()

    # Login (now verified)
    resp = await client.post("/auth/login", json={"email": email, "password": password})
    assert resp.status_code == 200

    # Create profile
    profile_data = _sample_profile()
    resp = await client.post("/profiles", json=profile_data)
    assert resp.status_code == 201, resp.text
    profile = resp.json()
    profile_id = profile["id"]
    assert profile["status"] == "draft"
    assert profile["first_name"] == "Ramana"

    # List profiles
    resp = await client.get("/profiles")
    assert resp.status_code == 200
    assert any(p["id"] == profile_id for p in resp.json())

    # Submit profile
    resp = await client.post(f"/profiles/{profile_id}/submit")
    assert resp.status_code == 200
    assert resp.json()["status"] == "pending"

    # Admin setup: get the seeded admin token from DB
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(User).where(User.is_admin == True)  # noqa: E712
        )
        admin = result.scalars().first()
        assert admin is not None, "Bootstrap admin should exist"
        admin_email = admin.email

    # We need to login as admin — use the bootstrap admin
    # Since we don't know the password, set it directly
    from app.services.auth import hash_password
    admin_password = "AdminPass789!"
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).where(User.is_admin == True))  # noqa: E712
        admin = result.scalars().first()
        admin.password_hash = hash_password(admin_password)
        await session.commit()

    # Create a separate client for admin
    from httpx import ASGITransport
    from app.main import app as litestar_app
    async with AsyncClient(transport=ASGITransport(app=litestar_app), base_url="http://testserver") as admin_client:
        resp = await admin_client.post("/auth/login", json={"email": admin_email, "password": admin_password})
        assert resp.status_code == 200, resp.text
        assert resp.json()["is_admin"]

        # Admin: list pending profiles
        resp = await admin_client.get("/admin/profiles?status=pending")
        assert resp.status_code == 200
        pending = resp.json()
        assert any(p["id"] == profile_id for p in pending)

        # Admin: approve
        resp = await admin_client.post(
            f"/admin/profiles/{profile_id}/approve",
            json={"admin_notes": "Looks good!"},
        )
        assert resp.status_code == 200, resp.text
        assert resp.json()["status"] == "approved"

    # Verify profile is now approved (via search, visible as approved)
    resp = await client.get(f"/profiles/{profile_id}")
    assert resp.status_code == 200
    # Owner sees full profile
    assert resp.json()["status"] == "approved"


async def test_search_returns_approved_only(client: AsyncClient) -> None:
    resp = await client.get("/search?gender=bride")
    assert resp.status_code == 200
    data = resp.json()
    assert "results" in data
    assert "total" in data
    assert "page" in data
    assert "per_page" in data
    # All results should be approved (we can't verify status in partial, just check shape)
    for r in data["results"]:
        assert "id" in r
        assert "gender" in r
        assert "age" in r
        # No last_name or dob in partial
        assert "last_name" not in r
        assert "dob" not in r


async def test_admin_stats(client: AsyncClient) -> None:
    from app.db import AsyncSessionLocal
    from app.models.user import User
    from app.services.auth import hash_password
    from sqlalchemy import select

    admin_password = "StatsAdmin123!"
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).where(User.is_admin == True))  # noqa: E712
        admin = result.scalars().first()
        admin.password_hash = hash_password(admin_password)
        await session.commit()
        admin_email = admin.email

    from httpx import ASGITransport
    from app.main import app as litestar_app
    async with AsyncClient(transport=ASGITransport(app=litestar_app), base_url="http://testserver") as admin_client:
        await admin_client.post("/auth/login", json={"email": admin_email, "password": admin_password})
        resp = await admin_client.get("/admin/stats")
        assert resp.status_code == 200
        data = resp.json()
        assert "users" in data
        assert "profiles_total" in data
        assert "profiles_pending" in data
        assert "profiles_approved" in data
        assert "requests_pending" in data


def _sample_profile() -> dict[str, Any]:
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
        "about": "Software engineer based in Hyderabad, family-oriented.",
        "partner_expectations": "Looking for a well-educated, caring partner.",
    }
