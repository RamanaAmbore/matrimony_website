"""Search routes."""
from datetime import date
from typing import Annotated, Any, Optional, Union

from litestar import Controller, get
from litestar.connection import Request
from litestar.params import Parameter
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.profile import (
    DietEnum,
    FamilyTypeEnum,
    GenderEnum,
    ManglikEnum,
    MaritalStatusEnum,
    Profile,
    ProfileStatusEnum,
    TobaccoAlcoholEnum,
)

# Anonymous preview constants
_PREVIEW_PAGE = 1
_PREVIEW_PER_PAGE = 6


def _compute_age(dob: date) -> int:
    today = date.today()
    return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))


def _serialize_partial(profile: Profile, request: Request) -> dict[str, Any]:
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
        "weight_kg": profile.weight_kg,
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
        # New fields safe for partial view
        "marital_status": profile.marital_status.value,
        "family_type": profile.family_type.value if profile.family_type else None,
        "smokes": profile.smokes.value if profile.smokes else None,
        "drinks": profile.drinks.value if profile.drinks else None,
    }


def _serialize_preview(profile: Profile, request: Request) -> dict[str, Any]:
    """Even more limited serialization for anonymous preview results."""
    primary = next((p for p in profile.photos if p.is_primary), None)
    if primary is None and profile.photos:
        primary = profile.photos[0]
    base = str(request.base_url).rstrip("/")
    return {
        "id": str(profile.id),
        "gender": profile.gender.value,
        "age": _compute_age(profile.dob),
        "height_cm": profile.height_cm,
        "weight_kg": profile.weight_kg,
        "city": profile.city,
        "state": profile.state,
        "gotra": profile.gotra,
        "nakshatram": profile.nakshatram,
        "blurred_url": f"{base}/media/{primary.blurred_path}" if primary else None,
    }


def _build_base_query(
    gender: Optional[str],
    age_min: Optional[int],
    age_max: Optional[int],
    height_min: Optional[int],
    height_max: Optional[int],
    weight_min: Optional[int],
    weight_max: Optional[int],
    gotra: Optional[str],
    nakshatram: Optional[str],
    rashi: Optional[str],
    city: Optional[str],
    state_filter: Optional[str],
    manglik: Optional[str],
    diet: Optional[str],
    marital_status: Optional[str],
    family_type: Optional[str],
    smokes: Optional[str],
    drinks: Optional[str],
    mother_tongue: Optional[str],
    pin_code: Optional[str],
) -> Any:
    """Build a filtered SQLAlchemy query for approved profiles (no order/limit)."""
    query = (
        select(Profile)
        .where(Profile.status == ProfileStatusEnum.approved)
        .options(selectinload(Profile.photos))
    )

    if gender:
        try:
            g = GenderEnum(gender)
            query = query.where(Profile.gender == g)
        except ValueError:
            pass

    if age_min is not None:
        max_dob = date.today().replace(year=date.today().year - age_min)
        query = query.where(Profile.dob <= max_dob)

    if age_max is not None:
        min_dob = date.today().replace(year=date.today().year - age_max - 1)
        query = query.where(Profile.dob >= min_dob)

    if height_min is not None:
        query = query.where(Profile.height_cm >= height_min)

    if height_max is not None:
        query = query.where(Profile.height_cm <= height_max)

    if weight_min is not None:
        query = query.where(Profile.weight_kg >= weight_min)
    if weight_max is not None:
        query = query.where(Profile.weight_kg <= weight_max)

    if gotra:
        query = query.where(Profile.gotra.ilike(f"%{gotra}%"))

    if nakshatram:
        query = query.where(Profile.nakshatram.ilike(f"%{nakshatram}%"))

    if rashi:
        query = query.where(Profile.rashi.ilike(f"%{rashi}%"))

    if city:
        query = query.where(Profile.city.ilike(f"%{city}%"))

    if state_filter:
        query = query.where(Profile.state.ilike(f"%{state_filter}%"))

    if manglik:
        try:
            m = ManglikEnum(manglik)
            query = query.where(Profile.manglik == m)
        except ValueError:
            pass

    if diet:
        try:
            d = DietEnum(diet)
            query = query.where(Profile.diet == d)
        except ValueError:
            pass

    if marital_status:
        try:
            ms = MaritalStatusEnum(marital_status)
            query = query.where(Profile.marital_status == ms)
        except ValueError:
            pass

    if family_type:
        try:
            ft = FamilyTypeEnum(family_type)
            query = query.where(Profile.family_type == ft)
        except ValueError:
            pass

    if smokes:
        try:
            s = TobaccoAlcoholEnum(smokes)
            query = query.where(Profile.smokes == s)
        except ValueError:
            pass

    if drinks:
        try:
            d_val = TobaccoAlcoholEnum(drinks)
            query = query.where(Profile.drinks == d_val)
        except ValueError:
            pass

    if mother_tongue:
        query = query.where(Profile.mother_tongue.ilike(f"%{mother_tongue}%"))

    if pin_code:
        query = query.where(Profile.pin_code.ilike(f"{pin_code}%"))

    return query


