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
_BOOTSTRAP_EMAIL = "ramanaamborespam@gmail.com"
_BOOTSTRAP_PHONE = "+91 9840770711"
_BOOTSTRAP_PASSWORD = "rambo1234"

# Legacy emails we still recognize as the bootstrap admin so old installs can
# be migrated forward without losing the row.
_LEGACY_EMAILS = ("rambo@marathakalyanam.com", "ramanamborespam@gmail.com")


async def bootstrap(session: AsyncSession) -> None:
    """Run once on startup: seed defaults and create admin if needed."""
    await settings_service.seed_defaults(session)

    result = await session.execute(select(func.count()).select_from(User))
    user_count = result.scalar_one()

    if user_count == 0:
        admin = User(
            id=uuid.uuid4(),
            email=_BOOTSTRAP_EMAIL,
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
            "Handle: %s\n"
            "Email: %s\n"
            "Phone: %s\n"
            "Password: %s\n"
            "ROTATE THIS PASSWORD AFTER FIRST LOGIN.\n%s",
            sep,
            _BOOTSTRAP_HANDLE,
            _BOOTSTRAP_EMAIL,
            _BOOTSTRAP_PHONE,
            _BOOTSTRAP_PASSWORD,
            sep,
        )
        return

    # Backfill / migrate the existing bootstrap row in place. Look it up by
    # handle first, then by any of the legacy emails. Password is never
    # overwritten — operator may have rotated it.
    candidate_emails = (_BOOTSTRAP_EMAIL, *_LEGACY_EMAILS)
    existing = await session.execute(
        select(User).where(
            (func.lower(User.user_handle) == _BOOTSTRAP_HANDLE)
            | (User.email.in_(candidate_emails))
        )
    )
    existing_user = existing.scalars().first()
    if not existing_user:
        logger.debug(
            "Bootstrap admin not found by handle/email; skipping seed (other users exist)."
        )
        return

    changed = False
    if not existing_user.user_handle:
        existing_user.user_handle = _BOOTSTRAP_HANDLE
        changed = True
    if existing_user.email in _LEGACY_EMAILS:
        existing_user.email = _BOOTSTRAP_EMAIL
        changed = True
    if not existing_user.phone_number or existing_user.phone_number.startswith("+00"):
        existing_user.phone_number = _BOOTSTRAP_PHONE
        changed = True
    if changed:
        await session.commit()
        logger.info(
            "Bootstrap admin reconciled: handle=%s email=%s phone=%s",
            existing_user.user_handle,
            existing_user.email,
            existing_user.phone_number,
        )
