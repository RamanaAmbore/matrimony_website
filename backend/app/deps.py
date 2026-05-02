"""Litestar dependency providers."""
from __future__ import annotations

import uuid
from typing import Any

from litestar.connection import ASGIConnection
from litestar.exceptions import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db_session


async def provide_db_session() -> AsyncSession:  # type: ignore[return]
    """Provided by get_db_session generator — wired in app."""
    ...


def get_current_user(connection: ASGIConnection) -> dict[str, Any]:
    """Extract current user from session. Raises 401 if not authenticated."""
    user = connection.session.get("user")
    if not user:
        raise HTTPException(status_code=401, detail={"code": "unauthenticated", "message": "Authentication required"})
    return user  # type: ignore[return-value]


def get_current_user_optional(connection: ASGIConnection) -> dict[str, Any] | None:
    """Extract current user from session, or None if not authenticated."""
    return connection.session.get("user")  # type: ignore[return-value]


def require_auth(connection: ASGIConnection) -> dict[str, Any]:
    """Guard: require authenticated user."""
    return get_current_user(connection)


def require_admin(connection: ASGIConnection) -> dict[str, Any]:
    """Guard: require admin user."""
    user = get_current_user(connection)
    if not user.get("is_admin"):
        raise HTTPException(status_code=403, detail={"code": "forbidden", "message": "Admin access required"})
    return user


def require_email_verified(connection: ASGIConnection) -> dict[str, Any]:
    """Guard: require auth + email verified."""
    user = get_current_user(connection)
    if not user.get("email_verified"):
        raise HTTPException(
            status_code=403,
            detail={"code": "email_not_verified", "message": "Email verification required"},
        )
    return user
