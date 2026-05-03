"""Authentication routes."""

import asyncio
import re
import uuid
from typing import Any

from litestar import Controller, Response, get, post
from litestar.connection import Request
from litestar.exceptions import HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import IS_PROD
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
from app.services.jwt_auth import mint_jwt
from app.services.settings import settings_service

_JWT_COOKIE = "mk_jwt"
_COOKIE_MAX_AGE = 86400 * 30  # 30 days — must match jwt_auth._EXPIRY_SECONDS

# ^[A-Za-z][A-Za-z0-9_]{2,29}$  →  starts with a letter, then 2–29 alphanumeric/underscore
# total length: 3–30 characters
_HANDLE_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_]{2,29}$")

# Email: local@domain.tld — same shape as the frontend regex so client and
# server agree on what is accepted.
_EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")

# Phone: must start with '+', spaces/hyphens/dots stripped before check.
_PHONE_STRIP_RE = re.compile(r"[\s\-.]")
_PHONE_RE = re.compile(r"^\+\d{7,17}$")

# Password: at least 8 chars, must contain at least one letter and one digit.
_PASSWORD_LETTER_RE = re.compile(r"[A-Za-z]")
_PASSWORD_DIGIT_RE = re.compile(r"\d")
_PASSWORD_MIN_LEN = 8


def _validate_email(value: str) -> None:
    if not _EMAIL_RE.match(value):
        raise HTTPException(
            status_code=422,
            detail={"code": "invalid_email", "message": "Enter a valid email address"},
        )


def _normalize_phone(value: str) -> str:
    return _PHONE_STRIP_RE.sub("", value.strip())


def _validate_phone(value: str) -> None:
    if not _PHONE_RE.match(_normalize_phone(value)):
        raise HTTPException(
            status_code=422,
            detail={
                "code": "invalid_phone",
                "message": "Phone must start with '+' and include country code (e.g. +91 9840770711).",
            },
        )


def _validate_password(value: str) -> None:
    if (
        len(value) < _PASSWORD_MIN_LEN
        or not _PASSWORD_LETTER_RE.search(value)
        or not _PASSWORD_DIGIT_RE.search(value)
    ):
        raise HTTPException(
            status_code=422,
            detail={
                "code": "weak_password",
                "message": (
                    "Password must be at least 8 characters and contain "
                    "at least one letter and one digit."
                ),
            },
        )


class AuthController(Controller):
    path = "/auth"

    @post("/register", status_code=201)
    async def register(
        self,
        data: RegisterRequest,
        db: AsyncSession,
        request: Request,
    ) -> dict[str, Any]:
        # Validate handle format
        if not _HANDLE_RE.match(data.user_handle):
            raise HTTPException(
                status_code=422,
                detail={
                    "code": "invalid_handle",
                    "message": (
                        "Handle must be 3–30 characters, start with a letter, "
                        "and contain only letters, digits, or underscores."
                    ),
                },
            )

        _validate_email(data.email)
        _validate_phone(data.phone_number)
        _validate_password(data.password)

        normalized_phone = _normalize_phone(data.phone_number)

        # Check handle uniqueness (case-insensitive)
        handle_result = await db.execute(
            select(User).where(func.lower(User.user_handle) == data.user_handle.lower())
        )
        if handle_result.scalar_one_or_none():
            raise HTTPException(
                status_code=409,
                detail={"code": "handle_taken", "message": "That handle is already taken"},
            )

        # Check email uniqueness (case-insensitive)
        email_result = await db.execute(
            select(User).where(func.lower(User.email) == data.email.lower())
        )
        if email_result.scalar_one_or_none():
            raise HTTPException(
                status_code=409,
                detail={"code": "email_taken", "message": "Email already registered"},
            )

        # Check phone uniqueness
        phone_result = await db.execute(
            select(User).where(User.phone_number == normalized_phone)
        )
        if phone_result.scalar_one_or_none():
            raise HTTPException(
                status_code=409,
                detail={"code": "phone_taken", "message": "Phone number already registered"},
            )

        token = auth_svc.generate_token()
        user = User(
            id=uuid.uuid4(),
            email=data.email.lower(),
            user_handle=data.user_handle,
            phone_number=normalized_phone,
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

        from app.services.telegram import notify_user_registered
        asyncio.create_task(notify_user_registered(
            name=data.user_handle,
            email=data.email,
            phone=normalized_phone,
        ))

        return {"user_id": str(user.id)}

    @post("/login")
    async def login(
        self,
        data: LoginRequest,
        db: AsyncSession,
        request: Request,
    ) -> Response[dict[str, Any]]:
        # Route lookup: identifier containing '@' is treated as an email
        if "@" in data.identifier:
            result = await db.execute(
                select(User).where(func.lower(User.email) == data.identifier.lower())
            )
        else:
            result = await db.execute(
                select(User).where(func.lower(User.user_handle) == data.identifier.lower())
            )
        user = result.scalar_one_or_none()

        if not user or not auth_svc.verify_password(data.password, user.password_hash):
            raise HTTPException(
                status_code=401,
                detail={"code": "invalid_credentials", "message": "Invalid identifier or password"},
            )

        token = mint_jwt(
            user_id=str(user.id),
            handle=user.user_handle,
            email=user.email,
            is_admin=user.is_admin,
            email_verified=user.email_verified,
        )

        body: dict[str, Any] = {
            "user_id": str(user.id),
            "user_handle": user.user_handle,
            "email": user.email,
            "is_admin": user.is_admin,
            "email_verified": user.email_verified,
        }

        response: Response[dict[str, Any]] = Response(content=body)
        response.set_cookie(
            key=_JWT_COOKIE,
            value=token,
            max_age=_COOKIE_MAX_AGE,
            httponly=True,
            samesite="lax",
            secure=IS_PROD,
            path="/",
        )
        return response

    @post("/logout", status_code=204)
    async def logout(self, request: Request) -> Response[None]:
        response: Response[None] = Response(content=None, status_code=204)
        response.delete_cookie(key=_JWT_COOKIE, path="/")
        return response

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
        payload: dict[str, Any] | None = request.scope.get("user_payload")
        if not payload:
            raise HTTPException(
                status_code=401,
                detail={"code": "unauthenticated", "message": "Not authenticated"},
            )
        return {
            "user_id": payload["sub"],
            "user_handle": payload.get("handle", ""),
            "email": payload.get("email", ""),
            "is_admin": payload.get("is_admin", False),
            "email_verified": payload.get("email_verified", False),
        }
