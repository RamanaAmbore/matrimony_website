"""Profile CRUD routes."""

import uuid
from datetime import date, datetime
from typing import Any

from litestar import Controller, delete, get, patch, post
from litestar.connection import Request
from litestar.exceptions import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import MEDIA_ROOT
from app.models.photo import Photo
from app.models.profile import Profile, ProfileStatusEnum
from app.schemas.profile import ProfileCreateRequest, ProfilePatchRequest
from app.services.settings import settings_service


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
        "country": profile.country,
        "gotra": profile.gotra,
        "kuldevata": profile.kuldevata,
        "devak": profile.devak,
        "surname_clan": profile.surname_clan,
        "nakshatram": profile.nakshatram,
        "rashi": profile.rashi,
        "manglik": profile.manglik.value,
        "mother_tongue": profile.mother_tongue,
        "diet": profile.diet.value,
        "about": profile.about,
        "partner_expectations": profile.partner_expectations,
        "status": profile.status.value,
        "admin_notes": profile.admin_notes,
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
        "manglik": profile.manglik.value,
        "diet": profile.diet.value,
        "mother_tongue": profile.mother_tongue,
        "blurred_url": f"{base}/media/{primary.blurred_path}" if primary else None,
        "thumb_url": f"{base}/media/{primary.thumb_path}" if primary else None,
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


class ProfileController(Controller):
    path = "/profiles"

    @get("")
    async def list_my_profiles(
        self,
        request: Request,
        db: AsyncSession,
    ) -> list[dict[str, Any]]:
        user = request.session.get("user")
        if not user:
            raise HTTPException(status_code=401, detail={"code": "unauthenticated", "message": "Authentication required"})

        result = await db.execute(
            select(Profile)
            .where(Profile.owner_user_id == uuid.UUID(user["user_id"]))
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
        user = request.session.get("user")
        if not user:
            raise HTTPException(status_code=401, detail={"code": "unauthenticated", "message": "Authentication required"})
        if not user.get("email_verified"):
            raise HTTPException(
                status_code=403,
                detail={"code": "email_not_verified", "message": "Email verification required"},
            )

        from app.models.profile import DietEnum, GenderEnum, ManglikEnum

        try:
            dob = date.fromisoformat(data.dob)
        except ValueError:
            raise HTTPException(
                status_code=422,
                detail={"code": "invalid_dob", "message": "dob must be an ISO date string (YYYY-MM-DD)"},
            )

        profile = Profile(
            id=uuid.uuid4(),
            owner_user_id=uuid.UUID(user["user_id"]),
            gender=_parse_enum(GenderEnum, data.gender, "gender"),
            first_name=data.first_name,
            last_name=data.last_name,
            dob=dob,
            height_cm=data.height_cm,
            complexion=data.complexion,
            education=data.education,
            occupation=data.occupation,
            annual_income_inr=data.annual_income_inr,
            city=data.city,
            state=data.state,
            country=data.country,
            gotra=data.gotra,
            kuldevata=data.kuldevata,
            devak=data.devak,
            surname_clan=data.surname_clan,
            nakshatram=data.nakshatram,
            rashi=data.rashi,
            manglik=_parse_enum(ManglikEnum, data.manglik, "manglik"),
            mother_tongue=data.mother_tongue,
            diet=_parse_enum(DietEnum, data.diet, "diet"),
            about=data.about,
            partner_expectations=data.partner_expectations,
            status=ProfileStatusEnum.draft,
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
        user = request.session.get("user")

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

        is_owner = user and user["user_id"] == str(profile.owner_user_id)
        is_admin = user and user.get("is_admin")

        if is_owner or is_admin:
            return _serialize_full_profile(profile, request)

        # Non-owner: only approved profiles get partial view
        if profile.status != ProfileStatusEnum.approved:
            raise HTTPException(status_code=404, detail={"code": "not_found", "message": "Profile not found"})

        return _serialize_partial_profile(profile, request)

    @patch("/{profile_id:str}")
    async def update_profile(
        self,
        profile_id: str,
        data: ProfilePatchRequest,
        request: Request,
        db: AsyncSession,
    ) -> dict[str, Any]:
        user = request.session.get("user")
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

        if str(profile.owner_user_id) != user["user_id"]:
            raise HTTPException(status_code=403, detail={"code": "forbidden", "message": "Not your profile"})

        from app.models.profile import DietEnum, GenderEnum, ManglikEnum

        changed = False
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
            changed = True

        # If was approved and now changed, reset to pending
        if changed and profile.status == ProfileStatusEnum.approved:
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
        user = request.session.get("user")
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

        if str(profile.owner_user_id) != user["user_id"] and not user.get("is_admin"):
            raise HTTPException(status_code=403, detail={"code": "forbidden", "message": "Not your profile"})

        await db.delete(profile)
        await db.commit()

    @post("/{profile_id:str}/submit")
    async def submit_profile(
        self,
        profile_id: str,
        request: Request,
        db: AsyncSession,
    ) -> dict[str, Any]:
        user = request.session.get("user")
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

        if str(profile.owner_user_id) != user["user_id"]:
            raise HTTPException(status_code=403, detail={"code": "forbidden", "message": "Not your profile"})

        if profile.status != ProfileStatusEnum.draft:
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
        return _serialize_full_profile(profile, request)
