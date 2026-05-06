"""Admin routes."""

import asyncio
import logging
import uuid
from datetime import date, datetime, timezone
from typing import Any, Optional

import msgspec
from litestar import Controller, get, post, put
from litestar.connection import Request
from litestar.exceptions import HTTPException
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import MEDIA_ROOT
from app.models.photo import Photo
from app.models.profile import Profile, ProfileStatusEnum
from app.models.request import DetailRequest, RequestStatusEnum
from app.models.user import User
from app.schemas.admin import (
    AdminApproveProfile,
    AdminApproveRequest,
    AdminRejectProfile,
    AdminRejectRequest,
)
from app.services import auth as auth_svc
from app.services import email as email_svc
from app.services.settings import settings_service, SENSITIVE_KEYS

logger = logging.getLogger(__name__)


class BroadcastEmailBody(msgspec.Struct):
    subject: str
    body_html: str
    filter_verified_only: bool = True
    filter_approved_only: bool = False
    filter_admin_only: bool = False
    filter_unapproved_only: bool = False
    filter_unverified_only: bool = False
    # Profile-derived filters: scope the audience to users who own at least
    # one profile matching ALL the supplied profile-side criteria. Empty/None
    # = no profile-side restriction.
    filter_mother_tongue: str | None = None
    filter_state: str | None = None
    filter_country: str | None = None


def _require_admin(request: Request) -> dict[str, Any]:
    """Admin-or-super gate. Super implies admin even if the flag has drifted."""
    payload = request.scope.get("user_payload")
    if not payload:
        raise HTTPException(status_code=401, detail={"code": "unauthenticated", "message": "Authentication required"})
    if not (payload.get("is_admin") or payload.get("is_super")):
        raise HTTPException(status_code=403, detail={"code": "forbidden", "message": "Admin access required"})
    return payload


def _require_super(request: Request) -> dict[str, Any]:
    payload = request.scope.get("user_payload")
    if not payload:
        raise HTTPException(status_code=401, detail={"code": "unauthenticated", "message": "Authentication required"})
    if not payload.get("is_super"):
        raise HTTPException(status_code=403, detail={"code": "forbidden", "message": "Super-user access required"})
    return payload


def _serialize_user(u: User) -> dict[str, Any]:
    return {
        "uuid": str(u.id),
        "email": u.email,
        "full_name": u.full_name,
        "user_id": u.user_handle,
        "phone_number": u.phone_number,
        "is_admin": u.is_admin,
        "is_super": u.is_super,
        "email_verified": u.email_verified,
        "is_approved": u.is_approved,
        "is_revoked": u.is_revoked,
        "created_at": u.created_at.isoformat(),
    }


def _serialize_profile(profile: Profile, request: Request) -> dict[str, Any]:
    base = str(request.base_url).rstrip("/")
    photos = []
    photos_bytes = 0
    for photo in profile.photos:
        photos_bytes += photo.byte_size or 0
        photos.append({
            "id": str(photo.id),
            "passport_url": f"{base}/media/{photo.passport_path}",
            "blurred_url": f"{base}/media/{photo.blurred_path}",
            "thumb_url": f"{base}/media/{photo.thumb_path}",
            "is_primary": photo.is_primary,
            "byte_size": photo.byte_size or 0,
        })

    def age(dob: date) -> int:
        today = date.today()
        return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))

    return {
        "id": str(profile.id),
        "profile_number": profile.profile_number,
        "owner_user_id": str(profile.owner_user_id),
        "photos_count": len(photos),
        "photos_bytes": photos_bytes,
        "gender": profile.gender.value,
        "first_name": profile.first_name,
        "last_name": profile.last_name,
        "dob": profile.dob.isoformat(),
        "age": age(profile.dob),
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
        "status": profile.status.value,
        "admin_notes": profile.admin_notes,
        "created_at": profile.created_at.isoformat(),
        "updated_at": profile.updated_at.isoformat(),
        "photos": photos,
    }


def _serialize_request(req: DetailRequest) -> dict[str, Any]:
    requester = getattr(req, "requester", None)
    profile = getattr(req, "profile", None)
    return {
        "id": str(req.id),
        "request_number": req.request_number,
        "requester_user_id": str(req.requester_user_id),
        "profile_id": str(req.profile_id),
        "status": req.status.value,
        "message": req.message,
        "admin_notes": req.admin_notes,
        "responded_at": req.responded_at.isoformat() if req.responded_at else None,
        "created_at": req.created_at.isoformat(),
        "requester_email": requester.email if requester else None,
        "requester_name": requester.full_name if requester else None,
        "profile_number": profile.profile_number if profile else None,
        "profile_first_name": profile.first_name if profile else None,
        "profile_last_name": profile.last_name if profile else None,
        "profile_gender": profile.gender.value if profile else None,
        "profile_city": profile.city if profile else None,
    }


