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
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

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
from app.services import email as email_svc
from app.services.settings import settings_service, SENSITIVE_KEYS

logger = logging.getLogger(__name__)


class BroadcastEmailBody(msgspec.Struct):
    subject: str
    body_html: str
    filter_verified_only: bool = True
    filter_approved_only: bool = False


def _require_admin(request: Request) -> dict[str, Any]:
    payload = request.scope.get("user_payload")
    if not payload:
        raise HTTPException(status_code=401, detail={"code": "unauthenticated", "message": "Authentication required"})
    if not payload.get("is_admin"):
        raise HTTPException(status_code=403, detail={"code": "forbidden", "message": "Admin access required"})
    return payload


def _serialize_profile(profile: Profile, request: Request) -> dict[str, Any]:
    base = str(request.base_url).rstrip("/")
    photos = []
    for photo in profile.photos:
        photos.append({
            "id": str(photo.id),
            "passport_url": f"{base}/media/{photo.passport_path}",
            "blurred_url": f"{base}/media/{photo.blurred_path}",
            "thumb_url": f"{base}/media/{photo.thumb_path}",
            "is_primary": photo.is_primary,
        })

    def age(dob: date) -> int:
        today = date.today()
        return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))

    return {
        "id": str(profile.id),
        "profile_number": profile.profile_number,
        "owner_user_id": str(profile.owner_user_id),
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
    return {
        "id": str(req.id),
        "requester_user_id": str(req.requester_user_id),
        "profile_id": str(req.profile_id),
        "status": req.status.value,
        "message": req.message,
        "admin_notes": req.admin_notes,
        "responded_at": req.responded_at.isoformat() if req.responded_at else None,
        "created_at": req.created_at.isoformat(),
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
        users_count = (await db.execute(select(func.count()).select_from(User))).scalar_one()
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
                select(func.count()).select_from(Profile).where(Profile.status == ProfileStatusEnum.rejected)
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
                select(func.count()).select_from(DetailRequest).where(DetailRequest.status == RequestStatusEnum.rejected)
            )
        ).scalar_one()
        requests_total = (
            await db.execute(
                select(func.count()).select_from(DetailRequest)
            )
        ).scalar_one()

        stats = {
            "users": users_count,
            "profiles_total": profiles_total,
            "profiles_pending": profiles_pending,
            "profiles_approved": profiles_approved,
            "profiles_rejected": profiles_rejected,
            "profiles_draft": profiles_draft,
            "requests_pending": requests_pending,
            "requests_approved": requests_approved,
            "requests_rejected": requests_rejected,
            "requests_total": requests_total,
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

        await db.refresh(profile, ["photos"])
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

        profile.status = ProfileStatusEnum.rejected
        profile.admin_notes = data.admin_notes
        await db.commit()

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

        await db.refresh(profile, ["photos"])
        return _serialize_profile(profile, request)

    # --- Requests ---
    @get("/requests")
    async def list_requests(
        self,
        request: Request,
        db: AsyncSession,
        status: Optional[str] = None,
    ) -> list[dict[str, Any]]:
        _require_admin(request)
        query = select(DetailRequest)
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

        result = await db.execute(select(DetailRequest).where(DetailRequest.id == rid))
        req = result.scalar_one_or_none()
        if not req:
            raise HTTPException(status_code=404, detail={"code": "not_found", "message": "Request not found"})

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
        return _serialize_request(req)

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

        req.status = RequestStatusEnum.rejected
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
        return _serialize_request(req)

    # --- Users ---
    @get("/users")
    async def list_users(
        self,
        request: Request,
        db: AsyncSession,
    ) -> list[dict[str, Any]]:
        _require_admin(request)
        result = await db.execute(select(User).order_by(User.created_at.desc()))
        users = result.scalars().all()
        return [
            {
                "user_id": str(u.id),
                "email": u.email,
                "full_name": u.full_name,
                "user_handle": u.user_handle,
                "phone_number": u.phone_number,
                "is_admin": u.is_admin,
                "email_verified": u.email_verified,
                "is_approved": u.is_approved,
                "created_at": u.created_at.isoformat(),
            }
            for u in users
        ]

    @post("/users/{user_id:str}/promote")
    async def promote_user(
        self,
        user_id: str,
        request: Request,
        db: AsyncSession,
    ) -> dict[str, Any]:
        _require_admin(request)

        try:
            uid = uuid.UUID(user_id)
        except ValueError:
            raise HTTPException(status_code=404, detail={"code": "not_found", "message": "User not found"})

        result = await db.execute(select(User).where(User.id == uid))
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=404, detail={"code": "not_found", "message": "User not found"})

        user.is_admin = True
        await db.commit()
        await db.refresh(user)
        return {
            "user_id": str(user.id),
            "email": user.email,
            "full_name": user.full_name,
            "user_handle": user.user_handle,
            "phone_number": user.phone_number,
            "is_admin": user.is_admin,
            "email_verified": user.email_verified,
            "is_approved": user.is_approved,
            "created_at": user.created_at.isoformat(),
        }

    @post("/users/{user_id:str}/verify_email")
    async def verify_user_email(
        self,
        user_id: str,
        request: Request,
        db: AsyncSession,
    ) -> dict[str, Any]:
        """Admin override: mark a user's email as verified."""
        _require_admin(request)

        try:
            uid = uuid.UUID(user_id)
        except ValueError:
            raise HTTPException(status_code=404, detail={"code": "not_found", "message": "User not found"})

        result = await db.execute(select(User).where(User.id == uid))
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=404, detail={"code": "not_found", "message": "User not found"})

        user.email_verified = True
        user.email_verification_token = None
        await db.commit()
        await db.refresh(user)
        return {
            "user_id": str(user.id),
            "email": user.email,
            "full_name": user.full_name,
            "user_handle": user.user_handle,
            "phone_number": user.phone_number,
            "is_admin": user.is_admin,
            "email_verified": user.email_verified,
            "is_approved": user.is_approved,
            "created_at": user.created_at.isoformat(),
        }

    @post("/users/{user_id:str}/approve")
    async def approve_user(
        self,
        user_id: str,
        request: Request,
        db: AsyncSession,
    ) -> dict[str, Any]:
        """Admin: mark a user as approved so they can create profiles."""
        _require_admin(request)

        try:
            uid = uuid.UUID(user_id)
        except ValueError:
            raise HTTPException(status_code=404, detail={"code": "not_found", "message": "User not found"})

        result = await db.execute(select(User).where(User.id == uid))
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=404, detail={"code": "not_found", "message": "User not found"})

        user.is_approved = True
        await db.commit()
        await db.refresh(user)

        from app.services.telegram import notify_user_approved
        asyncio.create_task(notify_user_approved(name=user.full_name, email=user.email))

        asyncio.create_task(email_svc.send_account_approved(user.email, user.full_name))

        return {
            "user_id": str(user.id),
            "email": user.email,
            "full_name": user.full_name,
            "user_handle": user.user_handle,
            "phone_number": user.phone_number,
            "is_admin": user.is_admin,
            "email_verified": user.email_verified,
            "is_approved": user.is_approved,
            "created_at": user.created_at.isoformat(),
        }

    @post("/users/{user_id:str}/unapprove")
    async def unapprove_user(
        self,
        user_id: str,
        request: Request,
        db: AsyncSession,
    ) -> dict[str, Any]:
        """Admin: revoke approval from a user."""
        _require_admin(request)

        try:
            uid = uuid.UUID(user_id)
        except ValueError:
            raise HTTPException(status_code=404, detail={"code": "not_found", "message": "User not found"})

        result = await db.execute(select(User).where(User.id == uid))
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=404, detail={"code": "not_found", "message": "User not found"})

        user.is_approved = False
        await db.commit()
        await db.refresh(user)

        return {
            "user_id": str(user.id),
            "email": user.email,
            "full_name": user.full_name,
            "user_handle": user.user_handle,
            "phone_number": user.phone_number,
            "is_admin": user.is_admin,
            "email_verified": user.email_verified,
            "is_approved": user.is_approved,
            "created_at": user.created_at.isoformat(),
        }

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

        query = select(User)
        if data.filter_verified_only:
            query = query.where(User.email_verified == True)  # noqa: E712
        if data.filter_approved_only:
            query = query.where(User.is_approved == True)  # noqa: E712
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

        users_count = (await db.execute(select(func.count()).select_from(User))).scalar_one()
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
