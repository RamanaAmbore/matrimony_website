"""Bootstrap: seed canonical admin users and settings on every startup.

Two canonical users live in code, not in tenant DB state:
  - "ambore" (Ramana Ambore) — the original super-user
  - "rambo"  (Rambo Admin)    — the bootstrap super-user

Both are reset on every boot from the constants below — full_name, email,
phone, password, and the is_super / is_admin / is_approved / email_verified
flags. This guarantees recovery if anyone has tampered with them via SQL,
and lets the operator rotate the source-of-truth password by editing this
file rather than touching the DB.
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

_SUPER_HANDLE = "ambore"
_SUPER_EMAIL = "ramana.ambore@gmail.com"
_SUPER_PHONE = "+919840770711"
_SUPER_FULL_NAME = "Ramana Ambore"

_BOOTSTRAP_HANDLE = "rambo"
_BOOTSTRAP_EMAIL = "rambo@marathakalyanam.com"
_BOOTSTRAP_PHONE = "+919840770711"
_BOOTSTRAP_FULL_NAME = "Rambo Admin"


async def _ensure_canonical_user(
    session: AsyncSession,
    *,
    handle: str,
    email: str,
    phone: str,
    password: str,
    full_name: str,
) -> None:
    """Idempotent: create or fully reset a canonical super-user record.

    Looked up by `user_handle`. Fields reset on every boot so SQL tampering
    is harmless — code is the source of truth.
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
            is_super=True,
            email_verification_token=None,
        )
        session.add(user)
        await session.commit()
        logger.info("Canonical user %s created", handle)
    else:
        existing.full_name = full_name
        existing.email = email
        existing.phone_number = phone
        existing.password_hash = hash_password(password)
        existing.is_super = True
        existing.is_admin = True
        existing.is_approved = True
        existing.email_verified = True
        existing.email_verification_token = None
        await session.commit()


async def bootstrap(session: AsyncSession) -> None:
    """Run on every startup: seed setting defaults + ensure canonical users."""
    await settings_service.seed_defaults(session)
    await _ensure_canonical_user(
        session,
        handle=_SUPER_HANDLE,
        email=_SUPER_EMAIL,
        phone=_SUPER_PHONE,
        password=_CANONICAL_PASSWORD,
        full_name=_SUPER_FULL_NAME,
    )
    await _ensure_canonical_user(
        session,
        handle=_BOOTSTRAP_HANDLE,
        email=_BOOTSTRAP_EMAIL,
        phone=_BOOTSTRAP_PHONE,
        password=_CANONICAL_PASSWORD,
        full_name=_BOOTSTRAP_FULL_NAME,
    )
