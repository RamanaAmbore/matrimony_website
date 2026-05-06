"""Detail request routes."""

import asyncio
import uuid
from datetime import datetime, timezone
from typing import Any

from litestar import Controller, delete, get, post
from litestar.connection import Request
from litestar.exceptions import HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.photo import Photo
from app.models.profile import Profile, ProfileStatusEnum
from app.models.request import DetailRequest, RequestStatusEnum
from app.models.user import User
from app.schemas.request import CreateDetailRequest
from app.services.short_codes import generate_unique_code


async def _generate_request_number(db: AsyncSession) -> str:
    """Generate unique RQ-XXXXXX request number (9 chars total)."""
    return await generate_unique_code(db, DetailRequest, DetailRequest.request_number, "RQ")


def _serialize_request(req: DetailRequest) -> dict[str, Any]:
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
    }


class RequestController(Controller):
    path = ""

    @post("/profiles/{profile_id:str}/request", status_code=201)
    async def create_request(
        self,
        profile_id: str,
        data: CreateDetailRequest,
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

        result = await db.execute(select(Profile).where(Profile.id == pid))
        profile = result.scalar_one_or_none()
        if not profile:
            raise HTTPException(status_code=404, detail={"code": "not_found", "message": "Profile not found"})

        if profile.status != ProfileStatusEnum.approved:
            raise HTTPException(
                status_code=409,
                detail={"code": "profile_not_approved", "message": "Can only request details for approved profiles"},
            )

        requester_id = uuid.UUID(user["sub"])
        if profile.owner_user_id == requester_id:
            raise HTTPException(
                status_code=409,
                detail={"code": "own_profile", "message": "Cannot request details for your own profile"},
            )

        detail_req = DetailRequest(
            id=uuid.uuid4(),
            request_number=await _generate_request_number(db),
            requester_user_id=requester_id,
            profile_id=pid,
            status=RequestStatusEnum.pending,
            message=data.message,
        )
        db.add(detail_req)
        try:
            await db.commit()
        except IntegrityError:
            await db.rollback()
            raise HTTPException(
                status_code=409,
                detail={"code": "duplicate_request", "message": "You have already requested details for this profile"},
            )

        await db.refresh(detail_req)

        # Notify admin
        from app.services import email as email_svc

        result2 = await db.execute(select(User).where(User.id == requester_id))
        requester_user = result2.scalar_one_or_none()
        requester_name = requester_user.full_name or requester_user.email if requester_user else str(requester_id)
        requester_email_addr = requester_user.email if requester_user else str(requester_id)
        profile_full_name = f"{profile.first_name} {profile.last_name or ''}".strip()

        try:
            await email_svc.send_admin_view_request(
                requester_name=requester_name,
                requester_email=requester_email_addr,
                profile_name=profile_full_name,
                profile_id=str(profile.id),
                message=data.message if hasattr(data, "message") else None,
            )
        except Exception as exc:
            import logging
            logging.getLogger(__name__).warning("Failed to send request notification: %s", exc)

        from app.services.telegram import notify_request_received
        asyncio.create_task(notify_request_received(
            requester=requester_name,
            profile_name=profile_full_name,
        ))

        return _serialize_request(detail_req)

    @get("/requests/mine")
    async def my_requests(
        self,
        request: Request,
        db: AsyncSession,
    ) -> list[dict[str, Any]]:
        """List requests the current user has made, enriched with the profile
        snapshot (name, gender, age, city, primary blurred photo) so the
        frontend can render a grid without an extra round-trip per row."""
        user = request.scope.get("user_payload")
        if not user:
            raise HTTPException(status_code=401, detail={"code": "unauthenticated", "message": "Authentication required"})

        requester_id = uuid.UUID(user["sub"])
        result = await db.execute(
            select(DetailRequest)
            .where(DetailRequest.requester_user_id == requester_id)
            .options(selectinload(DetailRequest.profile).selectinload(Profile.photos))
            .order_by(DetailRequest.created_at.desc())
        )
        base = str(request.base_url).rstrip("/")
        out: list[dict[str, Any]] = []
        for r in result.scalars().all():
            row = _serialize_request(r)
            p = r.profile
            if p is not None:
                primary_photo = next((ph for ph in p.photos if ph.is_primary), None) or (p.photos[0] if p.photos else None)
                row.update({
                    "profile_first_name": p.first_name,
                    "profile_last_name": p.last_name,
                    "profile_number": p.profile_number,
                    "profile_gender": p.gender.value if p.gender else None,
                    "profile_dob": p.dob.isoformat() if p.dob else None,
                    "profile_city": p.city,
                    "profile_state": p.state,
                    "profile_status": p.status.value if p.status else None,
                    "profile_blurred_url": (
                        f"{base}/media/{primary_photo.blurred_path}" if primary_photo else None
                    ),
                })
            out.append(row)
        return out

    @delete("/requests/{request_id:str}", status_code=204)
    async def delete_request(
        self,
        request_id: str,
        request: Request,
        db: AsyncSession,
    ) -> None:
        """Owner-side delete. Lets the requester remove a request they made,
        regardless of status (pending / approved / rejected)."""
        user = request.scope.get("user_payload")
        if not user:
            raise HTTPException(status_code=401, detail={"code": "unauthenticated", "message": "Authentication required"})

        try:
            rid = uuid.UUID(request_id)
        except ValueError:
            raise HTTPException(status_code=404, detail={"code": "not_found", "message": "Request not found"})

        result = await db.execute(select(DetailRequest).where(DetailRequest.id == rid))
        req = result.scalar_one_or_none()
        if not req:
            raise HTTPException(status_code=404, detail={"code": "not_found", "message": "Request not found"})

        is_owner = str(req.requester_user_id) == user["sub"]
        is_admin = bool(user.get("is_admin"))
        if not is_owner and not is_admin:
            raise HTTPException(status_code=403, detail={"code": "forbidden", "message": "Not your request"})

        await db.delete(req)
        await db.commit()
