"""Admin endpoints tests."""
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


def _sample_profile(**kwargs) -> dict[str, Any]:
    """Return a profile payload."""
    base = {
        "gender": "bride", "first_name": "Test", "last_name": "User",
        "dob": "1995-06-15", "height_cm": 163, "complexion": "wheatish",
        "education": "B.Tech", "occupation": "Engineer", "annual_income_inr": 1200000,
        "city": "Hyderabad", "state": "Telangana", "country": "India",
        "gotra": "Bharadwaja", "kuldevata": "Yellamma", "devak": "Mango",
        "surname_clan": "Ambore", "nakshatram": "Rohini", "rashi": "Vrishabha",
        "manglik": "no", "mother_tongue": "Telugu", "diet": "veg",
        "about": "Test", "partner_expectations": "Test",
    }
    base.update(kwargs)
    return base


async def _create_verified_user(client: AsyncClient, db_session: AsyncSession) -> tuple[str, str]:
    """Create and verify a user."""
    email = f"user_{uuid.uuid4().hex[:8]}@example.com"
    resp = await client.post("/auth/register", json={"email": email, "password": "ValidPass123!"})
    user_id = resp.json()["user_id"]
    result = await db_session.execute(select(User).where(User.id == uuid.UUID(user_id)))
    user = result.scalar_one()
    user.email_verified = True
    await db_session.commit()
    await client.post("/auth/login", json={"email": email, "password": "ValidPass123!"})
    return user_id, email


async def _get_admin(db_session: AsyncSession) -> tuple[str, str]:
    """Get the seeded admin user or create one."""
    result = await db_session.execute(select(User).where(User.is_admin == True))  # noqa: E712
    admin = result.scalars().first()
    if admin is None:
        admin = User(
            id=uuid.uuid4(), email="admin@test.com",
            password_hash=hash_password("AdminPass123!"),
            email_verified=True, is_admin=True,
        )
        db_session.add(admin)
        await db_session.commit()
    return str(admin.id), admin.email


async def _login_admin(client: AsyncClient, db_session: AsyncSession) -> None:
    """Login as admin."""
    admin_id, admin_email = await _get_admin(db_session)
    result = await db_session.execute(select(User).where(User.id == uuid.UUID(admin_id)))
    admin = result.scalar_one()
    admin.password_hash = hash_password("AdminPass123!")
    await db_session.commit()
    resp = await client.post(
        "/auth/login",
        json={"email": admin_email, "password": "AdminPass123!"},
    )
    assert resp.status_code == 200, f"Admin login failed: {resp.text}"


async def test_non_admin_gets_403_on_admin_endpoints(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Non-admin user gets 403 on /admin/* endpoints."""
    user_id, _ = await _create_verified_user(client, db_session)

    resp = await client.get("/admin/stats")
    assert resp.status_code == 403, resp.text
    assert resp.json()["detail"]["code"] == "forbidden"

    resp = await client.get("/admin/profiles")
    assert resp.status_code == 403

    resp = await client.get("/admin/settings")
    assert resp.status_code == 403


async def test_admin_stats_returns_expected_keys(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """GET /admin/stats returns expected keys with correct counts."""
    await _login_admin(client, db_session)
    resp = await client.get("/admin/stats")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    required_keys = {"users", "profiles_total", "profiles_pending", "profiles_approved", "requests_pending"}
    assert all(k in data for k in required_keys)
    assert all(isinstance(data[k], int) for k in required_keys)
    assert data["users"] >= 1


async def test_admin_stats_counts_correctly(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Admin stats counts reflect actual data."""
    user_id, _ = await _create_verified_user(client, db_session)
    for i in range(3):
        await client.post("/profiles", json=_sample_profile(first_name=f"User{i}"))
    await client.post("/auth/logout")
    await _login_admin(client, db_session)
    resp = await client.get("/admin/stats")
    assert resp.json()["profiles_total"] >= 3


async def test_admin_list_profiles_by_status(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Admin can list profiles filtered by status."""
    user_id, _ = await _create_verified_user(client, db_session)
    resp = await client.post("/profiles", json=_sample_profile(first_name="Test1"))
    pid1 = resp.json()["id"]
    resp = await client.post("/profiles", json=_sample_profile(first_name="Test2"))
    pid2 = resp.json()["id"]
    result = await db_session.execute(select(Profile).where(Profile.id == uuid.UUID(pid2)))
    p = result.scalar_one()
    p.status = ProfileStatusEnum.approved
    await db_session.commit()
    await client.post("/auth/logout")
    await _login_admin(client, db_session)
    resp = await client.get("/admin/profiles?status=approved")
    assert resp.status_code == 200
    assert pid2 in [p["id"] for p in resp.json()]


async def test_admin_can_approve_profile(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Admin can approve a pending profile."""
    user_id, _ = await _create_verified_user(client, db_session)
    resp = await client.post("/profiles", json=_sample_profile())
    pid = resp.json()["id"]
    await client.post(f"/profiles/{pid}/submit")
    await client.post("/auth/logout")
    await _login_admin(client, db_session)
    resp = await client.post(
        f"/admin/profiles/{pid}/approve",
        json={"admin_notes": "Looks good"},
    )
    assert resp.status_code == 200 and resp.json()["status"] == "approved"


async def test_get_admin_settings_returns_all_keys(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """GET /admin/settings returns all settings with public values."""
    await _login_admin(client, db_session)
    resp = await client.get("/admin/settings")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert len(data) > 0
    assert "photo_max_kb" in data and "smtp_host" in data and "smtp_password" in data


async def test_admin_settings_masks_smtp_password(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """smtp_password is masked as '***' in settings response."""
    await _login_admin(client, db_session)
    resp = await client.get("/admin/settings")
    password = resp.json().get("smtp_password", "")
    assert password in ("***", ""), f"Expected '***' or empty, got {password!r}"


async def test_admin_can_update_settings(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """PUT /admin/settings updates settings."""
    await _login_admin(client, db_session)
    resp = await client.put("/admin/settings", json={"photo_max_kb": 600, "upload_max_mb": 12})
    assert resp.status_code == 200, resp.text
    resp = await client.get("/admin/settings")
    data = resp.json()
    assert data.get("photo_max_kb") == 600 and data.get("upload_max_mb") == 12


async def test_promote_user_to_admin(client: AsyncClient, db_session: AsyncSession) -> None:
    """Admin can promote a user to admin."""
    user_id, _ = await _create_verified_user(client, db_session)
    await client.post("/auth/logout")
    await _login_admin(client, db_session)
    resp = await client.put(f"/admin/users/{user_id}/promote")
    assert resp.status_code == 200, resp.text
    result = await db_session.execute(select(User).where(User.id == uuid.UUID(user_id)))
    assert result.scalar_one().is_admin is True


async def test_promoted_user_can_access_admin_endpoints(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """After promotion, user can access /admin/* endpoints."""
    user_id, user_email = await _create_verified_user(client, db_session)
    await client.post("/auth/logout")
    await _login_admin(client, db_session)
    await client.put(f"/admin/users/{user_id}/promote")
    await client.post("/auth/logout")
    await client.post("/auth/login", json={"email": user_email, "password": "ValidPass123!"})
    resp = await client.get("/admin/stats")
    assert resp.status_code == 200
