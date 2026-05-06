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
    DeleteAccountRequest,
    LoginRequest,
    RegisterRequest,
    RegisterResponse,
    UpdateEmailRequest,
    UpdatePasswordRequest,
    UpdatePhoneRequest,
    UserResponse,
    VerifyEmailRequest,
)
from app.services import auth as auth_svc
from app.services import email as email_svc
from app.services.jwt_auth import mint_jwt
from app.services.settings import settings_service

_JWT_COOKIE = "mk_jwt"
_COOKIE_MAX_AGE = 86400 * 7  # 7 days — must match jwt_auth._EXPIRY_SECONDS

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
        # Validate full_name
        full_name = data.full_name.strip()
        if len(full_name) < 2:
            raise HTTPException(
                status_code=422,
                detail={
                    "code": "invalid_name",
                    "message": "Full name must be at least 2 characters.",
                },
            )

        # Validate user_id (handle) format
        if not _HANDLE_RE.match(data.user_id):
            raise HTTPException(
                status_code=422,
                detail={
                    "code": "invalid_user_id",
                    "message": (
                        "User ID must be 3–30 characters, start with a letter, "
                        "and contain only letters, digits, or underscores."
                    ),
                },
            )

        _validate_email(data.email)
        _validate_phone(data.phone_number)
        _validate_password(data.password)

        normalized_phone = _normalize_phone(data.phone_number)

        # Check user_id uniqueness (case-insensitive — DB column is user_handle)
        handle_result = await db.execute(
            select(User).where(func.lower(User.user_handle) == data.user_id.lower())
        )
        if handle_result.scalar_one_or_none():
            raise HTTPException(
                status_code=409,
                detail={"code": "user_id_taken", "message": "That user ID is already taken"},
            )

        # Check email/phone uniqueness — always enforced in prod, skipped in test mode
        is_prod = settings_service.get_bool("is_prod", False)
        if is_prod:
            email_result = await db.execute(
                select(User).where(func.lower(User.email) == data.email.lower())
            )
            if email_result.scalar_one_or_none():
                raise HTTPException(
                    status_code=422,
                    detail={"code": "email_taken", "message": "Email is already registered."},
                )

            phone_result = await db.execute(
                select(User).where(User.phone_number == normalized_phone)
            )
            if phone_result.scalar_one_or_none():
                raise HTTPException(
                    status_code=422,
                    detail={"code": "phone_taken", "message": "Phone number is already registered."},
                )

        token = auth_svc.generate_token()
        user = User(
            id=uuid.uuid4(),
            email=data.email.lower(),
            full_name=full_name,
            user_handle=data.user_id,
            phone_number=normalized_phone,
            password_hash=auth_svc.hash_password(data.password),
            email_verified=False,
            is_approved=False,
            email_verification_token=token,
            is_admin=False,
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)

        # Send verification email (non-blocking failure)
        try:
            await email_svc.send_verification_email(user.email, token, full_name=full_name)
        except Exception as exc:
            import logging
            logging.getLogger(__name__).warning("Failed to send verification email: %s", exc)

        from app.services.telegram import notify_user_registered
        asyncio.create_task(notify_user_registered(
            name=full_name,
            email=data.email,
            phone=normalized_phone,
        ))

        asyncio.create_task(email_svc.send_admin_new_user(
            full_name=full_name,
            email=data.email,
            phone=normalized_phone,
            user_handle=data.user_id,
        ))

        return {"uuid": str(user.id)}

    @post("/login", status_code=200)
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

        if user.is_revoked:
            raise HTTPException(
                status_code=403,
                detail={
                    "code": "user_revoked",
                    "message": "Your account has been revoked. Contact admin to reinstate or to permanently delete it.",
                },
            )
        # Suspended users CAN log in — that's the whole point of suspend
        # vs revoke. The frontend shows a banner and the search filter
        # hides their profiles until they unsuspend.

        token = mint_jwt(
            user_id=str(user.id),
            handle=user.user_handle,
            email=user.email,
            full_name=user.full_name,
            is_admin=user.is_admin,
            email_verified=user.email_verified,
            is_approved=user.is_approved,
            is_super=user.is_super,
            is_paused=user.is_paused,
            is_suspended=user.is_suspended,
        )

        body: dict[str, Any] = {
            "uuid": str(user.id),
            "user_id": user.user_handle,
            "email": user.email,
            "full_name": user.full_name,
            "is_admin": user.is_admin,
            "is_super": user.is_super,
            "email_verified": user.email_verified,
            "is_approved": user.is_approved,
            "is_paused": user.is_paused,
            "is_suspended": user.is_suspended,
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

    @post("/verify-email", status_code=200)
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
        await db.refresh(user)

        return {"message": "Email verified successfully"}

    @post("/me/resend-verification", status_code=200)
    async def resend_my_verification(
        self,
        db: AsyncSession,
        request: Request,
    ) -> dict[str, Any]:
        """H7: self-service resend of the email verification link.

        For users who never received the original email or whose token
        expired. No password required (authenticated session is enough),
        but rate-limited to one fresh token per call.
        """
        payload = request.scope.get("user_payload")
        if not payload:
            raise HTTPException(status_code=401, detail={"code": "unauthenticated", "message": "Authentication required"})

        result = await db.execute(select(User).where(User.id == uuid.UUID(payload["sub"])))
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=401, detail={"code": "unauthenticated", "message": "Authentication required"})
        if user.email_verified:
            raise HTTPException(
                status_code=409,
                detail={"code": "already_verified", "message": "Your email is already verified"},
            )

        token = auth_svc.generate_token()
        user.email_verification_token = token
        await db.commit()

        try:
            await email_svc.send_verification_email(user.email, token, full_name=user.full_name)
        except Exception as exc:
            import logging
            logging.getLogger(__name__).warning("Failed to send verification email: %s", exc)

        return {"message": f"Verification email sent to {user.email}"}

    # ── Account self-service ────────────────────────────────────────────────
    # All three updates require the current password as a confirmation.
    # Email-update resets email_verified+is_approved (the user must re-verify
    # the new email and an admin must re-approve). Phone + password updates
    # leave the account state alone.

    @post("/me/email", status_code=200)
    async def update_email(
        self,
        data: UpdateEmailRequest,
        db: AsyncSession,
        request: Request,
    ) -> dict[str, Any]:
        payload = request.scope.get("user_payload")
        if not payload:
            raise HTTPException(status_code=401, detail={"code": "unauthenticated", "message": "Authentication required"})

        result = await db.execute(select(User).where(User.id == uuid.UUID(payload["sub"])))
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=401, detail={"code": "unauthenticated", "message": "Authentication required"})

        if not auth_svc.verify_password(data.current_password, user.password_hash):
            raise HTTPException(status_code=403, detail={"code": "wrong_password", "message": "Current password is incorrect"})

        new_email = data.new_email.strip().lower()
        _validate_email(new_email)
        if new_email == user.email:
            raise HTTPException(status_code=422, detail={"code": "same_email", "message": "New email must differ from the current one"})

        # Uniqueness — always enforced for email changes (operators almost
        # certainly want this even in test mode).
        existing = await db.execute(select(User).where(func.lower(User.email) == new_email))
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=409, detail={"code": "email_taken", "message": "That email is already registered"})

        old_email = user.email
        token = auth_svc.generate_token()
        user.email = new_email
        user.email_verified = False
        user.is_approved = False
        user.email_verification_token = token
        await db.commit()

        try:
            await email_svc.send_verification_email(new_email, token, full_name=user.full_name)
        except Exception as exc:
            import logging
            logging.getLogger(__name__).warning("Failed to send verification email after update: %s", exc)

        # G10: notify ops the user re-entered the pending queue. They were
        # approved before, but email change resets email_verified+is_approved
        # so admin needs to re-approve after the user verifies the new address.
        try:
            from app.services.telegram import notify_user_email_changed
            asyncio.create_task(notify_user_email_changed(
                name=user.full_name, old_email=old_email, new_email=new_email,
            ))
        except Exception as exc:
            import logging
            logging.getLogger(__name__).warning("Failed to schedule email-change ops notification: %s", exc)

        return {
            "message": "Email updated. Please verify the new address from the link we just sent. Account approval will need re-confirmation by an admin.",
            "email": new_email,
        }

    @post("/me/phone", status_code=200)
    async def update_phone(
        self,
        data: UpdatePhoneRequest,
        db: AsyncSession,
        request: Request,
    ) -> dict[str, Any]:
        payload = request.scope.get("user_payload")
        if not payload:
            raise HTTPException(status_code=401, detail={"code": "unauthenticated", "message": "Authentication required"})

        result = await db.execute(select(User).where(User.id == uuid.UUID(payload["sub"])))
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=401, detail={"code": "unauthenticated", "message": "Authentication required"})

        if not auth_svc.verify_password(data.current_password, user.password_hash):
            raise HTTPException(status_code=403, detail={"code": "wrong_password", "message": "Current password is incorrect"})

        _validate_phone(data.new_phone)
        normalized = _normalize_phone(data.new_phone)
        if normalized == user.phone_number:
            raise HTTPException(status_code=422, detail={"code": "same_phone", "message": "New phone must differ from the current one"})

        # Uniqueness check (always enforced — same rationale as email)
        existing = await db.execute(select(User).where(User.phone_number == normalized))
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=409, detail={"code": "phone_taken", "message": "That phone number is already registered"})

        user.phone_number = normalized
        await db.commit()
        return {"message": "Phone number updated", "phone_number": normalized}

    @post("/me/password", status_code=200)
    async def update_password(
        self,
        data: UpdatePasswordRequest,
        db: AsyncSession,
        request: Request,
    ) -> dict[str, Any]:
        payload = request.scope.get("user_payload")
        if not payload:
            raise HTTPException(status_code=401, detail={"code": "unauthenticated", "message": "Authentication required"})

        result = await db.execute(select(User).where(User.id == uuid.UUID(payload["sub"])))
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=401, detail={"code": "unauthenticated", "message": "Authentication required"})

        if not auth_svc.verify_password(data.current_password, user.password_hash):
            raise HTTPException(status_code=403, detail={"code": "wrong_password", "message": "Current password is incorrect"})

        _validate_password(data.new_password)
        if data.new_password == data.current_password:
            raise HTTPException(status_code=422, detail={"code": "same_password", "message": "New password must differ from the current one"})

        user.password_hash = auth_svc.hash_password(data.new_password)
        await db.commit()
        return {"message": "Password updated"}

    @post("/me/delete", status_code=200)
    async def delete_account(
        self,
        data: DeleteAccountRequest,
        db: AsyncSession,
        request: Request,
    ) -> Response[dict[str, Any]]:
        """G9: self-service account deletion.

        Requires the user's current password AND a literal 'DELETE'
        confirmation string. Cascades the user record (profiles, photos,
        detail requests) and clears the JWT cookie. Super-users cannot
        delete themselves through this path — they are bootstrap-pinned.
        """
        payload = request.scope.get("user_payload")
        if not payload:
            raise HTTPException(status_code=401, detail={"code": "unauthenticated", "message": "Authentication required"})

        if data.confirmation.strip() != "DELETE":
            raise HTTPException(
                status_code=422,
                detail={"code": "confirmation_mismatch", "message": "Type DELETE to confirm account deletion"},
            )

        result = await db.execute(select(User).where(User.id == uuid.UUID(payload["sub"])))
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=401, detail={"code": "unauthenticated", "message": "Authentication required"})

        if not auth_svc.verify_password(data.current_password, user.password_hash):
            raise HTTPException(status_code=403, detail={"code": "wrong_password", "message": "Current password is incorrect"})

        if user.is_super:
            raise HTTPException(
                status_code=403,
                detail={"code": "forbidden", "message": "Super-users cannot self-delete; edit bootstrap.py"},
            )

        # Unlink owned photo files before cascade-deleting the user — same
        # pattern as the admin delete-user path so we don't leak JPEGs.
        from app.config import MEDIA_ROOT
        from app.models.photo import Photo
        from app.models.profile import Profile

        photos_to_unlink = await db.execute(
            select(Photo)
            .join(Profile, Profile.id == Photo.profile_id)
            .where(Profile.owner_user_id == user.id)
        )
        for photo in photos_to_unlink.scalars():
            for path_rel in (photo.passport_path, photo.blurred_path, photo.thumb_path):
                fpath = MEDIA_ROOT / path_rel
                if fpath.exists():
                    try:
                        fpath.unlink()
                    except OSError:
                        pass

        owned_profile_ids = await db.execute(select(Profile.id).where(Profile.owner_user_id == user.id))
        for (pid,) in owned_profile_ids.all():
            for sub in (MEDIA_ROOT / "profiles" / str(pid)).rglob("*"):
                pass
            profile_dir = MEDIA_ROOT / "profiles" / str(pid)
            if profile_dir.exists():
                for child in profile_dir.iterdir():
                    if child.is_dir() and not any(child.iterdir()):
                        try:
                            child.rmdir()
                        except OSError:
                            pass
                if not any(profile_dir.iterdir()):
                    try:
                        profile_dir.rmdir()
                    except OSError:
                        pass

        deleted_email = user.email
        deleted_name = user.full_name
        await db.delete(user)
        await db.commit()

        # Clear cookie and return 200.
        response: Response[dict[str, Any]] = Response(content={"deleted": True, "email": deleted_email})
        response.delete_cookie(key=_JWT_COOKIE, path="/")

        # Notify ops asynchronously.
        try:
            from app.services.telegram import _send as _tg_send
            asyncio.create_task(_tg_send(
                f"🗑️ <b>User self-deleted</b>\n{deleted_name}\n{deleted_email}"
            ))
        except Exception:
            pass

        return response

    @post("/me/pause", status_code=200)
    async def pause_account(
        self,
        request: Request,
        db: AsyncSession,
    ) -> dict[str, Any]:
        """Self-service vacation mode. Sets is_paused=True. The user can
        still log in (banner shown) but their profiles drop from search
        and they can't create new ones until they unpause.

        Idempotent — calling on an already-paused account returns 200.
        """
        payload = request.scope.get("user_payload")
        if not payload:
            raise HTTPException(status_code=401, detail={"code": "unauthenticated", "message": "Authentication required"})
        result = await db.execute(select(User).where(User.id == uuid.UUID(payload["sub"])))
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=401, detail={"code": "unauthenticated", "message": "Authentication required"})
        if user.is_revoked:
            raise HTTPException(status_code=403, detail={"code": "user_revoked", "message": "Account is revoked"})
        user.is_paused = True
        await db.commit()
        return {"is_paused": True, "message": "Your account is now paused. Profiles hidden from search."}

    @post("/me/unpause", status_code=200)
    async def unpause_account(
        self,
        request: Request,
        db: AsyncSession,
    ) -> dict[str, Any]:
        """Clear self-set vacation mode. is_suspended (admin-set) is NOT
        cleared by this — only an admin can lift a suspension."""
        payload = request.scope.get("user_payload")
        if not payload:
            raise HTTPException(status_code=401, detail={"code": "unauthenticated", "message": "Authentication required"})
        result = await db.execute(select(User).where(User.id == uuid.UUID(payload["sub"])))
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=401, detail={"code": "unauthenticated", "message": "Authentication required"})
        user.is_paused = False
        await db.commit()
        msg = "Your account is active again."
        if user.is_suspended:
            msg = (
                "Vacation mode cleared, but your account is still under an admin "
                "suspension. Contact support to lift the suspension."
            )
        return {"is_paused": False, "is_suspended": user.is_suspended, "message": msg}

    @get("/me")
    async def me(self, request: Request, db: AsyncSession) -> dict[str, Any]:
        """Return the current user, re-queried from the DB on each call so
        role changes (promote, demote, revoke, approve, verify) take effect
        on the next page load instead of requiring a re-login.

        If the user was deleted or revoked since the JWT was minted, raise
        401. The frontend already clears the cookie + redirects on 401.
        """
        payload: dict[str, Any] | None = request.scope.get("user_payload")
        if not payload:
            raise HTTPException(
                status_code=401,
                detail={"code": "unauthenticated", "message": "Not authenticated"},
            )

        try:
            uid = uuid.UUID(payload["sub"])
        except (KeyError, ValueError):
            raise HTTPException(
                status_code=401,
                detail={"code": "unauthenticated", "message": "Not authenticated"},
            )

        result = await db.execute(select(User).where(User.id == uid))
        user = result.scalar_one_or_none()
        if not user or user.is_revoked:
            raise HTTPException(
                status_code=401,
                detail={"code": "session_invalid", "message": "Session no longer valid"},
            )

        return {
            "uuid": str(user.id),
            "user_id": user.user_handle,
            "email": user.email,
            "full_name": user.full_name,
            "is_admin": user.is_admin,
            "is_super": user.is_super,
            "email_verified": user.email_verified,
            "is_approved": user.is_approved,
            "is_paused": user.is_paused,
            "is_suspended": user.is_suspended,
        }
