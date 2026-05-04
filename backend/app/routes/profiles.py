"""Profile CRUD routes."""

import asyncio
import random
import uuid
from datetime import date, datetime, time
from typing import Any

from litestar import Controller, delete, get, patch, post
from litestar.connection import Request
from litestar.exceptions import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import MEDIA_ROOT
from app.models.photo import Photo
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
    Profile,
    ProfileStatusEnum,
    TobaccoAlcoholEnum,
)
from app.schemas.profile import ProfileCreateRequest, ProfilePatchRequest
from app.services.keywords import extract_keywords
from app.services.settings import settings_service
from app.services.validation import validate_ascii


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _require_ascii(value: str | None, field: str) -> None:
    """Raise 422 if *value* contains non-ASCII printable characters."""
    if value and not validate_ascii(value):
        raise HTTPException(status_code=422, detail={
            "code": "non_english_input",
            "message": f"'{field.replace('_', ' ').title()}' must be filled in English (ASCII) characters only",
        })


def _compute_age(dob: date) -> int:
    today = date.today()
    return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))


def _photo_urls(photo: Photo, request: Request) -> dict[str, str]:
    base = str(request.base_url).rstrip("/")
    return {
        "passport_url": f"{base}/media/{photo.passport_path}",
        "blurred_url": f"{base}/media/{photo.blurred_path}",
        "thumb_url": f"{base}/media/{photo.thumb_path}",
    }


def _serialize_photo(photo: Photo, request: Request, include_passport: bool = True) -> dict[str, Any]:
    urls = _photo_urls(photo, request)
    return {
        "id": str(photo.id),
        "profile_id": str(photo.profile_id),
        "original_filename": photo.original_filename,
        "passport_url": urls["passport_url"] if include_passport else None,
        "blurred_url": urls["blurred_url"],
        "thumb_url": urls["thumb_url"],
        "byte_size": photo.byte_size,
        "is_primary": photo.is_primary,
        "created_at": photo.created_at.isoformat(),
    }


def _serialize_full_profile(profile: Profile, request: Request) -> dict[str, Any]:
    photos = [_serialize_photo(p, request, include_passport=True) for p in profile.photos]
    return {
        "id": str(profile.id),
        "profile_number": profile.profile_number,
        "owner_user_id": str(profile.owner_user_id),
        "gender": profile.gender.value,
        "first_name": profile.first_name,
        "last_name": profile.last_name,
        "dob": profile.dob.isoformat(),
        "age": _compute_age(profile.dob),
        "height_cm": profile.height_cm,
        "complexion": profile.complexion,
        "education": profile.education,
        "occupation": profile.occupation,
        "annual_income_inr": profile.annual_income_inr,
        "city": profile.city,
        "state": profile.state,
        "pin_code": profile.pin_code,
        "country": profile.country,
        "gotra": profile.gotra,
        "kuldevata": profile.kuldevata,
        "devak": profile.devak,
        "surname_clan": profile.surname_clan,
        "nakshatram": profile.nakshatram,
        "rashi": profile.rashi,
        "manglik": profile.manglik.value if profile.manglik else None,
        "mother_tongue": profile.mother_tongue,
        "diet": profile.diet.value if profile.diet else None,
        "about": profile.about,
        "partner_expectations": profile.partner_expectations,
        "status": profile.status.value,
        "admin_notes": profile.admin_notes,
        # New fields
        "marital_status": profile.marital_status.value if profile.marital_status else None,
        "sub_caste": profile.sub_caste,
        "weight_kg": profile.weight_kg,
        "body_type": profile.body_type.value if profile.body_type else None,
        "blood_group": profile.blood_group.value if profile.blood_group else None,
        "time_of_birth": profile.time_of_birth.isoformat() if profile.time_of_birth else None,
        "place_of_birth": profile.place_of_birth,
        "father_occupation": profile.father_occupation,
        "mother_occupation": profile.mother_occupation,
        "father_name": profile.father_name,
        "mother_name": profile.mother_name,
        "num_family_members": profile.num_family_members,
        "num_brothers": profile.num_brothers,
        "num_sisters": profile.num_sisters,
        "num_brothers_married": profile.num_brothers_married,
        "num_sisters_married": profile.num_sisters_married,
        "family_type": profile.family_type.value if profile.family_type else None,
        "family_status": profile.family_status.value if profile.family_status else None,
        "family_values": profile.family_values.value if profile.family_values else None,
        "native_place": profile.native_place,
        "college_university": profile.college_university,
        "employer": profile.employer,
        "work_location": profile.work_location,
        "smokes": profile.smokes.value if profile.smokes else None,
        "drinks": profile.drinks.value if profile.drinks else None,
        "hobbies": profile.hobbies,
        "partner_preference_keywords": profile.partner_preference_keywords,
        "created_at": profile.created_at.isoformat(),
        "updated_at": profile.updated_at.isoformat(),
        "photos": photos,
    }


