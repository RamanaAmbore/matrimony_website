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

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _unique_handle() -> str:
    return f"u{uuid.uuid4().hex[:7]}"


def _unique_phone() -> str:
    return f"+1{uuid.uuid4().int % 10**10:010d}"


def _reg_payload(
    email: str,
    password: str = "ValidPass123!",
    handle: str | None = None,
    phone: str | None = None,
) -> dict:
    return {
        "email": email,
        "password": password,
        "user_handle": handle or _unique_handle(),
        "phone_number": phone or _unique_phone(),
    }


def _login_email(email: str, password: str = "ValidPass123!") -> dict:
    return {"identifier": email, "password": password}


def _login_handle(handle: str, password: str = "ValidPass123!") -> dict:
    return {"identifier": handle, "password": password}


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------

async def test_register_success(client: AsyncClient) -> None:
    """Register a new user — 201 + user_id returned."""
    email = f"user_{uuid.uuid4().hex[:8]}@example.com"
    resp = await client.post("/auth/register", json=_reg_payload(email))
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert "user_id" in data and data["user_id"]


async def test_register_missing_handle(client: AsyncClient) -> None:
    """Register without user_handle → 422."""
    resp = await client.post(
        "/auth/register",
        json={
            "email": f"x_{uuid.uuid4().hex[:6]}@example.com",
            "password": "ValidPass123!",
            "phone_number": _unique_phone(),
            # user_handle intentionally omitted
        },
    )
    assert resp.status_code == 422, resp.text


async def test_register_invalid_email(client: AsyncClient) -> None:
    """Malformed email → 422 invalid_email."""
    resp = await client.post(
        "/auth/register",
        json=_reg_payload("not-an-email"),
    )
    assert resp.status_code == 422, resp.text
    assert resp.json()["detail"]["code"] == "invalid_email"


async def test_register_password_no_digit(client: AsyncClient) -> None:
    """Password without a digit → 422 weak_password."""
    email = f"pw_{uuid.uuid4().hex[:6]}@example.com"
    resp = await client.post(
        "/auth/register",
        json=_reg_payload(email, password="OnlyLetters"),
    )
    assert resp.status_code == 422, resp.text
    assert resp.json()["detail"]["code"] == "weak_password"


async def test_register_password_no_letter(client: AsyncClient) -> None:
    """Password with only digits → 422 weak_password."""
    email = f"pw2_{uuid.uuid4().hex[:6]}@example.com"
    resp = await client.post(
        "/auth/register",
        json=_reg_payload(email, password="12345678"),
    )
    assert resp.status_code == 422, resp.text
    assert resp.json()["detail"]["code"] == "weak_password"


async def test_register_password_too_short(client: AsyncClient) -> None:
    """Password under 8 chars → 422 weak_password."""
    email = f"pw3_{uuid.uuid4().hex[:6]}@example.com"
    resp = await client.post(
        "/auth/register",
        json=_reg_payload(email, password="ab12"),
    )
    assert resp.status_code == 422, resp.text
    assert resp.json()["detail"]["code"] == "weak_password"


async def test_register_bootstrap_style_password_accepted(client: AsyncClient) -> None:
    """The bootstrap admin password 'rambo1234' meets the rules."""
    email = f"rb_{uuid.uuid4().hex[:6]}@example.com"
    resp = await client.post(
        "/auth/register",
        json=_reg_payload(email, password="rambo1234"),
    )
    assert resp.status_code == 201, resp.text


async def test_register_duplicate_phone(client: AsyncClient) -> None:
    """Duplicate phone → 409 phone_taken."""
    phone = _unique_phone()
    email1 = f"dphone1_{uuid.uuid4().hex[:6]}@example.com"
    email2 = f"dphone2_{uuid.uuid4().hex[:6]}@example.com"

    resp = await client.post("/auth/register", json=_reg_payload(email1, phone=phone))
    assert resp.status_code == 201, resp.text

    resp = await client.post("/auth/register", json=_reg_payload(email2, phone=phone))
    assert resp.status_code == 409, resp.text
    assert resp.json()["detail"]["code"] == "phone_taken"


async def test_register_invalid_handle_starts_with_digit(client: AsyncClient) -> None:
    """Handle starting with a digit → 422."""
    email = f"inv_{uuid.uuid4().hex[:6]}@example.com"
    resp = await client.post("/auth/register", json=_reg_payload(email, handle="99rambo"))
    assert resp.status_code == 422, resp.text


