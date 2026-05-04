"""JWT mint/decode helpers for stateless authentication."""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any

import jwt

from app.config import SESSION_SECRET

logger = logging.getLogger(__name__)

_ALGORITHM = "HS256"
_EXPIRY_SECONDS = 86400 * 7  # 7 days — keep in sync with auth.py _COOKIE_MAX_AGE


def mint_jwt(
    user_id: str,
    handle: str,
    email: str,
    full_name: str,
    is_admin: bool,
    email_verified: bool,
    is_approved: bool = False,
    is_super: bool = False,
) -> str:
    """Create a signed JWT for the given user."""
    now = datetime.now(timezone.utc)
    payload: dict[str, Any] = {
        "sub": user_id,
        "handle": handle,
        "email": email,
        "full_name": full_name,
        "is_admin": is_admin,
        "is_super": is_super,
        "email_verified": email_verified,
        "is_approved": is_approved,
        "iat": now,
        "exp": now + timedelta(seconds=_EXPIRY_SECONDS),
    }
    return jwt.encode(payload, SESSION_SECRET, algorithm=_ALGORITHM)


def decode_jwt(token: str) -> dict[str, Any] | None:
    """Decode and verify a JWT.

    Returns the payload dict on success, or None on any failure
    (expired, bad signature, malformed, etc.).
    """
    try:
        return jwt.decode(token, SESSION_SECRET, algorithms=[_ALGORITHM])
    except jwt.PyJWTError as exc:
        logger.debug("JWT decode failed: %s", exc)
        return None
