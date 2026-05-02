"""Profile ORM model."""
from __future__ import annotations

import enum
import uuid
from datetime import date, datetime, time

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
    Time,
    func,
)
from sqlalchemy.dialects.postgresql import JSON, UUID
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
    jain = "jain"
    vegan = "vegan"


class ProfileStatusEnum(str, enum.Enum):
    draft = "draft"
    pending = "pending"
    approved = "approved"
    rejected = "rejected"


class MaritalStatusEnum(str, enum.Enum):
    never_married = "never_married"
    divorced = "divorced"
    widowed = "widowed"
    awaiting_divorce = "awaiting_divorce"


class BodyTypeEnum(str, enum.Enum):
    slim = "slim"
    average = "average"
    athletic = "athletic"
    heavy = "heavy"


class BloodGroupEnum(str, enum.Enum):
    a_pos = "A+"
    a_neg = "A-"
    b_pos = "B+"
    b_neg = "B-"
    ab_pos = "AB+"
    ab_neg = "AB-"
    o_pos = "O+"
    o_neg = "O-"
    unknown = "unknown"


class FamilyTypeEnum(str, enum.Enum):
    nuclear = "nuclear"
    joint = "joint"


class FamilyStatusEnum(str, enum.Enum):
    middle_class = "middle_class"
    upper_middle = "upper_middle"
    affluent = "affluent"
    rich = "rich"


class FamilyValuesEnum(str, enum.Enum):
    orthodox = "orthodox"
    traditional = "traditional"
    moderate = "moderate"
    liberal = "liberal"


class TobaccoAlcoholEnum(str, enum.Enum):
    no = "no"
    occasionally = "occasionally"
    yes = "yes"


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

    # --- New columns ---
    marital_status: Mapped[MaritalStatusEnum] = mapped_column(
        Enum(MaritalStatusEnum, name="marital_status_enum"),
        nullable=False,
        default=MaritalStatusEnum.never_married,
        server_default="never_married",
    )
    sub_caste: Mapped[str | None] = mapped_column(String(100), nullable=True)
    weight_kg: Mapped[int | None] = mapped_column(Integer, nullable=True)
    body_type: Mapped[BodyTypeEnum | None] = mapped_column(
        Enum(BodyTypeEnum, name="body_type_enum"), nullable=True
    )
    blood_group: Mapped[BloodGroupEnum | None] = mapped_column(
        Enum(BloodGroupEnum, name="blood_group_enum"), nullable=True
    )
    time_of_birth: Mapped[time | None] = mapped_column(Time, nullable=True)
    place_of_birth: Mapped[str | None] = mapped_column(String(150), nullable=True)
    father_occupation: Mapped[str | None] = mapped_column(String(150), nullable=True)
    mother_occupation: Mapped[str | None] = mapped_column(String(150), nullable=True)
    num_brothers: Mapped[int | None] = mapped_column(Integer, nullable=True)
    num_sisters: Mapped[int | None] = mapped_column(Integer, nullable=True)
    num_brothers_married: Mapped[int | None] = mapped_column(Integer, nullable=True)
    num_sisters_married: Mapped[int | None] = mapped_column(Integer, nullable=True)
    family_type: Mapped[FamilyTypeEnum | None] = mapped_column(
        Enum(FamilyTypeEnum, name="family_type_enum"), nullable=True
    )
    family_status: Mapped[FamilyStatusEnum | None] = mapped_column(
        Enum(FamilyStatusEnum, name="family_status_enum"), nullable=True
    )
    family_values: Mapped[FamilyValuesEnum | None] = mapped_column(
        Enum(FamilyValuesEnum, name="family_values_enum"), nullable=True
    )
    native_place: Mapped[str | None] = mapped_column(String(150), nullable=True)
    college_university: Mapped[str | None] = mapped_column(String(200), nullable=True)
    employer: Mapped[str | None] = mapped_column(String(200), nullable=True)
    work_location: Mapped[str | None] = mapped_column(String(150), nullable=True)
    smokes: Mapped[TobaccoAlcoholEnum | None] = mapped_column(
        Enum(TobaccoAlcoholEnum, name="tobacco_alcohol_enum"), nullable=True
    )
    drinks: Mapped[TobaccoAlcoholEnum | None] = mapped_column(
        # Reuse same enum type — pass create_constraint=False so SQLAlchemy doesn't
        # try to create a second type named tobacco_alcohol_enum for this column.
        Enum(TobaccoAlcoholEnum, name="tobacco_alcohol_enum", create_constraint=False),
        nullable=True,
    )
    hobbies: Mapped[str | None] = mapped_column(Text, nullable=True)
    partner_preference_keywords: Mapped[list | None] = mapped_column(
        JSON, nullable=True
    )

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
