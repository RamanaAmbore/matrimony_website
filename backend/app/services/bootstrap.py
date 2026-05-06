"""Bootstrap: seed canonical admin users and settings on every startup.

Four canonical users live in code, not in tenant DB state:
  - "ambore" (Ramana Ambore)        — super-user (primary)
  - "super"  (Venkat Somajigiri)    — super-user (secondary)
  - "rambo"  (Ramana Ambore)        — regular admin (operational)
  - "admin"  (Ramana Ambore)        — regular admin (day-to-day mod)

All four are reset on every boot from the constants below — full_name,
email, phone, password, and the is_super / is_admin / is_approved /
email_verified flags. This guarantees recovery if anyone has tampered
with them via SQL, and lets the operator rotate the source-of-truth
password by editing this file rather than touching the DB.
"""
from __future__ import annotations

import logging
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.services.auth import hash_password
from app.services.settings import settings_service

logger = logging.getLogger(__name__)

# Shared canonical password for both super-users.
_CANONICAL_PASSWORD = "Zerodha01#"

# Two super-users -------------------------------------------------------
_SUPER_HANDLE = "ambore"
_SUPER_EMAIL = "ramana.ambore@gmail.com"
_SUPER_PHONE = "+919840770711"
_SUPER_FULL_NAME = "Ramana Ambore"

_SUPER2_HANDLE = "super"
_SUPER2_EMAIL = "marathakalyanam@gmail.com"
_SUPER2_PHONE = "+919505250025"
_SUPER2_FULL_NAME = "Venkat Somajigiri"

# Two regular admins ----------------------------------------------------
_ADMIN1_HANDLE = "rambo"
_ADMIN1_EMAIL = "ramboquant@gmail.com"
_ADMIN1_PHONE = "+15155254636"
_ADMIN1_FULL_NAME = "Ramana Ambore"

_ADMIN2_HANDLE = "admin"
_ADMIN2_EMAIL = "admin.marathakalyanam@gmail.com"
_ADMIN2_PHONE = "+15155254636"
_ADMIN2_FULL_NAME = "Ramana Ambore"


async def _ensure_canonical_user(
    session: AsyncSession,
    *,
    handle: str,
    email: str,
    phone: str,
    password: str,
    full_name: str,
    is_super: bool,
) -> None:
    """Idempotent: create or fully reset a canonical admin/super user record.

    Looked up by `user_handle`. Fields reset on every boot so SQL tampering
    is harmless — code is the source of truth. is_admin is always True;
    is_super is set per the caller's argument.
    """
    result = await session.execute(
        select(User).where(User.user_handle == handle)
    )
    existing = result.scalar_one_or_none()
    if existing is None:
        user = User(
            id=uuid.uuid4(),
            email=email,
            full_name=full_name,
            user_handle=handle,
            phone_number=phone,
            password_hash=hash_password(password),
            email_verified=True,
            is_approved=True,
            is_admin=True,
            is_super=is_super,
            email_verification_token=None,
        )
        session.add(user)
        await session.commit()
        logger.info("Canonical user %s created (super=%s)", handle, is_super)
    else:
        existing.full_name = full_name
        existing.email = email
        existing.phone_number = phone
        existing.password_hash = hash_password(password)
        existing.is_super = is_super
        existing.is_admin = True
        existing.is_approved = True
        existing.email_verified = True
        existing.email_verification_token = None
        await session.commit()


async def bootstrap(session: AsyncSession) -> None:
    """Run on every startup: seed setting defaults + ensure canonical users."""
    await settings_service.seed_defaults(session)
    # Supers
    for h, e, p, n in [
        (_SUPER_HANDLE, _SUPER_EMAIL, _SUPER_PHONE, _SUPER_FULL_NAME),
        (_SUPER2_HANDLE, _SUPER2_EMAIL, _SUPER2_PHONE, _SUPER2_FULL_NAME),
    ]:
        await _ensure_canonical_user(
            session, handle=h, email=e, phone=p, password=_CANONICAL_PASSWORD,
            full_name=n, is_super=True,
        )
    # Regular admins
    for h, e, p, n in [
        (_ADMIN1_HANDLE, _ADMIN1_EMAIL, _ADMIN1_PHONE, _ADMIN1_FULL_NAME),
        (_ADMIN2_HANDLE, _ADMIN2_EMAIL, _ADMIN2_PHONE, _ADMIN2_FULL_NAME),
    ]:
        await _ensure_canonical_user(
            session, handle=h, email=e, phone=p, password=_CANONICAL_PASSWORD,
            full_name=n, is_super=False,
        )
