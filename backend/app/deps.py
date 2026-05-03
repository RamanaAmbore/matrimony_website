"""Litestar dependency providers."""
from __future__ import annotations

from typing import Any

from litestar.connection import ASGIConnection
from litestar.exceptions import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db_session  # noqa: F401  — re-exported for wiring


async def provide_db_session() -> AsyncSession:  # type: ignore[return]
    """Provided by get_db_session generator — wired in app."""
    ...


def get_current_user_payload(connection: ASGIConnection) -> dict[str, Any]:
    """Extract JWT payload from scope.  Raises 401 if not present."""
    payload: dict[str, Any] | None = connection.scope.get("user_payload")
    if not payload:
        raise HTTPException(
            status_code=401,
            detail={"code": "unauthenticated", "message": "Authentication required"},
        )
    return payload


def get_current_user_payload_optional(connection: ASGIConnection) -> dict[str, Any] | None:
    """Extract JWT payload from scope, or None if unauthenticated."""
    return connection.scope.get("user_payload")  # type: ignore[return-value]


# Keep old name as alias so any callers using get_current_user still work
def get_current_user(connection: ASGIConnection) -> dict[str, Any]:
    return get_current_user_payload(connection)


def get_current_user_optional(connection: ASGIConnection) -> dict[str, Any] | None:
    return get_current_user_payload_optional(connection)


def require_auth(connection: ASGIConnection) -> dict[str, Any]:
    """Guard: require authenticated user."""
    return get_current_user_payload(connection)


def require_admin(connection: ASGIConnection) -> dict[str, Any]:
    """Guard: require authenticated admin user."""
    payload = get_current_user_payload(connection)
    if not payload.get("is_admin"):
        raise HTTPException(
            status_code=403,
            detail={"code": "forbidden", "message": "Admin access required"},
        )
    return payload


def require_email_verified(connection: ASGIConnection) -> dict[str, Any]:
    """Guard: require auth + email verified."""
    payload = get_current_user_payload(connection)
    if not payload.get("email_verified"):
        raise HTTPException(
            status_code=403,
            detail={"code": "email_not_verified", "message": "Email verification required"},
        )
    return payload
