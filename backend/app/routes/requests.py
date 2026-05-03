"""Detail request routes."""

import asyncio
import uuid
from datetime import datetime, timezone
from typing import Any

from litestar import Controller, get, post
from litestar.connection import Request
from litestar.exceptions import HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.profile import Profile, ProfileStatusEnum
from app.models.request import DetailRequest, RequestStatusEnum
from app.models.user import User
from app.schemas.request import CreateDetailRequest


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
        from app.models.setting import Setting
        from app.services import email as email_svc
        from app.services.settings import settings_service

        owner_email = settings_service.get_str("owner_email", "admin.marathakalyanam@gmail.com")
        result2 = await db.execute(select(User).where(User.id == requester_id))
        requester_user = result2.scalar_one_or_none()
        requester_name = requester_user.email if requester_user else str(requester_id)
        profile_name = profile.first_name

        try:
            await email_svc.send_detail_request_received(owner_email, requester_name, profile_name)
        except Exception as exc:
            import logging
            logging.getLogger(__name__).warning("Failed to send request notification: %s", exc)

        from app.services.telegram import notify_request_received
        asyncio.create_task(notify_request_received(
            requester=requester_name,
            profile_name=f"{profile.first_name} {profile.last_name or ''}".strip(),
        ))

        return _serialize_request(detail_req)

    @get("/requests/mine")
    async def my_requests(
        self,
        request: Request,
        db: AsyncSession,
    ) -> list[dict[str, Any]]:
        user = request.scope.get("user_payload")
        if not user:
            raise HTTPException(status_code=401, detail={"code": "unauthenticated", "message": "Authentication required"})

        requester_id = uuid.UUID(user["sub"])
        result = await db.execute(
            select(DetailRequest)
            .where(DetailRequest.requester_user_id == requester_id)
            .order_by(DetailRequest.created_at.desc())
        )
        reqs = result.scalars().all()
        return [_serialize_request(r) for r in reqs]
