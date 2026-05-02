"""Profile schemas."""
from __future__ import annotations

from datetime import date, datetime
from typing import Any

import msgspec

from app.models.profile import DietEnum, GenderEnum, ManglikEnum, ProfileStatusEnum


class ProfileCreateRequest(msgspec.Struct, kw_only=True):
    gender: str
    first_name: str
    last_name: str
    dob: str  # ISO date string
    height_cm: int
    complexion: str
    education: str
    occupation: str
    annual_income_inr: int | None = None
    city: str
    state: str
    country: str = "India"
    gotra: str
    kuldevata: str
    devak: str
    surname_clan: str
    nakshatram: str
    rashi: str
    manglik: str = "unknown"
    mother_tongue: str = "Telugu"
    diet: str
    about: str = ""
    partner_expectations: str = ""


class ProfilePatchRequest(msgspec.Struct, kw_only=True):
    gender: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    dob: str | None = None
    height_cm: int | None = None
    complexion: str | None = None
    education: str | None = None
    occupation: str | None = None
    annual_income_inr: int | None = None
    city: str | None = None
    state: str | None = None
    country: str | None = None
    gotra: str | None = None
    kuldevata: str | None = None
    devak: str | None = None
    surname_clan: str | None = None
    nakshatram: str | None = None
    rashi: str | None = None
    manglik: str | None = None
    mother_tongue: str | None = None
    diet: str | None = None
    about: str | None = None
    partner_expectations: str | None = None


class PhotoSchema(msgspec.Struct):
    id: str
    profile_id: str
    original_filename: str
    passport_url: str
    blurred_url: str
    thumb_url: str
    byte_size: int
    is_primary: bool
    created_at: str


class FullProfileResponse(msgspec.Struct):
    id: str
    owner_user_id: str
    gender: str
    first_name: str
    last_name: str
    dob: str
    age: int
    height_cm: int
    complexion: str
    education: str
    occupation: str
    annual_income_inr: int | None
    city: str
    state: str
    country: str
    gotra: str
    kuldevata: str
    devak: str
    surname_clan: str
    nakshatram: str
    rashi: str
    manglik: str
    mother_tongue: str
    diet: str
    about: str
    partner_expectations: str
    status: str
    admin_notes: str | None
    created_at: str
    updated_at: str
    photos: list[PhotoSchema]


class PartialProfileResponse(msgspec.Struct):
    """Redacted profile for search results and non-approved viewers."""
    id: str
    gender: str
    first_name: str  # initial only e.g. "R."
    age: int
    height_cm: int
    education: str
    occupation: str
    city: str
    state: str
    gotra: str
    nakshatram: str
    rashi: str
    manglik: str
    diet: str
    mother_tongue: str
    blurred_url: str | None
    thumb_url: str | None
