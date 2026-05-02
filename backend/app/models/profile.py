"""Profile ORM model."""
from __future__ import annotations

import enum
import uuid
from datetime import date, datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class GenderEnum(str, enum.Enum):
    bride = "bride"
    groom = "groom"


class ManglikEnum(str, enum.Enum):
    yes = "yes"
    no = "no"
    partial = "partial"
    unknown = "unknown"


class DietEnum(str, enum.Enum):
    veg = "veg"
    non_veg = "non-veg"
    eggetarian = "eggetarian"


class ProfileStatusEnum(str, enum.Enum):
    draft = "draft"
    pending = "pending"
    approved = "approved"
    rejected = "rejected"


class Profile(Base):
    __tablename__ = "profiles"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    owner_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    gender: Mapped[GenderEnum] = mapped_column(
        Enum(GenderEnum, name="gender_enum"), nullable=False
    )
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    dob: Mapped[date] = mapped_column(Date, nullable=False)
    height_cm: Mapped[int] = mapped_column(Integer, nullable=False)
    complexion: Mapped[str] = mapped_column(String(50), nullable=False)
    education: Mapped[str] = mapped_column(String(200), nullable=False)
    occupation: Mapped[str] = mapped_column(String(200), nullable=False)
    annual_income_inr: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    city: Mapped[str] = mapped_column(String(100), nullable=False)
    state: Mapped[str] = mapped_column(String(100), nullable=False)
    country: Mapped[str] = mapped_column(String(100), nullable=False, default="India")
    gotra: Mapped[str] = mapped_column(String(100), nullable=False)
    kuldevata: Mapped[str] = mapped_column(String(100), nullable=False)
    devak: Mapped[str] = mapped_column(String(100), nullable=False)
    surname_clan: Mapped[str] = mapped_column(String(100), nullable=False)
    nakshatram: Mapped[str] = mapped_column(String(100), nullable=False)
    rashi: Mapped[str] = mapped_column(String(100), nullable=False)
    manglik: Mapped[ManglikEnum] = mapped_column(
        Enum(ManglikEnum, name="manglik_enum"), nullable=False, default=ManglikEnum.unknown
    )
    mother_tongue: Mapped[str] = mapped_column(String(50), nullable=False, default="Telugu")
    diet: Mapped[DietEnum] = mapped_column(
        Enum(DietEnum, name="diet_enum"), nullable=False
    )
    about: Mapped[str] = mapped_column(Text, nullable=False, default="")
    partner_expectations: Mapped[str] = mapped_column(Text, nullable=False, default="")
    status: Mapped[ProfileStatusEnum] = mapped_column(
        Enum(ProfileStatusEnum, name="profile_status_enum"),
        nullable=False,
        default=ProfileStatusEnum.draft,
    )
    admin_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
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
    owner: Mapped["User"] = relationship("User", back_populates="profiles")  # type: ignore[name-defined]
    photos: Mapped[list["Photo"]] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "Photo", back_populates="profile", cascade="all, delete-orphan", order_by="Photo.created_at"
    )
    detail_requests: Mapped[list["DetailRequest"]] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "DetailRequest", back_populates="profile", cascade="all, delete-orphan"
    )
