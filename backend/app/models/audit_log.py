"""AuditLog ORM model — records security-sensitive actions (impersonation, password resets, etc.)."""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class AuditLog(Base):
    __tablename__ = "audit_log"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    actor_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    target_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    action: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    # Column named "audit_metadata" at Python level to avoid clash with
    # SQLAlchemy's reserved `metadata` attribute on Base. Maps to DB column
    # also named audit_metadata.
    audit_metadata: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )

    # relationships (lazy-loaded; only used in the audit-log list endpoint)
    actor: Mapped["User"] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "User", foreign_keys=[actor_user_id], lazy="select"
    )
    target: Mapped["User | None"] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "User", foreign_keys=[target_user_id], lazy="select"
    )
