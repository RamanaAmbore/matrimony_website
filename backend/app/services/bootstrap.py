"""Bootstrap: seed admin user and settings on first startup."""
from __future__ import annotations

import logging
import secrets
import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import OWNER_EMAIL
from app.models.user import User
from app.services.auth import hash_password
from app.services.settings import settings_service

logger = logging.getLogger(__name__)


async def bootstrap(session: AsyncSession) -> None:
    """Run once on startup: seed defaults and create admin if needed."""
    # Seed settings defaults
    await settings_service.seed_defaults(session)

    # Check if any users exist
    result = await session.execute(select(func.count()).select_from(User))
    user_count = result.scalar_one()

    if user_count == 0:
        # Create bootstrap admin
        temp_password = secrets.token_urlsafe(16)
        reset_token = secrets.token_urlsafe(32)

        admin = User(
            id=uuid.uuid4(),
            email=OWNER_EMAIL,
            password_hash=hash_password(temp_password),
            email_verified=True,
            is_admin=True,
            email_verification_token=reset_token,
        )
        session.add(admin)
        await session.commit()

        sep = "=" * 60
        logger.warning(
            "\n%s\nBOOTSTRAP ADMIN CREATED\n"
            "Email: %s\n"
            "Temporary password: %s\n"
            "One-time reset token: %s\n"
            "Change your password immediately after first login.\n%s",
            sep,
            OWNER_EMAIL,
            temp_password,
            reset_token,
            sep,
        )
