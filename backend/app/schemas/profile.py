"""Profile schemas."""
from __future__ import annotations

from typing import Any

import msgspec

from app.models.profile import (
    BloodGroupEnum,
    BodyTypeEnum,
    DietEnum,
    FamilyStatusEnum,
    FamilyTypeEnum,
    FamilyValuesEnum,
    GenderEnum,
    ManglikEnum,
    MaritalStatusEnum,
    ProfileStatusEnum,
    TobaccoAlcoholEnum,
)


class ProfileCreateRequest(msgspec.Struct, kw_only=True):
    # --- Always required (wizard section 1) ---
    gender: str
    first_name: str
    last_name: str
    dob: str  # ISO date string YYYY-MM-DD

    # --- Required contact (defaults from User; user can edit, can't blank) ---
    contact_phone: str
    contact_email: str

    # --- Optional at creation — filled across wizard sections ---
    height_cm: int | None = None
    complexion: str | None = None
    education: str | None = None
    occupation: str | None = None
    city: str | None = None
    state: str | None = None
    gotra: str | None = None
    kuldevata: str | None = None
    devak: str | None = None
    surname_clan: str | None = None
    nakshatram: str | None = None
    rashi: str | None = None
    diet: str | None = None

    # --- Existing optional fields ---
    annual_income_inr: int | None = None
    country: str = "India"
    pin_code: str | None = None
    manglik: str = "unknown"
    mother_tongue: str = "Telugu"
    about: str = ""
    partner_expectations: str = ""

    # --- New fields ---
    marital_status: str = "never_married"
    caste: str | None = None
    sub_caste: str | None = None
    weight_kg: int | None = None
    body_type: str | None = None
    blood_group: str | None = None
    time_of_birth: str | None = None  # HH:MM or HH:MM:SS string
    place_of_birth: str | None = None
    father_occupation: str | None = None
    mother_occupation: str | None = None
    father_name: str | None = None
    mother_name: str | None = None
    num_family_members: int | None = None
    num_brothers: int | None = None
    num_sisters: int | None = None
    num_brothers_married: int | None = None
    num_sisters_married: int | None = None
    family_type: str | None = None
    family_status: str | None = None
    family_values: str | None = None
    native_place: str | None = None
    college_university: str | None = None
    employer: str | None = None
    work_location: str | None = None
    smokes: str | None = None
    drinks: str | None = None
    hobbies: str | None = None


class ProfilePatchRequest(msgspec.Struct, kw_only=True):
    # --- Existing fields ---
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
    pin_code: str | None = None
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

    # --- New fields ---
    marital_status: str | None = None
    caste: str | None = None
    sub_caste: str | None = None
    weight_kg: int | None = None
    body_type: str | None = None
    blood_group: str | None = None
    time_of_birth: str | None = None
    place_of_birth: str | None = None
    father_occupation: str | None = None
    mother_occupation: str | None = None
    father_name: str | None = None
    mother_name: str | None = None
    num_family_members: int | None = None
    num_brothers: int | None = None
    num_sisters: int | None = None
    num_brothers_married: int | None = None
    num_sisters_married: int | None = None
    family_type: str | None = None
    family_status: str | None = None
    family_values: str | None = None
    native_place: str | None = None
    college_university: str | None = None
    employer: str | None = None
    work_location: str | None = None
    smokes: str | None = None
    drinks: str | None = None
    hobbies: str | None = None
    contact_phone: str | None = None
    contact_email: str | None = None


class PhotoSchema(msgspec.Struct):
    id: str
    profile_id: str
    original_filename: str
    passport_url: str | None
    blurred_url: str
    thumb_url: str
    byte_size: int
    is_primary: bool
    created_at: str


class FullProfileResponse(msgspec.Struct):
    # --- Existing fields ---
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
    pin_code: str | None
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

    # --- New fields ---
    marital_status: str
    caste: str | None
    sub_caste: str | None
    weight_kg: int | None
    body_type: str | None
    blood_group: str | None
    time_of_birth: str | None
    place_of_birth: str | None
    father_occupation: str | None
    mother_occupation: str | None
    father_name: str | None
    mother_name: str | None
    num_family_members: int | None
    num_brothers: int | None
    num_sisters: int | None
    num_brothers_married: int | None
    num_sisters_married: int | None
    family_type: str | None
    family_status: str | None
    family_values: str | None
    native_place: str | None
    college_university: str | None
    employer: str | None
    work_location: str | None
    smokes: str | None
    drinks: str | None
    hobbies: str | None
    partner_preference_keywords: list[str] | None


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
    # New fields exposed in partial view (safe to share)
    marital_status: str
    family_type: str | None
    smokes: str | None
    drinks: str | None