async def test_register_invalid_handle_too_short(client: AsyncClient) -> None:
    """Handle shorter than 3 chars → 422."""
    email = f"inv_{uuid.uuid4().hex[:6]}@example.com"
    resp = await client.post("/auth/register", json=_reg_payload(email, handle="ab"))
    assert resp.status_code == 422, resp.text


async def test_register_invalid_handle_special_char(client: AsyncClient) -> None:
    """Handle with special character → 422."""
    email = f"inv_{uuid.uuid4().hex[:6]}@example.com"
    resp = await client.post("/auth/register", json=_reg_payload(email, handle="rambo!"))
    assert resp.status_code == 422, resp.text


async def test_register_invalid_handle_with_space(client: AsyncClient) -> None:
    """Handle containing a space → 422."""
    email = f"inv_{uuid.uuid4().hex[:6]}@example.com"
    resp = await client.post("/auth/register", json=_reg_payload(email, handle="rambo space"))
    assert resp.status_code == 422, resp.text


async def test_register_duplicate_handle(client: AsyncClient) -> None:
    """Duplicate handle → 409 handle_taken."""
    handle = f"Uhandle{uuid.uuid4().hex[:4]}"
    email1 = f"a_{uuid.uuid4().hex[:6]}@example.com"
    email2 = f"b_{uuid.uuid4().hex[:6]}@example.com"

    resp = await client.post("/auth/register", json=_reg_payload(email1, handle=handle))
    assert resp.status_code == 201, resp.text

    resp = await client.post("/auth/register", json=_reg_payload(email2, handle=handle))
    assert resp.status_code == 409, resp.text
    assert resp.json()["detail"]["code"] == "handle_taken"


async def test_register_duplicate_handle_case_insensitive(client: AsyncClient) -> None:
    """Duplicate handle (different case) → 409 handle_taken."""
    base = f"Ucasex{uuid.uuid4().hex[:4]}"
    email1 = f"c1_{uuid.uuid4().hex[:6]}@example.com"
    email2 = f"c2_{uuid.uuid4().hex[:6]}@example.com"

    await client.post("/auth/register", json=_reg_payload(email1, handle=base))
    resp = await client.post("/auth/register", json=_reg_payload(email2, handle=base.upper()))
    assert resp.status_code == 409, resp.text
    assert resp.json()["detail"]["code"] == "handle_taken"


async def test_register_duplicate_email(client: AsyncClient) -> None:
    """Duplicate email → 409 email_taken."""
    email = f"dup_{uuid.uuid4().hex[:8]}@example.com"
    await client.post("/auth/register", json=_reg_payload(email))
    resp = await client.post("/auth/register", json=_reg_payload(email, handle=_unique_handle()))
    assert resp.status_code == 409, resp.text
    assert resp.json()["detail"]["code"] == "email_taken"


# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------

async def test_login_with_email(client: AsyncClient) -> None:
    """Login with email (identifier contains @) succeeds."""
    email = f"login_{uuid.uuid4().hex[:8]}@example.com"
    handle = _unique_handle()
    await client.post("/auth/register", json=_reg_payload(email, handle=handle))

    resp = await client.post("/auth/login", json=_login_email(email))
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["user_id"]
    assert data["email"] == email
    assert data["user_handle"] == handle
    assert data["is_admin"] is False
    assert data["email_verified"] is False


async def test_login_with_handle(client: AsyncClient) -> None:
    """Login with handle (no @ in identifier) succeeds."""
    email = f"hlogin_{uuid.uuid4().hex[:8]}@example.com"
    handle = f"Hndl{uuid.uuid4().hex[:5]}"
    await client.post("/auth/register", json=_reg_payload(email, handle=handle))

    resp = await client.post("/auth/login", json=_login_handle(handle))
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["user_handle"] == handle
    assert data["email"] == email


async def test_login_with_handle_case_insensitive(client: AsyncClient) -> None:
    """Login with handle in different case succeeds (case-insensitive lookup)."""
    email = f"cilogin_{uuid.uuid4().hex[:8]}@example.com"
    handle = f"Rambo{uuid.uuid4().hex[:4]}"
    await client.post("/auth/register", json=_reg_payload(email, handle=handle))

    resp = await client.post("/auth/login", json=_login_handle(handle.upper()))
    assert resp.status_code == 200, resp.text


async def test_login_wrong_password(client: AsyncClient) -> None:
    """Login fails with wrong password → 401."""
    email = f"wrongpw_{uuid.uuid4().hex[:8]}@example.com"
    await client.post("/auth/register", json=_reg_payload(email))
    resp = await client.post("/auth/login", json={"identifier": email, "password": "WrongPass123!"})
    assert resp.status_code == 401, resp.text
    assert resp.json()["detail"]["code"] == "invalid_credentials"


