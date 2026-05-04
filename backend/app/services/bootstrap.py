"""Bootstrap: seed admin user and settings on first startup."""
from __future__ import annotations

import logging
import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.services.auth import hash_password
from app.services.settings import settings_service

logger = logging.getLogger(__name__)

# Dev/launch credential — operator MUST rotate this password after first login.
_BOOTSTRAP_HANDLE = "rambo"
_BOOTSTRAP_EMAIL = "rambo@marathakalyanam.com"
_BOOTSTRAP_PHONE = "+91 9840770711"
_BOOTSTRAP_PASSWORD = "rambo1234"


async def bootstrap(session: AsyncSession) -> None:
    """Run once on startup: seed defaults and create admin if needed."""
    await settings_service.seed_defaults(session)

    result = await session.execute(select(func.count()).select_from(User))
    user_count = result.scalar_one()

    if user_count == 0:
        admin = User(
            id=uuid.uuid4(),
            email=_BOOTSTRAP_EMAIL,
            full_name="",
            user_handle=_BOOTSTRAP_HANDLE,
            phone_number=_BOOTSTRAP_PHONE,
            password_hash=hash_password(_BOOTSTRAP_PASSWORD),
            email_verified=True,
            is_admin=True,
            email_verification_token=None,
        )
        session.add(admin)
        await session.commit()

        sep = "=" * 60
        logger.warning(
            "\n%s\nBOOTSTRAP ADMIN CREATED\n"
            "User ID: %s\n"
            "Email: %s\n"
            "Password: %s\n"
            "ROTATE THIS PASSWORD AFTER FIRST LOGIN.\n%s",
            sep,
            _BOOTSTRAP_HANDLE,
            _BOOTSTRAP_EMAIL,
            _BOOTSTRAP_PASSWORD,
            sep,
        )
        return

    # If the bootstrap admin already exists, only backfill missing user_handle
    # (handles upgrade from a pre-handle DB). Password and email are never
    # overwritten — operator may have rotated them.
    existing = await session.execute(
        select(User).where(User.email == _BOOTSTRAP_EMAIL)
    )
    existing_user = existing.scalar_one_or_none()
    if existing_user:
        changed = False
        if not existing_user.user_handle:
            existing_user.user_handle = _BOOTSTRAP_HANDLE
            changed = True
        if not existing_user.phone_number or existing_user.phone_number.startswith("+00"):
            existing_user.phone_number = _BOOTSTRAP_PHONE
            changed = True
        if changed:
            await session.commit()
            logger.info("Backfilled bootstrap admin fields")
