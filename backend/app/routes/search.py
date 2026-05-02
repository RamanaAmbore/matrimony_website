"""Search routes."""
from datetime import date
from typing import Annotated, Any, Optional

from litestar import Controller, get
from litestar.connection import Request
from litestar.params import Parameter
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.profile import DietEnum, GenderEnum, ManglikEnum, Profile, ProfileStatusEnum


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
        gotra: Optional[str] = None,
        nakshatram: Optional[str] = None,
        rashi: Optional[str] = None,
        city: Optional[str] = None,
        state_filter: Annotated[Optional[str], Parameter(query="state")] = None,
        manglik: Optional[str] = None,
        diet: Optional[str] = None,
        page: int = 1,
        per_page: int = 20,
    ) -> dict[str, Any]:
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

        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar_one()

        per_page = min(max(1, per_page), 100)
        page = max(1, page)
        offset = (page - 1) * per_page

        query = query.order_by(Profile.created_at.desc()).offset(offset).limit(per_page)
        result = await db.execute(query)
        profiles = result.scalars().all()

        return {
            "results": [_serialize_partial(p, request) for p in profiles],
            "total": total,
            "page": page,
            "per_page": per_page,
        }
