"""User ORM model."""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Index, String, func, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class User(Base):
    __tablename__ = "users"

    __table_args__ = (
        # Functional unique index for case-insensitive uniqueness on user_handle.
        # PostgreSQL-specific; enforces lower(user_handle) UNIQUE.
        Index("ix_users_user_handle_lower", text("lower(user_handle)"), unique=True),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    full_name: Mapped[str] = mapped_column(String(120), nullable=False, default="")
    user_handle: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    phone_number: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(512), nullable=False)
    email_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_approved: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    email_verification_token: Mapped[str | None] = mapped_column(String(64), nullable=True)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    # Super-user role: above admin. Hidden from admin-facing lists. Only super
    # can delete/demote admin users. There is exactly one super user
    # (seeded in bootstrap), and they cannot be deleted.
    is_super: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    # Soft-revoke: admin ban. Blocks login. Distinct from is_approved
    # (which only governs new-profile creation).
    is_revoked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    # Vacation mode — user-controlled toggle. Paused users CAN still log in
    # (they get a banner) but their profiles drop out of search and they
    # can't create new profiles. The user themselves can flip this on/off.
    is_paused: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    # Admin enforcement hold — admin-controlled. Same search/creation
    # consequences as is_paused, but only admin can clear it. Useful when
    # admin needs to investigate without escalating to a full ban.
    is_suspended: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # relationships
    profiles: Mapped[list["Profile"]] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "Profile", back_populates="owner", cascade="all, delete-orphan"
    )
    detail_requests: Mapped[list["DetailRequest"]] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "DetailRequest",
        foreign_keys="DetailRequest.requester_user_id",
        back_populates="requester",
        cascade="all, delete-orphan",
    )
