"""Authentication endpoint tests."""
from __future__ import annotations

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.services.auth import hash_password

pytestmark = pytest.mark.asyncio


async def test_register_success(client: AsyncClient) -> None:
    """Register a new user."""
    email = f"user_{uuid.uuid4().hex[:8]}@example.com"
    password = "ValidPass123!"

    resp = await client.post("/auth/register", json={"email": email, "password": password})
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert "user_id" in data
    assert data["user_id"]


async def test_register_duplicate_email(client: AsyncClient) -> None:
    """Cannot register with duplicate email."""
    email = f"dup_{uuid.uuid4().hex[:8]}@example.com"
    await client.post("/auth/register", json={"email": email, "password": "ValidPass123!"})

    resp = await client.post("/auth/register", json={"email": email, "password": "ValidPass123!"})
    assert resp.status_code == 409, resp.text
    assert resp.json()["detail"]["code"] == "email_exists"


async def test_login_success(client: AsyncClient) -> None:
    """Login with correct credentials."""
    email = f"login_{uuid.uuid4().hex[:8]}@example.com"
    password = "ValidPass123!"

    await client.post("/auth/register", json={"email": email, "password": password})
    resp = await client.post("/auth/login", json={"email": email, "password": password})

    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["user_id"]
    assert data["email"] == email
    assert data["is_admin"] is False
    assert data["email_verified"] is False


async def test_login_wrong_password(client: AsyncClient) -> None:
    """Login fails with wrong password."""
    email = f"wrongpw_{uuid.uuid4().hex[:8]}@example.com"
    await client.post("/auth/register", json={"email": email, "password": "ValidPass123!"})

    resp = await client.post("/auth/login", json={"email": email, "password": "WrongPass123!"})
    assert resp.status_code == 401, resp.text
    assert resp.json()["detail"]["code"] == "invalid_credentials"


async def test_login_nonexistent_email(client: AsyncClient) -> None:
    """Login fails with non-existent email."""
    email = f"nonexist_{uuid.uuid4().hex[:8]}@example.com"

    resp = await client.post("/auth/login", json={"email": email, "password": "AnyPass123!"})
    assert resp.status_code == 401, resp.text
    assert resp.json()["detail"]["code"] == "invalid_credentials"


async def test_me_unauthenticated(client: AsyncClient) -> None:
    """/auth/me returns 401 when not logged in."""
    resp = await client.get("/auth/me")
    assert resp.status_code == 401


async def test_me_authenticated(client: AsyncClient) -> None:
    """/auth/me returns user info when logged in."""
    email = f"me_{uuid.uuid4().hex[:8]}@example.com"
    password = "ValidPass123!"

    await client.post("/auth/register", json={"email": email, "password": password})
    await client.post("/auth/login", json={"email": email, "password": password})

    resp = await client.get("/auth/me")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["email"] == email
    assert data["is_admin"] is False


async def test_logout_clears_session(client: AsyncClient) -> None:
    """Logout clears the session."""
    email = f"logout_{uuid.uuid4().hex[:8]}@example.com"
    password = "ValidPass123!"

    await client.post("/auth/register", json={"email": email, "password": password})
    await client.post("/auth/login", json={"email": email, "password": password})

    resp = await client.post("/auth/logout")
    assert resp.status_code == 204

    resp = await client.get("/auth/me")
    assert resp.status_code == 401


async def test_verify_email_with_bad_token(client: AsyncClient, db_session: AsyncSession) -> None:
    """Email verification with bad token returns 400/404."""
    resp = await client.post("/auth/verify-email", json={"token": "badtoken123"})
    assert resp.status_code in [400, 404], resp.text


async def test_verify_email_with_good_token(client: AsyncClient, db_session: AsyncSession) -> None:
    """Email verification with good token succeeds."""
    email = f"verify_{uuid.uuid4().hex[:8]}@example.com"
    password = "ValidPass123!"

    # Register user
    resp = await client.post("/auth/register", json={"email": email, "password": password})
    user_id = resp.json()["user_id"]

    # Get the verification token from DB
    result = await db_session.execute(select(User).where(User.id == uuid.UUID(user_id)))
    user = result.scalar_one()
    token = user.email_verification_token
    assert token is not None

    # Verify email
    resp = await client.post("/auth/verify-email", json={"token": token})
    assert resp.status_code == 200, resp.text

    # Confirm user is now verified
    resp = await client.get("/auth/me")
    data = resp.json()
    assert data["email_verified"] is True


async def test_verify_email_double_use(client: AsyncClient, db_session: AsyncSession) -> None:
    """Using the same verification token twice fails on second attempt."""
    email = f"doubleuse_{uuid.uuid4().hex[:8]}@example.com"
    password = "ValidPass123!"

    resp = await client.post("/auth/register", json={"email": email, "password": password})
    user_id = resp.json()["user_id"]

    result = await db_session.execute(select(User).where(User.id == uuid.UUID(user_id)))
    user = result.scalar_one()
    token = user.email_verification_token

    # First verification succeeds
    resp = await client.post("/auth/verify-email", json={"token": token})
    assert resp.status_code == 200

    # Second verification fails
    resp = await client.post("/auth/verify-email", json={"token": token})
    assert resp.status_code == 400, f"Expected 400 but got {resp.status_code}, body: {resp.text}"


async def test_profile_creation_requires_email_verified(client: AsyncClient) -> None:
    """Cannot create profile until email_verified is true."""
    email = f"unverified_{uuid.uuid4().hex[:8]}@example.com"
    password = "ValidPass123!"

    await client.post("/auth/register", json={"email": email, "password": password})
    await client.post("/auth/login", json={"email": email, "password": password})

    profile_data = {
        "gender": "bride",
        "first_name": "Test",
        "last_name": "User",
        "dob": "1995-06-15",
        "height_cm": 163,
        "complexion": "wheatish",
        "education": "B.Tech",
        "occupation": "Engineer",
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

    resp = await client.post("/profiles", json=profile_data)
    assert resp.status_code == 403, resp.text
    assert resp.json()["detail"]["code"] == "email_not_verified"