def _serialize_partial_profile(profile: Profile, request: Request) -> dict[str, Any]:
    primary = next((p for p in profile.photos if p.is_primary), None)
    if primary is None and profile.photos:
        primary = profile.photos[0]
    base = str(request.base_url).rstrip("/")
    return {
        "id": str(profile.id),
        "gender": profile.gender.value,
        "first_name": profile.first_name[0].upper() + "." if profile.first_name else "",
        "age": _compute_age(profile.dob),
        "height_cm": profile.height_cm,
        "education": profile.education,
        "occupation": profile.occupation,
        "city": profile.city,
        "state": profile.state,
        "gotra": profile.gotra,
        "nakshatram": profile.nakshatram,
        "rashi": profile.rashi,
        "manglik": profile.manglik.value if profile.manglik else None,
        "diet": profile.diet.value if profile.diet else None,
        "mother_tongue": profile.mother_tongue,
        "blurred_url": f"{base}/media/{primary.blurred_path}" if primary else None,
        "thumb_url": f"{base}/media/{primary.thumb_path}" if primary else None,
        # New fields safe for partial view
        "marital_status": profile.marital_status.value if profile.marital_status else None,
        "family_type": profile.family_type.value if profile.family_type else None,
        "smokes": profile.smokes.value if profile.smokes else None,
        "drinks": profile.drinks.value if profile.drinks else None,
    }


def _parse_enum(enum_cls: type, value: str, field: str) -> Any:
    try:
        return enum_cls(value)
    except ValueError:
        valid = [e.value for e in enum_cls]
        raise HTTPException(
            status_code=422,
            detail={"code": "invalid_enum", "message": f"Invalid value for {field}. Must be one of: {valid}"},
        )


def _parse_time(value: str | None, field: str = "time_of_birth") -> time | None:
    """Parse HH:MM or HH:MM:SS string to time object."""
    if value is None:
        return None
    try:
        return time.fromisoformat(value)
    except ValueError:
        raise HTTPException(
            status_code=422,
            detail={"code": "invalid_time", "message": f"{field} must be HH:MM or HH:MM:SS"},
        )


def _validate_free_text_fields(data: ProfileCreateRequest | ProfilePatchRequest) -> None:
    """Validate all free-text and varchar fields are ASCII-only."""
    text_fields: list[tuple[str, str | None]] = [
        ("about", getattr(data, "about", None)),
        ("partner_expectations", getattr(data, "partner_expectations", None)),
        ("hobbies", getattr(data, "hobbies", None)),
        ("first_name", getattr(data, "first_name", None)),
        ("last_name", getattr(data, "last_name", None)),
        ("complexion", getattr(data, "complexion", None)),
        ("education", getattr(data, "education", None)),
        ("occupation", getattr(data, "occupation", None)),
        ("city", getattr(data, "city", None)),
        ("state", getattr(data, "state", None)),
        ("pin_code", getattr(data, "pin_code", None)),
        ("country", getattr(data, "country", None)),
        ("gotra", getattr(data, "gotra", None)),
        ("kuldevata", getattr(data, "kuldevata", None)),
        ("devak", getattr(data, "devak", None)),
        ("surname_clan", getattr(data, "surname_clan", None)),
        ("nakshatram", getattr(data, "nakshatram", None)),
        ("rashi", getattr(data, "rashi", None)),
        ("mother_tongue", getattr(data, "mother_tongue", None)),
        ("sub_caste", getattr(data, "sub_caste", None)),
        ("place_of_birth", getattr(data, "place_of_birth", None)),
        ("father_occupation", getattr(data, "father_occupation", None)),
        ("mother_occupation", getattr(data, "mother_occupation", None)),
        ("father_name", getattr(data, "father_name", None)),
        ("mother_name", getattr(data, "mother_name", None)),
        ("native_place", getattr(data, "native_place", None)),
        ("college_university", getattr(data, "college_university", None)),
        ("employer", getattr(data, "employer", None)),
        ("work_location", getattr(data, "work_location", None)),
    ]
    for field, value in text_fields:
        _require_ascii(value, field)


