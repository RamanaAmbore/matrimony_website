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
# This is the intentional dev/launch credential: rambo / rambo1234.
_BOOTSTRAP_EMAIL = "rambo@marathakalyanam.com"
_BOOTSTRAP_PASSWORD = "rambo1234"


async def bootstrap(session: AsyncSession) -> None:
    """Run once on startup: seed defaults and create admin if needed."""
    # Seed settings defaults
    await settings_service.seed_defaults(session)

    # Check if any users exist
    result = await session.execute(select(func.count()).select_from(User))
    user_count = result.scalar_one()

    if user_count == 0:
        # Create bootstrap admin with known dev/launch credentials.
        # IMPORTANT: rotate the password after first login on a live server.
        admin = User(
            id=uuid.uuid4(),
            email=_BOOTSTRAP_EMAIL,
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
            "Email: %s\n"
            "Password: %s\n"
            "ROTATE THIS PASSWORD AFTER FIRST LOGIN.\n%s",
            sep,
            _BOOTSTRAP_EMAIL,
            _BOOTSTRAP_PASSWORD,
            sep,
        )
    else:
        # If the bootstrap admin already exists, leave it alone (do not
        # overwrite the password — operator may have already rotated it).
        existing = await session.execute(
            select(User).where(User.email == _BOOTSTRAP_EMAIL)
        )
        if not existing.scalar_one_or_none():
            logger.debug("Bootstrap admin %s not found; non-zero user table — skipping seed.", _BOOTSTRAP_EMAIL)
