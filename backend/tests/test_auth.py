"""Authentication endpoint tests."""
from __future__ import annotations

import re
import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.models.user import User

pytestmark = pytest.mark.asyncio

# MK-XXXXXX pattern for system-generated user handles
_MK_RE = re.compile(r"^MK-[A-Z0-9]{6}$")

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _unique_phone() -> str:
    return f"+1{uuid.uuid4().int % 10**10:010d}"


def _reg_payload(
    email: str,
    password: str = "ValidPass123!",
    phone: str | None = None,
    full_name: str = "Test User",
) -> dict:
    """Registration payload — handle is now system-generated, not supplied."""
    return {
        "email": email,
        "password": password,
        "phone_number": phone or _unique_phone(),
        "full_name": full_name,
    }


def _login_email(email: str, password: str = "ValidPass123!") -> dict:
    return {"identifier": email, "password": password}


def _login_handle(handle: str, password: str = "ValidPass123!") -> dict:
    return {"identifier": handle, "password": password}


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------

async def test_register_success(client: AsyncClient) -> None:
    """Register a new user — 201 + uuid returned, user_id is MK-XXXXXX."""
    email = f"user_{uuid.uuid4().hex[:8]}@example.com"
    resp = await client.post("/auth/register", json=_reg_payload(email))
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert "uuid" in data and data["uuid"]


async def test_register_missing_full_name(client: AsyncClient) -> None:
    """Register without full_name → 400/422 (required field)."""
    resp = await client.post(
        "/auth/register",
        json={
            "email": f"x_{uuid.uuid4().hex[:6]}@example.com",
            "password": "ValidPass123!",
            "phone_number": _unique_phone(),
            # full_name intentionally omitted
        },
    )
    assert resp.status_code in (400, 422), resp.text


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
    """Duplicate phone → 409 phone_taken (prod mode enforced via settings patch)."""
    from app.services.settings import settings_service
    settings_service._cache["is_prod"] = True
    try:
        phone = _unique_phone()
        email1 = f"dphone1_{uuid.uuid4().hex[:6]}@example.com"
        email2 = f"dphone2_{uuid.uuid4().hex[:6]}@example.com"

        resp = await client.post("/auth/register", json=_reg_payload(email1, phone=phone))
        assert resp.status_code == 201, resp.text

        resp = await client.post("/auth/register", json=_reg_payload(email2, phone=phone))
        assert resp.status_code in (409, 422), resp.text
        assert resp.json()["detail"]["code"] == "phone_taken"
    finally:
        settings_service._cache["is_prod"] = False


async def test_register_generated_handle_is_mk_format(client: AsyncClient) -> None:
    """System-generated user_handle is MK-XXXXXX format (verified via login response)."""
    email = f"mkfmt_{uuid.uuid4().hex[:8]}@example.com"
    resp = await client.post("/auth/register", json=_reg_payload(email))
    assert resp.status_code == 201, resp.text

    # Log in to get the handle from the JWT response
    login_resp = await client.post("/auth/login", json=_login_email(email))
    assert login_resp.status_code == 200, login_resp.text
    data = login_resp.json()
    assert _MK_RE.match(data["user_id"]), f"Expected MK-XXXXXX, got {data['user_id']!r}"


async def test_register_duplicate_email(client: AsyncClient) -> None:
    """Duplicate email → 409 email_taken (prod mode enforced via settings patch)."""
    from app.services.settings import settings_service
    settings_service._cache["is_prod"] = True
    try:
        email = f"dup_{uuid.uuid4().hex[:8]}@example.com"
        await client.post("/auth/register", json=_reg_payload(email))
        resp = await client.post("/auth/register", json=_reg_payload(email))
        assert resp.status_code in (409, 422), resp.text
        assert resp.json()["detail"]["code"] == "email_taken"
    finally:
        settings_service._cache["is_prod"] = False


# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------

async def test_login_with_email(client: AsyncClient) -> None:
    """Login with email (identifier contains @) succeeds; user_id is MK-XXXXXX."""
    email = f"login_{uuid.uuid4().hex[:8]}@example.com"
    await client.post("/auth/register", json=_reg_payload(email))

    resp = await client.post("/auth/login", json=_login_email(email))
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["uuid"]
    assert data["email"] == email
    assert _MK_RE.match(data["user_id"]), f"Expected MK-XXXXXX, got {data['user_id']!r}"
    assert data["is_admin"] is False
    assert data["email_verified"] is False


async def test_login_with_handle(client: AsyncClient) -> None:
    """Login with system-generated MK-XXXXXX handle (no @ in identifier) succeeds."""
    email = f"hlogin_{uuid.uuid4().hex[:8]}@example.com"
    await client.post("/auth/register", json=_reg_payload(email))

    # First login via email to discover the handle
    first_resp = await client.post("/auth/login", json=_login_email(email))
    assert first_resp.status_code == 200, first_resp.text
    system_handle = first_resp.json()["user_id"]
    assert _MK_RE.match(system_handle)

    # Now login using the MK-XXXXXX handle as identifier (no '@')
    resp = await client.post("/auth/login", json=_login_handle(system_handle))
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["user_id"] == system_handle
    assert data["email"] == email


async def test_login_with_handle_case_insensitive(client: AsyncClient) -> None:
    """Login with handle in different case succeeds (case-insensitive lookup)."""
    email = f"cilogin_{uuid.uuid4().hex[:8]}@example.com"
    await client.post("/auth/register", json=_reg_payload(email))

    # Discover the system-generated handle
    first_resp = await client.post("/auth/login", json=_login_email(email))
    system_handle = first_resp.json()["user_id"]  # e.g. MK-AB1234

    resp = await client.post("/auth/login", json=_login_handle(system_handle.lower()))
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
    """/auth/me returns uuid, user_id (MK-XXXXXX), email when logged in."""
    email = f"me_{uuid.uuid4().hex[:8]}@example.com"
    await client.post("/auth/register", json=_reg_payload(email))
    login_data = (await client.post("/auth/login", json=_login_email(email))).json()
    system_handle = login_data["user_id"]

    resp = await client.get("/auth/me")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["email"] == email
    assert data["user_id"] == system_handle
    assert _MK_RE.match(data["user_id"]), f"Expected MK-XXXXXX, got {data['user_id']!r}"
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

async def test_verify_email_with_bad_token(client: AsyncClient) -> None:
    """Email verification with bad token returns 400/404."""
    resp = await client.post("/auth/verify-email", json={"token": "badtoken123"})
    assert resp.status_code in [400, 404], resp.text


async def test_verify_email_with_good_token(client: AsyncClient) -> None:
    """Email verification with good token succeeds; re-login reflects verified state."""
    from app.db import AsyncSessionLocal
    email = f"verify_{uuid.uuid4().hex[:8]}@example.com"
    password = "ValidPass123!"

    resp = await client.post("/auth/register", json=_reg_payload(email, password=password))
    user_uuid = resp.json()["uuid"]

    # Read the token from a fresh session (app already committed this row)
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).where(User.id == uuid.UUID(user_uuid)))
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


async def test_verify_email_double_use(client: AsyncClient) -> None:
    """Using the same verification token twice fails on second attempt."""
    from app.db import AsyncSessionLocal
    email = f"doubleuse_{uuid.uuid4().hex[:8]}@example.com"
    password = "ValidPass123!"

    resp = await client.post("/auth/register", json=_reg_payload(email, password=password))
    user_uuid = resp.json()["uuid"]

    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).where(User.id == uuid.UUID(user_uuid)))
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
