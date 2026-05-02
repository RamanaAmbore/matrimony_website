"""Authentication routes."""

import uuid
from typing import Any

from litestar import Controller, Response, delete, get, post
from litestar.connection import Request
from litestar.exceptions import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.schemas.auth import (
    LoginRequest,
    RegisterRequest,
    RegisterResponse,
    UserResponse,
    VerifyEmailRequest,
)
from app.services import auth as auth_svc
from app.services import email as email_svc
from app.services.settings import settings_service


class AuthController(Controller):
    path = "/auth"

    @post("/register", status_code=201)
    async def register(
        self,
        data: RegisterRequest,
        db: AsyncSession,
        request: Request,
    ) -> dict[str, Any]:
        # Check if email exists
        result = await db.execute(select(User).where(User.email == data.email.lower()))
        existing = result.scalar_one_or_none()
        if existing:
            raise HTTPException(
                status_code=409,
                detail={"code": "email_exists", "message": "Email already registered"},
            )

        if len(data.password) < 8:
            raise HTTPException(
                status_code=422,
                detail={"code": "weak_password", "message": "Password must be at least 8 characters"},
            )

        token = auth_svc.generate_token()
        user = User(
            id=uuid.uuid4(),
            email=data.email.lower(),
            password_hash=auth_svc.hash_password(data.password),
            email_verified=False,
            email_verification_token=token,
            is_admin=False,
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)

        # Send verification email (non-blocking failure)
        try:
            await email_svc.send_verification_email(user.email, token)
        except Exception as exc:
            import logging
            logging.getLogger(__name__).warning("Failed to send verification email: %s", exc)

        return {"user_id": str(user.id)}

    @post("/login")
    async def login(
        self,
        data: LoginRequest,
        db: AsyncSession,
        request: Request,
    ) -> dict[str, Any]:
        result = await db.execute(select(User).where(User.email == data.email.lower()))
        user = result.scalar_one_or_none()

        if not user or not auth_svc.verify_password(data.password, user.password_hash):
            raise HTTPException(
                status_code=401,
                detail={"code": "invalid_credentials", "message": "Invalid email or password"},
            )

        # Set session
        request.session["user"] = {
            "user_id": str(user.id),
            "email": user.email,
            "is_admin": user.is_admin,
            "email_verified": user.email_verified,
        }

        return {
            "user_id": str(user.id),
            "email": user.email,
            "is_admin": user.is_admin,
            "email_verified": user.email_verified,
        }

    @post("/logout", status_code=204)
    async def logout(self, request: Request) -> None:
        request.session.clear()

    @post("/verify-email")
    async def verify_email(
        self,
        data: VerifyEmailRequest,
        db: AsyncSession,
    ) -> dict[str, Any]:
        result = await db.execute(
            select(User).where(User.email_verification_token == data.token)
        )
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(
                status_code=400,
                detail={"code": "invalid_token", "message": "Invalid or expired verification token"},
            )

        user.email_verified = True
        user.email_verification_token = None
        await db.commit()

        return {"message": "Email verified successfully"}

    @get("/me")
    async def me(self, request: Request) -> dict[str, Any]:
        user = request.session.get("user")
        if not user:
            raise HTTPException(
                status_code=401,
                detail={"code": "unauthenticated", "message": "Not authenticated"},
            )
        return user