async def _generate_profile_number(db: AsyncSession) -> str:
    """Generate unique TC-###### profile number."""
    for _ in range(10):  # retry up to 10 times on collision
        num = f"TC-{random.randint(0, 999999):06d}"
        result = await db.execute(select(Profile).where(Profile.profile_number == num))
        if result.scalar_one_or_none() is None:
            return num
    raise RuntimeError("Could not generate unique profile number after 10 attempts")


# ---------------------------------------------------------------------------
# Controller
# ---------------------------------------------------------------------------

class ProfileController(Controller):
    path = "/profiles"

    @get("")
    async def list_my_profiles(
        self,
        request: Request,
        db: AsyncSession,
    ) -> list[dict[str, Any]]:
        user = request.scope.get("user_payload")
        if not user:
            raise HTTPException(status_code=401, detail={"code": "unauthenticated", "message": "Authentication required"})

        result = await db.execute(
            select(Profile)
            .where(Profile.owner_user_id == uuid.UUID(user["sub"]))
            .options(selectinload(Profile.photos))
            .order_by(Profile.created_at.desc())
        )
        profiles = result.scalars().all()
        return [_serialize_full_profile(p, request) for p in profiles]

    @post("", status_code=201)
    async def create_profile(
        self,
        data: ProfileCreateRequest,
        request: Request,
        db: AsyncSession,
    ) -> dict[str, Any]:
        user = request.scope.get("user_payload")
        if not user:
            raise HTTPException(status_code=401, detail={"code": "unauthenticated", "message": "Authentication required"})
        if not user.get("email_verified"):
            raise HTTPException(
                status_code=403,
                detail={"code": "email_not_verified", "message": "Email verification required"},
            )
        if not user.get("is_approved", True):
            raise HTTPException(
                status_code=403,
                detail={"code": "not_approved", "message": "Your account is pending admin approval before you can create profiles."},
            )

        # ASCII validation
        _validate_free_text_fields(data)

        try:
            dob = date.fromisoformat(data.dob)
        except ValueError:
            raise HTTPException(
                status_code=422,
                detail={"code": "invalid_dob", "message": "dob must be an ISO date string (YYYY-MM-DD)"},
            )

        # Extract keywords from partner_expectations
        keywords = extract_keywords(data.partner_expectations) if data.partner_expectations else []

        profile_number = await _generate_profile_number(db)
        profile = Profile(
            id=uuid.uuid4(),
            profile_number=profile_number,
            owner_user_id=uuid.UUID(user["sub"]),
            gender=_parse_enum(GenderEnum, data.gender, "gender"),
            first_name=data.first_name,
            last_name=data.last_name or None,
            dob=dob,
            height_cm=data.height_cm or None,
            complexion=data.complexion or None,
            education=data.education or None,
            occupation=data.occupation or None,
            annual_income_inr=data.annual_income_inr,
            city=data.city or None,
            state=data.state or None,
            pin_code=data.pin_code or None,
            country=data.country or "India",
            gotra=data.gotra or None,
            kuldevata=data.kuldevata or None,
            devak=data.devak or None,
            surname_clan=data.surname_clan or None,
            nakshatram=data.nakshatram or None,
            rashi=data.rashi or None,
            manglik=_parse_enum(ManglikEnum, data.manglik, "manglik") if data.manglik else ManglikEnum.unknown,
            mother_tongue=data.mother_tongue or "Telugu",
            diet=_parse_enum(DietEnum, data.diet, "diet") if data.diet else None,
            about=data.about,
            partner_expectations=data.partner_expectations,
            partner_preference_keywords=keywords or None,
            status=ProfileStatusEnum.draft,
            # New fields
            marital_status=_parse_enum(MaritalStatusEnum, data.marital_status, "marital_status") if data.marital_status else MaritalStatusEnum.never_married,
            sub_caste=data.sub_caste or None,
            weight_kg=data.weight_kg,
            body_type=_parse_enum(BodyTypeEnum, data.body_type, "body_type") if data.body_type else None,
            blood_group=_parse_enum(BloodGroupEnum, data.blood_group, "blood_group") if data.blood_group else None,
            time_of_birth=_parse_time(data.time_of_birth),
            place_of_birth=data.place_of_birth or None,
            father_occupation=data.father_occupation or None,
            mother_occupation=data.mother_occupation or None,
            father_name=data.father_name or None,
            mother_name=data.mother_name or None,
            num_family_members=data.num_family_members,
            num_brothers=data.num_brothers,
            num_sisters=data.num_sisters,
            num_brothers_married=data.num_brothers_married,
            num_sisters_married=data.num_sisters_married,
            family_type=_parse_enum(FamilyTypeEnum, data.family_type, "family_type") if data.family_type else None,
            family_status=_parse_enum(FamilyStatusEnum, data.family_status, "family_status") if data.family_status else None,
            family_values=_parse_enum(FamilyValuesEnum, data.family_values, "family_values") if data.family_values else None,
            native_place=data.native_place or None,
            college_university=data.college_university or None,
            employer=data.employer or None,
            work_location=data.work_location or None,
            smokes=_parse_enum(TobaccoAlcoholEnum, data.smokes, "smokes") if data.smokes else None,
            drinks=_parse_enum(TobaccoAlcoholEnum, data.drinks, "drinks") if data.drinks else None,
            hobbies=data.hobbies or None,
        )
        db.add(profile)
        await db.commit()
        await db.refresh(profile)
        # Load photos (empty at creation)
        await db.refresh(profile, ["photos"])
        return _serialize_full_profile(profile, request)

    @get("/{profile_id:str}")
    async def get_profile(
        self,
        profile_id: str,
        request: Request,
        db: AsyncSession,
    ) -> dict[str, Any]:
        user = request.scope.get("user_payload")

        try:
            pid = uuid.UUID(profile_id)
        except ValueError:
            raise HTTPException(status_code=404, detail={"code": "not_found", "message": "Profile not found"})

        result = await db.execute(
            select(Profile)
            .where(Profile.id == pid)
            .options(selectinload(Profile.photos))
        )
        profile = result.scalar_one_or_none()
        if not profile:
            raise HTTPException(status_code=404, detail={"code": "not_found", "message": "Profile not found"})

        is_owner = user and user["sub"] == str(profile.owner_user_id)
        is_admin = user and user.get("is_admin")

        if is_owner or is_admin:
            full = _serialize_full_profile(profile, request)
            photos_data = full.pop("photos", [])
            return {"profile": full, "photos": photos_data}

        # Non-owner: only approved profiles get partial view
        if profile.status != ProfileStatusEnum.approved:
            raise HTTPException(status_code=404, detail={"code": "not_found", "message": "Profile not found"})

        partial = _serialize_partial_profile(profile, request)
        return {"profile": partial, "photos": []}

    @patch("/{profile_id:str}")
    async def update_profile(
        self,
        profile_id: str,
        data: ProfilePatchRequest,
        request: Request,
        db: AsyncSession,
    ) -> dict[str, Any]:
        user = request.scope.get("user_payload")
        if not user:
            raise HTTPException(status_code=401, detail={"code": "unauthenticated", "message": "Authentication required"})

        try:
            pid = uuid.UUID(profile_id)
        except ValueError:
            raise HTTPException(status_code=404, detail={"code": "not_found", "message": "Profile not found"})

        result = await db.execute(
            select(Profile).where(Profile.id == pid).options(selectinload(Profile.photos))
        )
        profile = result.scalar_one_or_none()
        if not profile:
            raise HTTPException(status_code=404, detail={"code": "not_found", "message": "Profile not found"})

        if str(profile.owner_user_id) != user["sub"] and not user.get("is_admin"):
            raise HTTPException(status_code=403, detail={"code": "forbidden", "message": "Not your profile"})

        # ASCII validation
        _validate_free_text_fields(data)

        changed = False

        # --- Existing fields ---
        if data.gender is not None:
            profile.gender = _parse_enum(GenderEnum, data.gender, "gender")
            changed = True
        if data.first_name is not None:
            profile.first_name = data.first_name
            changed = True
        if data.last_name is not None:
            profile.last_name = data.last_name
            changed = True
        if data.dob is not None:
            try:
                profile.dob = date.fromisoformat(data.dob)
            except ValueError:
                raise HTTPException(status_code=422, detail={"code": "invalid_dob", "message": "dob must be YYYY-MM-DD"})
            changed = True
        if data.height_cm is not None:
            profile.height_cm = data.height_cm
            changed = True
        if data.complexion is not None:
            profile.complexion = data.complexion
            changed = True
        if data.education is not None:
            profile.education = data.education
            changed = True
        if data.occupation is not None:
            profile.occupation = data.occupation
            changed = True
        if data.annual_income_inr is not None:
            profile.annual_income_inr = data.annual_income_inr
            changed = True
        if data.city is not None:
            profile.city = data.city
            changed = True
        if data.state is not None:
            profile.state = data.state
            changed = True
        if data.pin_code is not None:
            profile.pin_code = data.pin_code
            changed = True
        if data.country is not None:
            profile.country = data.country
            changed = True
        if data.gotra is not None:
            profile.gotra = data.gotra
            changed = True
        if data.kuldevata is not None:
            profile.kuldevata = data.kuldevata
            changed = True
        if data.devak is not None:
            profile.devak = data.devak
            changed = True
        if data.surname_clan is not None:
            profile.surname_clan = data.surname_clan
            changed = True
        if data.nakshatram is not None:
            profile.nakshatram = data.nakshatram
            changed = True
        if data.rashi is not None:
            profile.rashi = data.rashi
            changed = True
        if data.manglik is not None:
            profile.manglik = _parse_enum(ManglikEnum, data.manglik, "manglik")
            changed = True
        if data.mother_tongue is not None:
            profile.mother_tongue = data.mother_tongue
            changed = True
        if data.diet is not None:
            profile.diet = _parse_enum(DietEnum, data.diet, "diet")
            changed = True
        if data.about is not None:
            profile.about = data.about
            changed = True
        if data.partner_expectations is not None:
            profile.partner_expectations = data.partner_expectations
            profile.partner_preference_keywords = extract_keywords(data.partner_expectations) or None
            changed = True

        # --- New fields ---
        if data.marital_status is not None:
            profile.marital_status = _parse_enum(MaritalStatusEnum, data.marital_status, "marital_status")
            changed = True
        if data.sub_caste is not None:
            profile.sub_caste = data.sub_caste
            changed = True
        if data.weight_kg is not None:
            profile.weight_kg = data.weight_kg
            changed = True
        if data.body_type is not None:
            profile.body_type = _parse_enum(BodyTypeEnum, data.body_type, "body_type")
            changed = True
        if data.blood_group is not None:
            profile.blood_group = _parse_enum(BloodGroupEnum, data.blood_group, "blood_group")
            changed = True
        if data.time_of_birth is not None:
            profile.time_of_birth = _parse_time(data.time_of_birth)
            changed = True
        if data.place_of_birth is not None:
            profile.place_of_birth = data.place_of_birth
            changed = True
        if data.father_occupation is not None:
            profile.father_occupation = data.father_occupation
            changed = True
        if data.mother_occupation is not None:
            profile.mother_occupation = data.mother_occupation
            changed = True
        if data.father_name is not None:
            profile.father_name = data.father_name
            changed = True
        if data.mother_name is not None:
            profile.mother_name = data.mother_name
            changed = True
        if data.num_family_members is not None:
            profile.num_family_members = data.num_family_members
            changed = True
        if data.num_brothers is not None:
            profile.num_brothers = data.num_brothers
            changed = True
        if data.num_sisters is not None:
            profile.num_sisters = data.num_sisters
            changed = True
        if data.num_brothers_married is not None:
            profile.num_brothers_married = data.num_brothers_married
            changed = True
        if data.num_sisters_married is not None:
            profile.num_sisters_married = data.num_sisters_married
            changed = True
        if data.family_type is not None:
            profile.family_type = _parse_enum(FamilyTypeEnum, data.family_type, "family_type")
            changed = True
        if data.family_status is not None:
            profile.family_status = _parse_enum(FamilyStatusEnum, data.family_status, "family_status")
            changed = True
        if data.family_values is not None:
            profile.family_values = _parse_enum(FamilyValuesEnum, data.family_values, "family_values")
            changed = True
        if data.native_place is not None:
            profile.native_place = data.native_place
            changed = True
        if data.college_university is not None:
            profile.college_university = data.college_university
            changed = True
        if data.employer is not None:
            profile.employer = data.employer
            changed = True
        if data.work_location is not None:
            profile.work_location = data.work_location
            changed = True
        if data.smokes is not None:
            profile.smokes = _parse_enum(TobaccoAlcoholEnum, data.smokes, "smokes")
            changed = True
        if data.drinks is not None:
            profile.drinks = _parse_enum(TobaccoAlcoholEnum, data.drinks, "drinks")
            changed = True
        if data.hobbies is not None:
            profile.hobbies = data.hobbies
            changed = True

        # If the profile was approved or rejected and is now being edited, reset to
        # pending so an admin re-reviews the updated content.
        if changed and profile.status in (ProfileStatusEnum.approved, ProfileStatusEnum.rejected):
            profile.status = ProfileStatusEnum.pending

        await db.commit()
        await db.refresh(profile)
        await db.refresh(profile, ["photos"])
        return _serialize_full_profile(profile, request)

    @delete("/{profile_id:str}", status_code=204)
    async def delete_profile(
        self,
        profile_id: str,
        request: Request,
        db: AsyncSession,
    ) -> None:
        user = request.scope.get("user_payload")
        if not user:
            raise HTTPException(status_code=401, detail={"code": "unauthenticated", "message": "Authentication required"})

        try:
            pid = uuid.UUID(profile_id)
        except ValueError:
            raise HTTPException(status_code=404, detail={"code": "not_found", "message": "Profile not found"})

        result = await db.execute(select(Profile).where(Profile.id == pid))
        profile = result.scalar_one_or_none()
        if not profile:
            raise HTTPException(status_code=404, detail={"code": "not_found", "message": "Profile not found"})

        is_owner = str(profile.owner_user_id) == user["sub"]
        is_admin = bool(user.get("is_admin"))

        if not is_owner and not is_admin:
            raise HTTPException(status_code=403, detail={"code": "forbidden", "message": "Not your profile"})

        # Non-admins may only delete profiles that are draft or rejected.
        # An approved profile is live on the platform; require admin action to remove it.
        if is_owner and not is_admin and profile.status == ProfileStatusEnum.approved:
            raise HTTPException(
                status_code=409,
                detail={"code": "invalid_status", "message": "Approved profiles cannot be deleted; contact the admin"},
            )

        await db.delete(profile)
        await db.commit()

    @post("/{profile_id:str}/submit")
    async def submit_profile(
        self,
        profile_id: str,
        request: Request,
        db: AsyncSession,
    ) -> dict[str, Any]:
        user = request.scope.get("user_payload")
        if not user:
            raise HTTPException(status_code=401, detail={"code": "unauthenticated", "message": "Authentication required"})

        try:
            pid = uuid.UUID(profile_id)
        except ValueError:
            raise HTTPException(status_code=404, detail={"code": "not_found", "message": "Profile not found"})

        result = await db.execute(
            select(Profile).where(Profile.id == pid).options(selectinload(Profile.photos))
        )
        profile = result.scalar_one_or_none()
        if not profile:
            raise HTTPException(status_code=404, detail={"code": "not_found", "message": "Profile not found"})

        if str(profile.owner_user_id) != user["sub"]:
            raise HTTPException(status_code=403, detail={"code": "forbidden", "message": "Not your profile"})

        if profile.status not in (ProfileStatusEnum.draft, ProfileStatusEnum.rejected):
            raise HTTPException(
                status_code=409,
                detail={"code": "invalid_status", "message": f"Profile is already in '{profile.status.value}' status"},
            )

        require_approval = settings_service.get_bool("require_admin_approval_for_profiles", True)
        if require_approval:
            profile.status = ProfileStatusEnum.pending
        else:
            profile.status = ProfileStatusEnum.approved

        await db.commit()
        await db.refresh(profile)
        await db.refresh(profile, ["photos"])

        from app.services.telegram import notify_profile_submitted, notify_profile_approved
        from app.services import email as email_svc
        asyncio.create_task(notify_profile_submitted(
            profile_id=str(profile.id),
            name=f"{profile.first_name} {profile.last_name or ''}".strip(),
            gender=profile.gender.value if profile.gender else "unknown",
        ))

        if not require_approval:
            asyncio.create_task(notify_profile_approved(
                name=f"{profile.first_name} {profile.last_name or ''}".strip(),
                admin_notes="Auto-approved",
            ))

        asyncio.create_task(email_svc.send_admin_profile_submitted(
            profile_name=f"{profile.first_name} {profile.last_name or ''}".strip(),
            gender=profile.gender.value if profile.gender else "unknown",
            age=_compute_age(profile.dob),
            city=profile.city or "",
            state=profile.state or "",
            gotra=profile.gotra or "",
            occupation=profile.occupation or "",
            profile_id=str(profile.id),
        ))

        return _serialize_full_profile(profile, request)
