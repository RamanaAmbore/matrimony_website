"""JWT service and auth cookie tests."""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

import jwt
import pytest
from httpx import AsyncClient

from app.config import SESSION_SECRET
from app.services.jwt_auth import _ALGORITHM, mint_jwt, decode_jwt

pytestmark = pytest.mark.asyncio

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _unique_handle() -> str:
    return f"u{uuid.uuid4().hex[:7]}"


def _reg(email: str, handle: str, password: str = "ValidPass123!") -> dict:
    return {"email": email, "password": password, "user_handle": handle, "phone_number": "+911234567890", "full_name": "Test User"}


def _login(identifier: str, password: str = "ValidPass123!") -> dict:
    return {"identifier": identifier, "password": password}


# ---------------------------------------------------------------------------
# Unit tests — no DB required
# ---------------------------------------------------------------------------


def test_mint_and_decode_roundtrip() -> None:
    """mint_jwt produces a token that decode_jwt can verify."""
    user_id = str(uuid.uuid4())
    token = mint_jwt(
        user_id=user_id,
        handle="rambo",
        email="rambo@example.com",
        full_name="Rambo Test",
        is_admin=False,
        email_verified=True,
    )
    payload = decode_jwt(token)

    assert payload is not None
    assert payload["sub"] == user_id
    assert payload["handle"] == "rambo"
    assert payload["email"] == "rambo@example.com"
    assert payload["is_admin"] is False
    assert payload["email_verified"] is True


def test_expired_token_returns_none() -> None:
    """A token with exp in the past decodes to None."""
    now = datetime.now(timezone.utc)
    expired_payload = {
        "sub": "some-user",
        "handle": "ghost",
        "email": "ghost@example.com",
        "is_admin": False,
        "email_verified": False,
        "iat": now - timedelta(hours=25),
        "exp": now - timedelta(seconds=1),
    }
    token = jwt.encode(expired_payload, SESSION_SECRET, algorithm=_ALGORITHM)
    assert decode_jwt(token) is None


def test_bad_signature_returns_none() -> None:
    """A token signed with a different key decodes to None."""
    token = mint_jwt(
        user_id="user-x",
        handle="userx",
        email="x@example.com",
        full_name="User X",
        is_admin=True,
        email_verified=True,
    )
    # Corrupt the last 4 bytes of the signature
    bad_token = token[:-4] + ("A" * 4)
    assert decode_jwt(bad_token) is None


def test_malformed_token_returns_none() -> None:
    """A completely invalid string decodes to None."""
    assert decode_jwt("not.a.jwt") is None
    assert decode_jwt("") is None


def test_token_payload_fields() -> None:
    """Token contains iat and exp claims within expected range."""
    before = datetime.now(timezone.utc)
    token = mint_jwt(
        user_id="u",
        handle="testuser",
        email="testuser@example.com",
        full_name="Test User",
        is_admin=False,
        email_verified=False,
    )
    after = datetime.now(timezone.utc)

    payload = decode_jwt(token)
    assert payload is not None

    iat = datetime.fromtimestamp(payload["iat"], tz=timezone.utc)
    exp = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)

    assert before <= iat <= after
    # exp should be approximately iat + 24h
    delta = exp - iat
    assert timedelta(hours=23, minutes=59) <= delta <= timedelta(hours=24, seconds=5)


# ---------------------------------------------------------------------------
# Integration tests — require only ASGI (no DB for cookie shape tests)
# ---------------------------------------------------------------------------


async def test_login_sets_jwt_cookie(client: AsyncClient) -> None:
    """POST /auth/login sets the mk_jwt cookie."""
    email = f"jwttest_{uuid.uuid4().hex[:8]}@example.com"
    handle = _unique_handle()
    password = "ValidPass123!"

    await client.post("/auth/register", json=_reg(email, handle, password))
    resp = await client.post("/auth/login", json=_login(email, password))

    assert resp.status_code == 200, resp.text
    assert "mk_jwt" in resp.cookies
    token = resp.cookies["mk_jwt"]
    payload = decode_jwt(token)
    assert payload is not None
    assert payload.get("is_admin") is False
    assert payload.get("email_verified") is False
    assert payload.get("handle") == handle


async def test_logout_clears_jwt_cookie(client: AsyncClient) -> None:
    """POST /auth/logout deletes the mk_jwt cookie."""
    email = f"logoutjwt_{uuid.uuid4().hex[:8]}@example.com"
    handle = _unique_handle()
    password = "ValidPass123!"

    await client.post("/auth/register", json=_reg(email, handle, password))
    await client.post("/auth/login", json=_login(email, password))

    resp = await client.post("/auth/logout")
    assert resp.status_code == 204

    # Cookie should be absent or have an empty/expired value
    cookie_val = resp.cookies.get("mk_jwt", "")
    assert cookie_val == ""

    # Subsequent /auth/me must return 401
    resp = await client.get("/auth/me")
    assert resp.status_code == 401


async def test_me_returns_payload_from_jwt_cookie(client: AsyncClient) -> None:
    """/auth/me reads user info from the JWT cookie, not the session."""
    email = f"mejwt_{uuid.uuid4().hex[:8]}@example.com"
    handle = _unique_handle()
    password = "ValidPass123!"

    await client.post("/auth/register", json=_reg(email, handle, password))
    await client.post("/auth/login", json=_login(email, password))

    resp = await client.get("/auth/me")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert "uuid" in data
    assert data["user_id"] == handle
    assert data["email"] == email
    assert data["is_admin"] is False
    assert data["email_verified"] is False


async def test_me_unauthenticated_without_cookie(client: AsyncClient) -> None:
    """/auth/me returns 401 when no JWT cookie is present."""
    # Use a fresh client without any cookies
    from httpx import ASGITransport, AsyncClient as FreshClient
    from app.main import app

    async with FreshClient(transport=ASGITransport(app=app), base_url="http://testserver") as fresh:
        resp = await fresh.get("/auth/me")
    assert resp.status_code == 401
