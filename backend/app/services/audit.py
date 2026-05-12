"""Audit log service helper.

Provides a single ``log()`` coroutine that inserts an AuditLog row into the
current SQLAlchemy session WITHOUT committing — the caller's transaction
commit is responsible. This keeps the audit row atomic with the action it
records.

Usage::

    from app.services.audit import log as audit_log
    await audit_log(db, actor_user_id=admin.id, target_user_id=target.id,
                    action="password_reset_admin", metadata={"actor_handle": admin.user_handle})
    # db commit happens in the route handler / Litestar DI layer
"""
from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog


async def log(
    db: AsyncSession,
    *,
    actor_user_id: uuid.UUID,
    target_user_id: uuid.UUID | None = None,
    action: str,
    metadata: dict[str, Any] | None = None,
) -> None:
    """Insert an AuditLog row. Does NOT commit — caller's transaction commits."""
    entry = AuditLog(
        actor_user_id=actor_user_id,
        target_user_id=target_user_id,
        action=action,
        audit_metadata=metadata,
    )
    db.add(entry)
