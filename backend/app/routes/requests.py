"""Detail request routes."""

import asyncio
import random
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


async def _generate_request_number(db: AsyncSession) -> str:
    """Generate unique RQ-#########  request number (12 chars total)."""
    for _ in range(10):
        num = f"RQ-{random.randint(0, 999_999_999):09d}"
        result = await db.execute(
            select(DetailRequest).where(DetailRequest.request_number == num)
        )
        if result.scalar_one_or_none() is None:
            return num
    raise RuntimeError("Could not generate unique request number after 10 attempts")


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