async def test_login_nonexistent_email(client: AsyncClient) -> None:
    """Login fails with non-existent email → 401."""
    email = f"nonexist_{uuid.uuid4().hex[:8]}@example.com"
    resp = await client.post("/auth/login", json=_login_email(email))
    assert resp.status_code == 401, resp.text
    assert resp.json()["detail"]["code"] == "invalid_credentials"


async def test_login_nonexistent_handle(client: AsyncClient) -> None:
    """Login fails with non-existent handle → 401."""
    resp = await client.post("/auth/login", json=_login_handle("ghost_handle_xyz"))
    assert resp.status_code == 401, resp.text
    assert resp.json()["detail"]["code"] == "invalid_credentials"


# ---------------------------------------------------------------------------
# /auth/me
# ---------------------------------------------------------------------------

async def test_me_unauthenticated(client: AsyncClient) -> None:
    """/auth/me returns 401 when not logged in."""
    resp = await client.get("/auth/me")
    assert resp.status_code == 401


async def test_me_authenticated(client: AsyncClient) -> None:
    """/auth/me returns user_id, user_handle, email when logged in."""
    email = f"me_{uuid.uuid4().hex[:8]}@example.com"
    handle = _unique_handle()
    await client.post("/auth/register", json=_reg_payload(email, handle=handle))
    await client.post("/auth/login", json=_login_email(email))

    resp = await client.get("/auth/me")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["email"] == email
    assert data["user_handle"] == handle
    assert data["is_admin"] is False


# ---------------------------------------------------------------------------
# Logout
# ---------------------------------------------------------------------------

async def test_logout_clears_session(client: AsyncClient) -> None:
    """Logout clears the session."""
    email = f"logout_{uuid.uuid4().hex[:8]}@example.com"
    await client.post("/auth/register", json=_reg_payload(email))
    await client.post("/auth/login", json=_login_email(email))

    resp = await client.post("/auth/logout")
    assert resp.status_code == 204

    resp = await client.get("/auth/me")
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Email verification
# ---------------------------------------------------------------------------

async def test_verify_email_with_bad_token(client: AsyncClient, db_session: AsyncSession) -> None:
    """Email verification with bad token returns 400/404."""
    resp = await client.post("/auth/verify-email", json={"token": "badtoken123"})
    assert resp.status_code in [400, 404], resp.text


async def test_verify_email_with_good_token(client: AsyncClient, db_session: AsyncSession) -> None:
    """Email verification with good token succeeds; re-login reflects verified state."""
    email = f"verify_{uuid.uuid4().hex[:8]}@example.com"
    password = "ValidPass123!"

    resp = await client.post("/auth/register", json=_reg_payload(email, password=password))
    user_id = resp.json()["user_id"]

    result = await db_session.execute(select(User).where(User.id == uuid.UUID(user_id)))
    user = result.scalar_one()
    token = user.email_verification_token
    assert token is not None

    resp = await client.post("/auth/verify-email", json={"token": token})
    assert resp.status_code == 200, resp.text

    # Re-login so fresh JWT with email_verified=True is issued
    await client.post("/auth/login", json=_login_email(email, password))

    resp = await client.get("/auth/me")
    data = resp.json()
    assert data["email_verified"] is True


async def test_verify_email_double_use(client: AsyncClient, db_session: AsyncSession) -> None:
    """Using the same verification token twice fails on second attempt."""
    email = f"doubleuse_{uuid.uuid4().hex[:8]}@example.com"
    password = "ValidPass123!"

    resp = await client.post("/auth/register", json=_reg_payload(email, password=password))
    user_id = resp.json()["user_id"]

    result = await db_session.execute(select(User).where(User.id == uuid.UUID(user_id)))
    user = result.scalar_one()
    token = user.email_verification_token

    resp = await client.post("/auth/verify-email", json={"token": token})
    assert resp.status_code == 200

    resp = await client.post("/auth/verify-email", json={"token": token})
    assert resp.status_code == 400, f"Expected 400 but got {resp.status_code}, body: {resp.text}"


async def test_profile_creation_requires_email_verified(client: AsyncClient) -> None:
    """Cannot create profile until email_verified is true."""
    email = f"unverified_{uuid.uuid4().hex[:8]}@example.com"
    password = "ValidPass123!"

    await client.post("/auth/register", json=_reg_payload(email, password=password))
    await client.post("/auth/login", json=_login_email(email, password))

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