class SearchController(Controller):
    path = "/search"

    @get("")
    async def search(
        self,
        request: Request,
        db: AsyncSession,
        gender: Optional[str] = None,
        age_min: Optional[int] = None,
        age_max: Optional[int] = None,
        height_min: Optional[int] = None,
        height_max: Optional[int] = None,
        weight_min: Optional[int] = None,
        weight_max: Optional[int] = None,
        gotra: Optional[str] = None,
        nakshatram: Optional[str] = None,
        rashi: Optional[str] = None,
        city: Optional[str] = None,
        state_filter: Annotated[Optional[str], Parameter(query="state")] = None,
        manglik: Optional[str] = None,
        diet: Optional[str] = None,
        # New filters
        marital_status: Optional[str] = None,
        family_type: Optional[str] = None,
        smokes: Optional[str] = None,
        drinks: Optional[str] = None,
        mother_tongue: Optional[str] = None,
        pin_code: Optional[str] = None,
        # Keyword/interests filter (comma-separated)
        interests: Optional[str] = None,
        page: int = 1,
        per_page: int = 20,
    ) -> dict[str, Any]:
        # Detect anonymous caller — JWT cookie absent or invalid means no payload.
        user_payload = request.scope.get("user_payload")
        is_anonymous = not user_payload

        query = _build_base_query(
            gender=gender,
            age_min=age_min,
            age_max=age_max,
            height_min=height_min,
            height_max=height_max,
            weight_min=weight_min,
            weight_max=weight_max,
            gotra=gotra,
            nakshatram=nakshatram,
            rashi=rashi,
            city=city,
            state_filter=state_filter,
            manglik=manglik,
            diet=diet,
            marital_status=marital_status,
            family_type=family_type,
            smokes=smokes,
            drinks=drinks,
            mother_tongue=mother_tongue,
            pin_code=pin_code,
        )

        # Count matching approved profiles (filter-respecting, before pagination)
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar_one()

        # ── Anonymous preview path ────────────────────────────────────────────
        if is_anonymous:
            preview_query = (
                query
                .order_by(func.random())
                .limit(_PREVIEW_PER_PAGE)
            )
            result = await db.execute(preview_query)
            profiles = list(result.scalars().all())

            return {
                "results": [_serialize_preview(p, request) for p in profiles],
                "total": total,
                "page": _PREVIEW_PAGE,
                "per_page": _PREVIEW_PER_PAGE,
                "requires_registration": True,
            }

        # ── Logged-in path (existing behaviour) ──────────────────────────────
        # Parse requested keywords
        requested_keywords: set[str] = set()
        if interests:
            requested_keywords = {kw.strip().lower() for kw in interests.split(",") if kw.strip()}

        per_page = min(max(1, per_page), 100)
        page = max(1, page)
        offset = (page - 1) * per_page

        if requested_keywords:
            # For keyword-scored search: fetch all results (no DB-level pagination),
            # score and sort in Python, then slice.
            all_query = query.order_by(Profile.created_at.desc())
            result = await db.execute(all_query)
            all_profiles = result.scalars().all()

            # Score by keyword intersection
            def _score(p: Profile) -> int:
                kws: list[str] = p.partner_preference_keywords or []
                return len(set(kws) & requested_keywords)

            scored = [(p, _score(p)) for p in all_profiles]
            # Keep only profiles with at least 1 keyword match
            scored = [(p, s) for p, s in scored if s > 0]
            # Sort by score desc, then created_at desc
            scored.sort(key=lambda x: (-x[1], x[0].created_at), reverse=False)

            total = len(scored)
            sliced = scored[offset: offset + per_page]
            profiles = [p for p, _ in sliced]
        else:
            query = query.order_by(Profile.created_at.desc()).offset(offset).limit(per_page)
            result = await db.execute(query)
            profiles = list(result.scalars().all())

        return {
            "results": [_serialize_partial(p, request) for p in profiles],
            "total": total,
            "page": page,
            "per_page": per_page,
        }