class AdminController(Controller):
    path = "/admin"

    # --- Dashboard ---
    @get("/dashboard")
    async def dashboard(
        self,
        request: Request,
        db: AsyncSession,
    ) -> dict[str, Any]:
        """Single-call admin home: stats + pending items for inline review."""
        _require_admin(request)

        # ── Stats ────────────────────────────────────────────────────────────
        # Exclude super-users from every users-derived count.
        users_count = (
            await db.execute(
                select(func.count()).select_from(User).where(User.is_super == False)  # noqa: E712
            )
        ).scalar_one()
        users_admins = (
            await db.execute(
                select(func.count()).select_from(User).where(
                    User.is_admin == True, User.is_super == False  # noqa: E712
                )
            )
        ).scalar_one()
        users_super = (
            await db.execute(
                select(func.count()).select_from(User).where(User.is_super == True)  # noqa: E712
            )
        ).scalar_one()
        profiles_total = (await db.execute(select(func.count()).select_from(Profile))).scalar_one()
        profiles_pending = (
            await db.execute(
                select(func.count()).select_from(Profile).where(Profile.status == ProfileStatusEnum.pending)
            )
        ).scalar_one()
        profiles_approved = (
            await db.execute(
                select(func.count()).select_from(Profile).where(Profile.status == ProfileStatusEnum.approved)
            )
        ).scalar_one()
        profiles_rejected = (
            await db.execute(
                select(func.count()).select_from(Profile).where(Profile.status == ProfileStatusEnum.revoked)
            )
        ).scalar_one()
        profiles_draft = (
            await db.execute(
                select(func.count()).select_from(Profile).where(Profile.status == ProfileStatusEnum.draft)
            )
        ).scalar_one()
        requests_pending = (
            await db.execute(
                select(func.count()).select_from(DetailRequest).where(DetailRequest.status == RequestStatusEnum.pending)
            )
        ).scalar_one()
        requests_approved = (
            await db.execute(
                select(func.count()).select_from(DetailRequest).where(DetailRequest.status == RequestStatusEnum.approved)
            )
        ).scalar_one()
        requests_rejected = (
            await db.execute(
                select(func.count()).select_from(DetailRequest).where(DetailRequest.status == RequestStatusEnum.revoked)
            )
        ).scalar_one()
        requests_total = (
            await db.execute(
                select(func.count()).select_from(DetailRequest)
            )
        ).scalar_one()

        # Total disk usage of all stored photos (passport variant only —
        # blurred + thumb are derived and roughly proportional). Useful for
        # ops to keep an eye on MEDIA_ROOT growth.
        photos_total_bytes = (
            await db.execute(select(func.coalesce(func.sum(Photo.byte_size), 0)))
        ).scalar_one() or 0
        photos_count = (await db.execute(select(func.count()).select_from(Photo))).scalar_one()

        stats = {
            "users": users_count,
            "users_admins": users_admins,
            "users_super": users_super,
            "profiles_total": profiles_total,
            "profiles_pending": profiles_pending,
            "profiles_approved": profiles_approved,
            "profiles_rejected": profiles_rejected,
            "profiles_draft": profiles_draft,
            "requests_pending": requests_pending,
            "requests_approved": requests_approved,
            "requests_rejected": requests_rejected,
            "requests_total": requests_total,
            "photos_count": photos_count,
            "photos_total_bytes": int(photos_total_bytes),
        }

        # ── Pending profiles (up to 25) with owner email ────────────────────
        pending_profiles_result = await db.execute(
            select(Profile)
            .where(Profile.status == ProfileStatusEnum.pending)
            .options(selectinload(Profile.owner))
            .order_by(Profile.created_at.asc())
            .limit(25)
        )
        pending_profiles_rows = pending_profiles_result.scalars().all()

        def _age(dob: date) -> int:
            today = date.today()
            return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))

        pending_profiles = [
            {
                "id": str(p.id),
                "owner_email": p.owner.email if p.owner else None,
                "gender": p.gender.value,
                "first_name": p.first_name,
                "last_name": p.last_name,
                "age": _age(p.dob),
                "city": p.city,
                "state": p.state,
                "gotra": p.gotra,
                "nakshatram": p.nakshatram,
                "created_at": p.created_at.isoformat(),
            }
            for p in pending_profiles_rows
        ]

        # ── Pending users (unverified, up to 25) ────────────────────────────
        pending_users_result = await db.execute(
            select(User)
            .where(User.email_verified == False)  # noqa: E712
            .order_by(User.created_at.desc())
            .limit(25)
        )
        pending_users = [
            {
                "id": str(u.id),
                "email": u.email,
                "email_verified": u.email_verified,
                "created_at": u.created_at.isoformat(),
            }
            for u in pending_users_result.scalars().all()
        ]

        # ── Pending requests (up to 25) with requester email + profile name ─
        pending_requests_result = await db.execute(
            select(DetailRequest)
            .where(DetailRequest.status == RequestStatusEnum.pending)
            .options(
                selectinload(DetailRequest.requester),
                selectinload(DetailRequest.profile),
            )
            .order_by(DetailRequest.created_at.asc())
            .limit(25)
        )
        pending_requests = [
            {
                "id": str(r.id),
                "requester_email": r.requester.email if r.requester else None,
                "profile_id": str(r.profile_id),
                "profile_first_name": r.profile.first_name if r.profile else None,
                "profile_last_name": r.profile.last_name if r.profile else None,
                "message": r.message,
                "created_at": r.created_at.isoformat(),
            }
            for r in pending_requests_result.scalars().all()
        ]

        return {
            "stats": stats,
            "pending_profiles": pending_profiles,
            "pending_users": pending_users,
            "pending_requests": pending_requests,
        }

    # --- Profiles ---
    @get("/profiles")
    async def list_profiles(
        self,
        request: Request,
        db: AsyncSession,
        status: Optional[str] = None,
    ) -> list[dict[str, Any]]:
        _require_admin(request)
        query = select(Profile).options(selectinload(Profile.photos))
        if status:
            try:
                st = ProfileStatusEnum(status)
                query = query.where(Profile.status == st)
            except ValueError:
                pass
        query = query.order_by(Profile.created_at.desc())
        result = await db.execute(query)
        profiles = result.scalars().all()
        return [_serialize_profile(p, request) for p in profiles]

    @post("/profiles/{profile_id:str}/approve")
    async def approve_profile(
        self,
        profile_id: str,
        data: AdminApproveProfile,
        request: Request,
        db: AsyncSession,
    ) -> dict[str, Any]:
        _require_admin(request)

        try:
            pid = uuid.UUID(profile_id)
        except ValueError:
            raise HTTPException(status_code=404, detail={"code": "not_found", "message": "Profile not found"})

        result = await db.execute(
            select(Profile)
            .where(Profile.id == pid)
            .options(selectinload(Profile.photos), selectinload(Profile.owner))
        )
        profile = result.scalar_one_or_none()
        if not profile:
            raise HTTPException(status_code=404, detail={"code": "not_found", "message": "Profile not found"})

        # H3: refuse to approve a profile whose owner is currently revoked.
        # Search would hide it anyway, but admin work and the approval email
        # would be wasted on an account that can't log in.
        if profile.owner and profile.owner.is_revoked:
            raise HTTPException(
                status_code=409,
                detail={
                    "code": "owner_revoked",
                    "message": "Owner account is revoked — reinstate the user before approving the profile",
                },
            )

        profile.status = ProfileStatusEnum.approved
        profile.admin_notes = data.admin_notes
        await db.commit()
        await db.refresh(profile)

        # Send approval email to owner
        try:
            owner_result = await db.execute(select(User).where(User.id == profile.owner_user_id))
            owner = owner_result.scalar_one_or_none()
            if owner:
                await email_svc.send_profile_approved(
                    owner.email,
                    profile.first_name,
                    data.admin_notes,
                    profile_id=str(profile.id)[:5],
                )
        except Exception as exc:
            import logging
            logging.getLogger(__name__).warning("Failed to send approval email: %s", exc)

        from app.services.telegram import notify_profile_approved
        asyncio.create_task(notify_profile_approved(
            name=f"{profile.first_name} {profile.last_name or ''}".strip(),
            admin_notes=data.admin_notes or "",
        ))

        await db.refresh(profile)
        return _serialize_profile(profile, request)

    @post("/profiles/{profile_id:str}/reject")
    async def reject_profile(
        self,
        profile_id: str,
        data: AdminRejectProfile,
        request: Request,
        db: AsyncSession,
    ) -> dict[str, Any]:
        _require_admin(request)

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

        profile.status = ProfileStatusEnum.revoked
        profile.admin_notes = data.admin_notes
        # G6: stamp the time of rejection. submit_profile uses this to refuse
        # re-submission unless the owner has actually edited (updated_at >
        # rejected_at).
        profile.rejected_at = datetime.now(timezone.utc)
        # G2: cascade-revoke any pending requests targeting this profile.
        # Capture the affected requests first so H6 can email each requester.
        cascaded = await db.execute(
            select(DetailRequest)
            .where(
                DetailRequest.profile_id == pid,
                DetailRequest.status == RequestStatusEnum.pending,
            )
            .options(selectinload(DetailRequest.requester))
        )
        cascaded_requests = list(cascaded.scalars())
        for cascaded_req in cascaded_requests:
            cascaded_req.status = RequestStatusEnum.revoked
            cascaded_req.responded_at = datetime.now(timezone.utc)
        await db.commit()

        # H6: notify requesters whose pending requests were just cascade-revoked
        # so they aren't left waiting on a profile that's now offline.
        for cascaded_req in cascaded_requests:
            if cascaded_req.requester:
                try:
                    asyncio.create_task(email_svc.send_detail_request_rejected(
                        cascaded_req.requester.email,
                        profile.first_name,
                        "The profile is no longer available.",
                    ))
                except Exception as exc:
                    logger.warning("Failed to schedule cascade-reject email: %s", exc)

        try:
            owner_result = await db.execute(select(User).where(User.id == profile.owner_user_id))
            owner = owner_result.scalar_one_or_none()
            if owner:
                await email_svc.send_profile_rejected(owner.email, profile.first_name, data.admin_notes)
        except Exception as exc:
            import logging
            logging.getLogger(__name__).warning("Failed to send rejection email: %s", exc)

        from app.services.telegram import notify_profile_rejected
        asyncio.create_task(notify_profile_rejected(
            name=f"{profile.first_name} {profile.last_name or ''}".strip(),
            admin_notes=data.admin_notes or "",
        ))

        await db.refresh(profile)
        return _serialize_profile(profile, request)

    @post("/profiles/{profile_id:str}/reinstate")
    async def reinstate_profile(
        self,
        profile_id: str,
        request: Request,
        db: AsyncSession,
    ) -> dict[str, Any]:
        """Reinstate a revoked profile by setting its status back to approved.

        Returns 409 if the profile is not currently revoked.
        """
        _require_admin(request)

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

        if profile.status != ProfileStatusEnum.revoked:
            raise HTTPException(
                status_code=409,
                detail={"code": "not_revoked", "message": f"Profile is '{profile.status.value}', not revoked — cannot reinstate"},
            )

        profile.status = ProfileStatusEnum.approved
        await db.commit()
        await db.refresh(profile)
        return _serialize_profile(profile, request)

    @post("/profiles/{profile_id:str}/delete", status_code=200)
    async def delete_profile(
        self,
        profile_id: str,
        request: Request,
        db: AsyncSession,
    ) -> dict[str, Any]:
        """Hard-delete a profile (cascades photos and detail requests).

        Canonical flow: revoke first, then delete. Super-users may bypass the
        revoke-first guard and delete directly.
        """
        payload = _require_admin(request)

        try:
            pid = uuid.UUID(profile_id)
        except ValueError:
            raise HTTPException(status_code=404, detail={"code": "not_found", "message": "Profile not found"})

        result = await db.execute(select(Profile).where(Profile.id == pid))
        profile = result.scalar_one_or_none()
        if not profile:
            raise HTTPException(status_code=404, detail={"code": "not_found", "message": "Profile not found"})

        if profile.status != ProfileStatusEnum.revoked and not payload.get("is_super"):
            raise HTTPException(
                status_code=409,
                detail={"code": "not_revoked", "message": "Revoke before deleting"},
            )

        # H2: unlink photo files on disk before cascade. Same gap that G3
        # closed for user-delete, still present here. Without this every
        # admin profile-delete leaks the JPEG variants under MEDIA_ROOT.
        photos_to_unlink = await db.execute(select(Photo).where(Photo.profile_id == pid))
        for photo in photos_to_unlink.scalars():
            for path_rel in (photo.passport_path, photo.blurred_path, photo.thumb_path):
                fpath = MEDIA_ROOT / path_rel
                if fpath.exists():
                    try:
                        fpath.unlink()
                    except OSError as exc:
                        logger.warning("Failed to unlink %s: %s", fpath, exc)
            photo_dir = MEDIA_ROOT / "profiles" / str(pid) / str(photo.id)
            if photo_dir.exists() and not any(photo_dir.iterdir()):
                try:
                    photo_dir.rmdir()
                except OSError:
                    pass
        profile_dir = MEDIA_ROOT / "profiles" / str(pid)
        if profile_dir.exists() and not any(profile_dir.iterdir()):
            try:
                profile_dir.rmdir()
            except OSError:
                pass

        deleted = {
            "id": str(profile.id),
            "profile_number": profile.profile_number,
            "first_name": profile.first_name,
            "last_name": profile.last_name,
        }
        await db.delete(profile)
        await db.commit()
        return {"deleted": deleted}

    # --- Requests ---
    @get("/requests")
    async def list_requests(
        self,
        request: Request,
        db: AsyncSession,
        status: Optional[str] = None,
    ) -> list[dict[str, Any]]:
        _require_admin(request)
        query = select(DetailRequest).options(
            selectinload(DetailRequest.requester),
            selectinload(DetailRequest.profile),
        )
        if status:
            try:
                st = RequestStatusEnum(status)
                query = query.where(DetailRequest.status == st)
            except ValueError:
                pass
        query = query.order_by(DetailRequest.created_at.desc())
        result = await db.execute(query)
        reqs = result.scalars().all()
        return [_serialize_request(r) for r in reqs]

    @post("/requests/{request_id:str}/approve")
    async def approve_request(
        self,
        request_id: str,
        data: AdminApproveRequest,
        request: Request,
        db: AsyncSession,
    ) -> dict[str, Any]:
        _require_admin(request)

        try:
            rid = uuid.UUID(request_id)
        except ValueError:
            raise HTTPException(status_code=404, detail={"code": "not_found", "message": "Request not found"})

        result = await db.execute(
            select(DetailRequest)
            .where(DetailRequest.id == rid)
            .options(
                selectinload(DetailRequest.requester),
                selectinload(DetailRequest.profile).selectinload(Profile.owner),
            )
        )
        req = result.scalar_one_or_none()
        if not req:
            raise HTTPException(status_code=404, detail={"code": "not_found", "message": "Request not found"})

        # H4: refuse to approve if the requester is revoked. G1 already
        # cascade-revokes pending requests at revoke time, but this guard
        # closes the race window where a revoke fires after admin started
        # approving but before the commit lands.
        if req.requester and req.requester.is_revoked:
            raise HTTPException(
                status_code=409,
                detail={
                    "code": "requester_revoked",
                    "message": "Requester account is revoked — cannot approve",
                },
            )
        # Defence-in-depth: also refuse if the target profile's owner has been
        # revoked since the request was placed.
        if req.profile and req.profile.owner and req.profile.owner.is_revoked:
            raise HTTPException(
                status_code=409,
                detail={
                    "code": "owner_revoked",
                    "message": "Profile owner is revoked — cannot approve request",
                },
            )

        req.status = RequestStatusEnum.approved
        req.admin_notes = data.admin_notes
        req.responded_at = datetime.now(timezone.utc)
        await db.commit()

        # Send full profile details to requester
        requester = None
        profile = None
        try:
            requester_result = await db.execute(select(User).where(User.id == req.requester_user_id))
            requester = requester_result.scalar_one_or_none()

            profile_result = await db.execute(
                select(Profile)
                .where(Profile.id == req.profile_id)
                .options(selectinload(Profile.photos))
            )
            profile = profile_result.scalar_one_or_none()

            if requester and profile:
                from app.config import MEDIA_ROOT
                photo_bytes_map: dict[str, bytes] = {}
                for photo in profile.photos:
                    passport_file = MEDIA_ROOT / photo.passport_path
                    if passport_file.exists():
                        photo_bytes_map[str(photo.id)] = passport_file.read_bytes()

                requester_name = requester.full_name if requester.full_name else "Member"
                await email_svc.send_detail_request_approved(
                    requester.email,
                    profile,
                    profile.photos,
                    photo_bytes_map,
                    requester_name=requester_name,
                )
        except Exception as exc:
            import logging
            logging.getLogger(__name__).warning("Failed to send approved request email: %s", exc)

        from app.services.telegram import notify_request_approved
        asyncio.create_task(notify_request_approved(
            requester=requester.email if requester else str(req.requester_user_id),
            profile_name=(
                f"{profile.first_name} {profile.last_name or ''}".strip()
                if profile else str(req.profile_id)
            ),
        ))

        await db.refresh(req)
        # Reload relationships for enriched serialization
        enriched = await db.execute(
            select(DetailRequest)
            .where(DetailRequest.id == req.id)
            .options(
                selectinload(DetailRequest.requester),
                selectinload(DetailRequest.profile),
            )
        )
        return _serialize_request(enriched.scalar_one())

    @post("/requests/{request_id:str}/reject")
    async def reject_request(
        self,
        request_id: str,
        data: AdminRejectRequest,
        request: Request,
        db: AsyncSession,
    ) -> dict[str, Any]:
        _require_admin(request)

        try:
            rid = uuid.UUID(request_id)
        except ValueError:
            raise HTTPException(status_code=404, detail={"code": "not_found", "message": "Request not found"})

        result = await db.execute(select(DetailRequest).where(DetailRequest.id == rid))
        req = result.scalar_one_or_none()
        if not req:
            raise HTTPException(status_code=404, detail={"code": "not_found", "message": "Request not found"})

        req.status = RequestStatusEnum.revoked
        req.admin_notes = data.admin_notes
        req.responded_at = datetime.now(timezone.utc)
        await db.commit()

        requester = None
        profile = None
        try:
            requester_result = await db.execute(select(User).where(User.id == req.requester_user_id))
            requester = requester_result.scalar_one_or_none()
            profile_result = await db.execute(select(Profile).where(Profile.id == req.profile_id))
            profile = profile_result.scalar_one_or_none()

            if requester:
                await email_svc.send_detail_request_rejected(
                    requester.email,
                    profile.first_name if profile else None,
                    data.admin_notes,
                )
        except Exception as exc:
            import logging
            logging.getLogger(__name__).warning("Failed to send rejected request notification: %s", exc)

        from app.services.telegram import notify_request_rejected
        asyncio.create_task(notify_request_rejected(
            requester=requester.email if requester else str(req.requester_user_id),
            profile_name=(
                f"{profile.first_name} {profile.last_name or ''}".strip()
                if profile else str(req.profile_id)
            ),
        ))

        await db.refresh(req)
        # Reload relationships for enriched serialization
        enriched = await db.execute(
            select(DetailRequest)
            .where(DetailRequest.id == req.id)
            .options(
                selectinload(DetailRequest.requester),
                selectinload(DetailRequest.profile),
            )
        )
        return _serialize_request(enriched.scalar_one())

    @post("/requests/{request_id:str}/reinstate")
    async def reinstate_request(
        self,
        request_id: str,
        request: Request,
        db: AsyncSession,
    ) -> dict[str, Any]:
        """Reinstate a revoked detail request by setting status back to approved.

        Returns 409 if the request is not currently revoked.
        """
        _require_admin(request)

        try:
            rid = uuid.UUID(request_id)
        except ValueError:
            raise HTTPException(status_code=404, detail={"code": "not_found", "message": "Request not found"})

        result = await db.execute(
            select(DetailRequest)
            .where(DetailRequest.id == rid)
            .options(
                selectinload(DetailRequest.requester),
                selectinload(DetailRequest.profile),
            )
        )
        req = result.scalar_one_or_none()
        if not req:
            raise HTTPException(status_code=404, detail={"code": "not_found", "message": "Request not found"})

        if req.status != RequestStatusEnum.revoked:
            raise HTTPException(
                status_code=409,
                detail={"code": "not_revoked", "message": f"Request is '{req.status.value}', not revoked — cannot reinstate"},
            )

        req.status = RequestStatusEnum.approved
        await db.commit()
        await db.refresh(req)
        enriched = await db.execute(
            select(DetailRequest)
            .where(DetailRequest.id == req.id)
            .options(
                selectinload(DetailRequest.requester),
                selectinload(DetailRequest.profile),
            )
        )
        return _serialize_request(enriched.scalar_one())

    @post("/requests/{request_id:str}/delete", status_code=200)
    async def delete_request(
        self,
        request_id: str,
        request: Request,
        db: AsyncSession,
    ) -> dict[str, Any]:
        """Hard-delete a detail request.

        Canonical flow: revoke first, then delete. Super-users may bypass the
        revoke-first guard and delete directly.
        """
        payload = _require_admin(request)

        try:
            rid = uuid.UUID(request_id)
        except ValueError:
            raise HTTPException(status_code=404, detail={"code": "not_found", "message": "Request not found"})

        result = await db.execute(select(DetailRequest).where(DetailRequest.id == rid))
        req = result.scalar_one_or_none()
        if not req:
            raise HTTPException(status_code=404, detail={"code": "not_found", "message": "Request not found"})

        if req.status != RequestStatusEnum.revoked and not payload.get("is_super"):
            raise HTTPException(
                status_code=409,
                detail={"code": "not_revoked", "message": "Revoke before deleting"},
            )

        deleted = {
            "id": str(req.id),
            "request_number": req.request_number,
            "status": req.status.value,
        }
        await db.delete(req)
        await db.commit()
        return {"deleted": deleted}

    # --- Users ---
    @get("/users")
    async def list_users(
        self,
        request: Request,
        db: AsyncSession,
    ) -> list[dict[str, Any]]:
        _require_admin(request)
        # Hide super-users from the admin list — super is a privileged
        # invisible role that even other admins should not see or act on.
        result = await db.execute(
            select(User).where(User.is_super == False).order_by(User.created_at.desc())  # noqa: E712
        )
        users = result.scalars().all()
        return [_serialize_user(u) for u in users]

    @post("/users/{user_id:str}/promote")
    async def promote_user(
        self,
        user_id: str,
        request: Request,
        db: AsyncSession,
    ) -> dict[str, Any]:
        """Promote a regular user to admin. Super-only — a plain admin cannot
        create more admins.

        Guards:
          - target must not already be admin or super
          - target must not be revoked (revoked users are banned)
          - target must have verified email AND be approved (no half-baked admins)
        """
        _require_super(request)

        try:
            uid = uuid.UUID(user_id)
        except ValueError:
            raise HTTPException(status_code=404, detail={"code": "not_found", "message": "User not found"})

        result = await db.execute(select(User).where(User.id == uid))
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=404, detail={"code": "not_found", "message": "User not found"})
        if user.is_super:
            raise HTTPException(status_code=409, detail={"code": "already_super", "message": "User is already a super-user"})
        if user.is_admin:
            raise HTTPException(status_code=409, detail={"code": "already_admin", "message": "User is already an admin"})
        if user.is_revoked:
            raise HTTPException(status_code=409, detail={"code": "user_revoked", "message": "Reinstate the user before promoting"})
        if not user.email_verified:
            raise HTTPException(status_code=409, detail={"code": "email_not_verified", "message": "User email must be verified before promotion"})
        if not user.is_approved:
            raise HTTPException(status_code=409, detail={"code": "not_approved", "message": "User must be approved before promotion"})

        user.is_admin = True
        await db.commit()
        await db.refresh(user)

        # G7: notify the new admin + telegram ops alert
        try:
            asyncio.create_task(email_svc.send_admin_promoted(user.email, user.full_name))
            from app.services.telegram import notify_user_promoted
            asyncio.create_task(notify_user_promoted(name=user.full_name, email=user.email))
        except Exception as exc:
            logger.warning("Failed to schedule promote notifications: %s", exc)

        return _serialize_user(user)

    @post("/users/{user_id:str}/resend_verification")
    async def resend_verification(
        self,
        user_id: str,
        request: Request,
        db: AsyncSession,
    ) -> dict[str, Any]:
        """G8: regenerate the email verification token and re-send the
        verification email. Useful when a user's original token has expired
        or they never got the email — preferable to admin-overriding
        verify_email since this preserves the actual verification step.

        Permission rules mirror verify_user_email:
          - cannot target super (super is always verified)
          - admin-target requires super
          - cannot target an already-verified user (409)
        """
        payload = _require_admin(request)

        try:
            uid = uuid.UUID(user_id)
        except ValueError:
            raise HTTPException(status_code=404, detail={"code": "not_found", "message": "User not found"})

        result = await db.execute(select(User).where(User.id == uid))
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=404, detail={"code": "not_found", "message": "User not found"})
        if user.is_super:
            raise HTTPException(status_code=403, detail={"code": "forbidden", "message": "Cannot modify a super-user"})
        if user.is_admin and not payload.get("is_super"):
            raise HTTPException(
                status_code=403,
                detail={"code": "forbidden", "message": "Only super-user can act on an admin account"},
            )
        if user.email_verified:
            raise HTTPException(
                status_code=409,
                detail={"code": "already_verified", "message": "User email is already verified"},
            )

        token = auth_svc.generate_token()
        user.email_verification_token = token
        await db.commit()
        await db.refresh(user)

        try:
            await email_svc.send_verification_email(user.email, token, full_name=user.full_name)
        except Exception as exc:
            logger.warning("Failed to send verification email: %s", exc)

        return _serialize_user(user)

    @post("/users/{user_id:str}/verify_email")
    async def verify_user_email(
        self,
        user_id: str,
        request: Request,
        db: AsyncSession,
    ) -> dict[str, Any]:
        """Admin override: mark a user's email as verified.

        Permission rules:
          - cannot target super-user (super is always verified)
          - admin-target → super-only (mirrors revoke/reinstate/delete on admins)
        """
        payload = _require_admin(request)

        try:
            uid = uuid.UUID(user_id)
        except ValueError:
            raise HTTPException(status_code=404, detail={"code": "not_found", "message": "User not found"})

        result = await db.execute(select(User).where(User.id == uid))
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=404, detail={"code": "not_found", "message": "User not found"})
        if user.is_super:
            raise HTTPException(status_code=403, detail={"code": "forbidden", "message": "Cannot modify a super-user"})
        if user.is_admin and not payload.get("is_super"):
            raise HTTPException(
                status_code=403,
                detail={"code": "forbidden", "message": "Only super-user can act on an admin account"},
            )

        user.email_verified = True
        user.email_verification_token = None
        await db.commit()
        await db.refresh(user)
        return _serialize_user(user)

    @post("/users/{user_id:str}/approve")
    async def approve_user(
        self,
        user_id: str,
        request: Request,
        db: AsyncSession,
    ) -> dict[str, Any]:
        """Admin: mark a user as approved so they can create profiles.

        Guards:
          - cannot target super (super is always approved by bootstrap)
          - admin-target → super-only (mirrors revoke/reinstate/delete on admins)
          - cannot approve a revoked user (must reinstate first)
          - cannot approve before email is verified
        """
        payload = _require_admin(request)

        try:
            uid = uuid.UUID(user_id)
        except ValueError:
            raise HTTPException(status_code=404, detail={"code": "not_found", "message": "User not found"})

        result = await db.execute(select(User).where(User.id == uid))
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=404, detail={"code": "not_found", "message": "User not found"})
        if user.is_super:
            raise HTTPException(status_code=403, detail={"code": "forbidden", "message": "Cannot approve a super-user"})
        if user.is_admin and not payload.get("is_super"):
            raise HTTPException(
                status_code=403,
                detail={"code": "forbidden", "message": "Only super-user can act on an admin account"},
            )
        if user.is_revoked:
            raise HTTPException(
                status_code=409,
                detail={"code": "user_revoked", "message": "User is revoked — reinstate them instead of approving"},
            )
        if not user.email_verified:
            raise HTTPException(
                status_code=409,
                detail={"code": "email_not_verified", "message": "User email must be verified before approval"},
            )

        user.is_approved = True
        await db.commit()
        await db.refresh(user)

        from app.services.telegram import notify_user_approved
        asyncio.create_task(notify_user_approved(name=user.full_name, email=user.email))

        asyncio.create_task(email_svc.send_account_approved(user.email, user.full_name))

        return _serialize_user(user)

    @post("/users/{user_id:str}/unapprove")
    async def unapprove_user(
        self,
        user_id: str,
        request: Request,
        db: AsyncSession,
    ) -> dict[str, Any]:
        """Pull live access from a user by clearing is_approved (does NOT set is_revoked).

        This is a lighter action than revoke: the user can still log in but
        cannot create profiles. Use /admin/users/{id}/revoke for a stronger
        action that also blocks login entirely.

        Permission rules:
          - admin → can unapprove only non-admin users
          - super → can unapprove any user (incl. other admins)
          - never targets a super-user
        """
        payload = _require_admin(request)

        try:
            uid = uuid.UUID(user_id)
        except ValueError:
            raise HTTPException(status_code=404, detail={"code": "not_found", "message": "User not found"})

        result = await db.execute(select(User).where(User.id == uid))
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=404, detail={"code": "not_found", "message": "User not found"})
        if user.is_super:
            raise HTTPException(status_code=403, detail={"code": "forbidden", "message": "Cannot unapprove a super-user"})
        if user.is_admin and not payload.get("is_super"):
            raise HTTPException(
                status_code=403,
                detail={"code": "forbidden", "message": "Only super-user can revoke approval from an admin"},
            )

        user.is_approved = False
        await db.commit()
        await db.refresh(user)
        return _serialize_user(user)

    @post("/users/{user_id:str}/demote", status_code=200)
    async def demote_user(
        self,
        user_id: str,
        request: Request,
        db: AsyncSession,
    ) -> dict[str, Any]:
        """Strip admin from a user. Super-only; cannot target super."""
        _require_super(request)

        try:
            uid = uuid.UUID(user_id)
        except ValueError:
            raise HTTPException(status_code=404, detail={"code": "not_found", "message": "User not found"})

        result = await db.execute(select(User).where(User.id == uid))
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=404, detail={"code": "not_found", "message": "User not found"})
        if user.is_super:
            raise HTTPException(status_code=403, detail={"code": "forbidden", "message": "Cannot demote a super-user"})
        if not user.is_admin:
            raise HTTPException(status_code=409, detail={"code": "not_admin", "message": "User is not an admin"})

        user.is_admin = False
        await db.commit()
        await db.refresh(user)

        # G7: notify the demoted admin + telegram ops alert
        try:
            asyncio.create_task(email_svc.send_admin_demoted(user.email, user.full_name))
            from app.services.telegram import notify_user_demoted
            asyncio.create_task(notify_user_demoted(name=user.full_name, email=user.email))
        except Exception as exc:
            logger.warning("Failed to schedule demote notifications: %s", exc)

        return _serialize_user(user)

    @post("/users/{user_id:str}/revoke", status_code=200)
    async def revoke_user(
        self,
        user_id: str,
        request: Request,
        db: AsyncSession,
    ) -> dict[str, Any]:
        """Soft-revoke a user account: sets is_revoked=True and is_approved=False.

        Revoked users cannot log in. Use reinstate to undo.

        Permission rules:
          - super-users can never be revoked
          - revoking an admin requires the caller to be super
          - plain admins can revoke non-admin users
          - cannot revoke self
        """
        payload = _require_admin(request)
        caller_uid = uuid.UUID(payload["sub"])

        try:
            uid = uuid.UUID(user_id)
        except ValueError:
            raise HTTPException(status_code=404, detail={"code": "not_found", "message": "User not found"})
        if uid == caller_uid:
            raise HTTPException(status_code=400, detail={"code": "self_action", "message": "Cannot revoke your own account"})

        result = await db.execute(select(User).where(User.id == uid))
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=404, detail={"code": "not_found", "message": "User not found"})
        if user.is_super:
            raise HTTPException(status_code=403, detail={"code": "forbidden", "message": "Cannot revoke a super-user"})
        if user.is_admin and not payload.get("is_super"):
            raise HTTPException(
                status_code=403,
                detail={"code": "forbidden", "message": "Only super-user can revoke an admin account"},
            )

        user.is_revoked = True
        user.is_approved = False
        # G1: cascade-revoke any pending detail requests this user has
        # in flight. They were placed by an account that's now banned, so
        # leaving them in the admin queue would be a leak — admin could
        # otherwise still approve them and email a full profile to a banned
        # requester.
        await db.execute(
            update(DetailRequest)
            .where(
                DetailRequest.requester_user_id == uid,
                DetailRequest.status == RequestStatusEnum.pending,
            )
            .values(status=RequestStatusEnum.revoked, responded_at=datetime.now(timezone.utc))
        )
        await db.commit()
        await db.refresh(user)

        # G7: notify the user they've been revoked + telegram ops alert
        try:
            asyncio.create_task(email_svc.send_account_revoked(user.email, user.full_name))
            from app.services.telegram import notify_user_revoked
            asyncio.create_task(notify_user_revoked(name=user.full_name, email=user.email))
        except Exception as exc:
            logger.warning("Failed to schedule revoke notifications: %s", exc)
        return _serialize_user(user)

    @post("/users/{user_id:str}/reinstate", status_code=200)
    async def reinstate_user(
        self,
        user_id: str,
        request: Request,
        db: AsyncSession,
    ) -> dict[str, Any]:
        """Reinstate a revoked user: clears is_revoked.

        Approval is restored only if the email is already verified — preserves
        the verify-then-approve gate so a user revoked while unverified does
        not return as a fully-approved account.

        Permission rules mirror revoke:
          - super-users cannot be targeted (they are never revoked)
          - reinstating an admin requires caller to be super
          - plain admins can reinstate non-admin users
          - cannot reinstate self
          - target must currently be revoked (409 otherwise)
        """
        payload = _require_admin(request)
        caller_uid = uuid.UUID(payload["sub"])

        try:
            uid = uuid.UUID(user_id)
        except ValueError:
            raise HTTPException(status_code=404, detail={"code": "not_found", "message": "User not found"})
        if uid == caller_uid:
            raise HTTPException(status_code=400, detail={"code": "self_action", "message": "Cannot reinstate your own account"})

        result = await db.execute(select(User).where(User.id == uid))
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=404, detail={"code": "not_found", "message": "User not found"})
        if user.is_super:
            raise HTTPException(status_code=403, detail={"code": "forbidden", "message": "Cannot reinstate a super-user"})
        if user.is_admin and not payload.get("is_super"):
            raise HTTPException(
                status_code=403,
                detail={"code": "forbidden", "message": "Only super-user can reinstate an admin account"},
            )
        if not user.is_revoked:
            raise HTTPException(
                status_code=409,
                detail={"code": "not_revoked", "message": "User is not revoked"},
            )

        user.is_revoked = False
        # Only restore approval if the email is verified. Otherwise the user
        # must still go through verify → admin approve.
        if user.email_verified:
            user.is_approved = True
        await db.commit()
        await db.refresh(user)

        # G7: notify the user they can return + telegram ops alert
        try:
            asyncio.create_task(email_svc.send_account_reinstated(
                user.email, user.full_name, approved=user.is_approved,
            ))
            from app.services.telegram import notify_user_reinstated
            asyncio.create_task(notify_user_reinstated(name=user.full_name, email=user.email))
        except Exception as exc:
            logger.warning("Failed to schedule reinstate notifications: %s", exc)

        return _serialize_user(user)

    @post("/users/{user_id:str}/delete", status_code=200)
    async def delete_user(
        self,
        user_id: str,
        request: Request,
        db: AsyncSession,
    ) -> dict[str, Any]:
        """Delete a user (cascades profiles, photos, requests).

        Canonical flow: revoke first, then delete. Super-users may bypass the
        revoke-first guard and delete directly.

        Permission rules:
          - super         → can delete any non-super user (bypasses revoke-first)
          - admin         → can delete only NON-admin, already-revoked users
          - everyone else → forbidden
          - cannot delete self
          - never delete a super-user
        """
        payload = _require_admin(request)
        caller_uid = uuid.UUID(payload["sub"])

        try:
            uid = uuid.UUID(user_id)
        except ValueError:
            raise HTTPException(status_code=404, detail={"code": "not_found", "message": "User not found"})
        if uid == caller_uid:
            raise HTTPException(status_code=400, detail={"code": "self_delete", "message": "Cannot delete your own account"})

        result = await db.execute(select(User).where(User.id == uid))
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=404, detail={"code": "not_found", "message": "User not found"})
        if user.is_super:
            raise HTTPException(status_code=403, detail={"code": "forbidden", "message": "Cannot delete a super-user"})
        if user.is_admin and not payload.get("is_super"):
            raise HTTPException(
                status_code=403,
                detail={"code": "forbidden", "message": "Only super-user can delete admin accounts"},
            )
        if not user.is_revoked and not payload.get("is_super"):
            raise HTTPException(
                status_code=409,
                detail={"code": "not_revoked", "message": "Revoke before deleting"},
            )

        # G3: unlink photo files on disk before cascade-deleting the user.
        # The DB cascade removes Photo rows, but the JPEG variants under
        # MEDIA_ROOT are external state — the cascade can't touch them, so
        # without this every admin user-delete leaks files.
        photos_to_unlink = await db.execute(
            select(Photo)
            .join(Profile, Profile.id == Photo.profile_id)
            .where(Profile.owner_user_id == uid)
        )
        for photo in photos_to_unlink.scalars():
            for path_rel in (photo.passport_path, photo.blurred_path, photo.thumb_path):
                fpath = MEDIA_ROOT / path_rel
                if fpath.exists():
                    try:
                        fpath.unlink()
                    except OSError as exc:
                        logger.warning("Failed to unlink %s: %s", fpath, exc)
            photo_dir = MEDIA_ROOT / "profiles" / str(photo.profile_id) / str(photo.id)
            if photo_dir.exists() and not any(photo_dir.iterdir()):
                try:
                    photo_dir.rmdir()
                except OSError:
                    pass
        # Best-effort cleanup of profile-level dirs after the photo dirs are gone.
        owned_profiles = await db.execute(
            select(Profile.id).where(Profile.owner_user_id == uid)
        )
        for (pid,) in owned_profiles.all():
            profile_dir = MEDIA_ROOT / "profiles" / str(pid)
            if profile_dir.exists() and not any(profile_dir.iterdir()):
                try:
                    profile_dir.rmdir()
                except OSError:
                    pass

        deleted = {
            "uuid": str(user.id),
            "user_id": user.user_handle,
            "email": user.email,
            "is_admin": user.is_admin,
        }
        await db.delete(user)
        await db.commit()
        return {"deleted": deleted}

    # --- Settings ---
    @get("/settings")
    async def get_settings(
        self,
        request: Request,
        db: AsyncSession,
    ) -> dict[str, Any]:
        _require_admin(request)
        await settings_service.ensure_loaded(db)
        return settings_service.all_public()

    @put("/settings")
    async def update_settings(
        self,
        request: Request,
        db: AsyncSession,
    ) -> dict[str, Any]:
        payload = _require_admin(request)

        body = await request.json()
        if not isinstance(body, dict):
            raise HTTPException(status_code=422, detail={"code": "invalid_body", "message": "Body must be a JSON object"})

        # SECURITY: Sensitive values (smtp_password, matrimony_tg_token, ...)
        # are returned as the mask string '***' from GET /admin/settings.
        # If a save round-trips that mask back unchanged, do NOT overwrite the
        # real stored secret. The admin must explicitly type a new value to
        # change it. This prevents accidental credential corruption when the
        # admin saves settings without touching the masked fields.
        for k in list(body.keys()):
            if k in SENSITIVE_KEYS and body[k] in ("***", None):
                del body[k]

        # Validate email-shaped settings before persisting.
        # Accept either bare 'name@example.com' or RFC display-name form
        # 'Display Name <name@example.com>' (smtp_from typically uses the latter).
        import re as _re
        _EMAIL_RE = _re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
        _ANGLE_RE = _re.compile(r"<([^>]+)>")
        EMAIL_KEYS = {"owner_email", "smtp_from"}
        for k in EMAIL_KEYS:
            if k in body and body[k] not in (None, ""):
                value = str(body[k]).strip()
                m = _ANGLE_RE.search(value)
                addr = m.group(1).strip() if m else value
                if not _EMAIL_RE.match(addr):
                    raise HTTPException(
                        status_code=422,
                        detail={
                            "code": "invalid_email",
                            "message": (
                                f"{k}: enter a valid email address "
                                f"(e.g. name@example.com or 'Display Name <name@example.com>')"
                            ),
                        },
                    )

        updated_by = uuid.UUID(payload["sub"]) if payload else None
        await settings_service.set_many(body, db, updated_by)
        await db.commit()

        return settings_service.all_public()

    # --- Broadcast email ---
    @post("/broadcast-email")
    async def broadcast_email(
        self,
        data: BroadcastEmailBody,
        request: Request,
        db: AsyncSession,
    ) -> dict[str, Any]:
        """Send a custom broadcast email to all (or filtered) registered users."""
        _require_admin(request)

        # Always exclude super-users from broadcasts (privileged hidden role).
        query = select(User).where(User.is_super == False)  # noqa: E712
        if data.filter_verified_only:
            query = query.where(User.email_verified == True)  # noqa: E712
        if data.filter_unverified_only:
            query = query.where(User.email_verified == False)  # noqa: E712
        if data.filter_approved_only:
            query = query.where(User.is_approved == True)  # noqa: E712
        if data.filter_unapproved_only:
            query = query.where(User.is_approved == False)  # noqa: E712
        if data.filter_admin_only:
            query = query.where(User.is_admin == True)  # noqa: E712

        # Profile-derived filters — restrict to users whose profiles match.
        # Joining users → profiles where ALL provided profile criteria match.
        # Distinct on user.id so a user with multiple matching profiles is
        # only emailed once.
        profile_filters = [
            (data.filter_mother_tongue, Profile.mother_tongue),
            (data.filter_state, Profile.state),
            (data.filter_country, Profile.country),
        ]
        active_profile_filters = [(v, col) for v, col in profile_filters if v]
        if active_profile_filters:
            query = query.join(Profile, Profile.owner_user_id == User.id)
            for v, col in active_profile_filters:
                query = query.where(col == v)
            query = query.distinct()

        result = await db.execute(query)
        users = result.scalars().all()

        _BATCH_SIZE = 20
        sent = 0
        failed = 0

        for batch_start in range(0, len(users), _BATCH_SIZE):
            batch = users[batch_start : batch_start + _BATCH_SIZE]

            async def _send_one(user: User) -> bool:
                recipient_name = user.full_name or user.email
                try:
                    await email_svc.send_broadcast(
                        to=user.email,
                        subject=data.subject,
                        body_html=data.body_html,
                        recipient_name=recipient_name,
                    )
                    return True
                except Exception as exc:
                    logger.warning(
                        "Broadcast send failed for %s: %s", user.email, exc
                    )
                    return False

            results = await asyncio.gather(*[_send_one(u) for u in batch])
            sent += sum(1 for ok in results if ok)
            failed += sum(1 for ok in results if not ok)

        logger.info(
            "Broadcast: sent=%d failed=%d subject=%s",
            sent,
            failed,
            data.subject,
        )
        return {"sent": sent, "failed": failed}

    # --- Stats ---
    @get("/stats")
    async def stats(
        self,
        request: Request,
        db: AsyncSession,
    ) -> dict[str, Any]:
        _require_admin(request)

        users_count = (
            await db.execute(
                select(func.count()).select_from(User).where(User.is_super == False)  # noqa: E712
            )
        ).scalar_one()
        profiles_total = (await db.execute(select(func.count()).select_from(Profile))).scalar_one()
        profiles_pending = (
            await db.execute(
                select(func.count()).select_from(Profile).where(Profile.status == ProfileStatusEnum.pending)
            )
        ).scalar_one()
        profiles_approved = (
            await db.execute(
                select(func.count()).select_from(Profile).where(Profile.status == ProfileStatusEnum.approved)
            )
        ).scalar_one()
        requests_pending = (
            await db.execute(
                select(func.count()).select_from(DetailRequest).where(DetailRequest.status == RequestStatusEnum.pending)
            )
        ).scalar_one()
        requests_total = (
            await db.execute(
                select(func.count()).select_from(DetailRequest)
            )
        ).scalar_one()

        return {
            "users": users_count,
            "profiles_total": profiles_total,
            "profiles_pending": profiles_pending,
            "profiles_approved": profiles_approved,
            "requests_pending": requests_pending,
            "requests_total": requests_total,
        }
