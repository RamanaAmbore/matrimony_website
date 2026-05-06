"""DetailRequest ORM model."""
from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    DateTime,
    Enum,
    ForeignKey,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class RequestStatusEnum(str, enum.Enum):
    pending = "pending"
    approved = "approved"
    revoked = "revoked"


class DetailRequest(Base):
    __tablename__ = "detail_requests"
    __table_args__ = (
        UniqueConstraint("requester_user_id", "profile_id", name="uq_request_user_profile"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    # Public-facing identifier: RQ- prefix + 9-digit numeric, total 12 chars,
    # unique across the table. Generated when a request is first created.
    request_number: Mapped[str] = mapped_column(
        String(12), unique=True, nullable=False, default=""
    )
    requester_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    profile_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    status: Mapped[RequestStatusEnum] = mapped_column(
        Enum(RequestStatusEnum, name="request_status_enum"),
        nullable=False,
        default=RequestStatusEnum.pending,
    )
    message: Mapped[str | None] = mapped_column(Text, nullable=True)
    admin_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    responded_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # relationships
    requester: Mapped["User"] = relationship(  # type: ignore[name-defined]
        "User",
        foreign_keys=[requester_user_id],
        back_populates="detail_requests",
    )
    profile: Mapped["Profile"] = relationship("Profile", back_populates="detail_requests")  # type: ignore[name-defined]
