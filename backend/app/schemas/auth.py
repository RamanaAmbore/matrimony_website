"""Auth schemas."""
from __future__ import annotations

import uuid

import msgspec


class RegisterRequest(msgspec.Struct):
    email: str
    password: str
    user_id: str  # the public handle/alias the user picks at registration
    phone_number: str
    full_name: str


class LoginRequest(msgspec.Struct):
    identifier: str  # email address OR user_id (handle)
    password: str


class VerifyEmailRequest(msgspec.Struct):
    token: str


class UserResponse(msgspec.Struct):
    uuid: str
    user_id: str
    email: str
    full_name: str
    is_admin: bool
    email_verified: bool
    is_approved: bool


class RegisterResponse(msgspec.Struct):
    uuid: str


class UpdateEmailRequest(msgspec.Struct):
    new_email: str
    current_password: str


class UpdatePhoneRequest(msgspec.Struct):
    new_phone: str
    current_password: str


class UpdatePasswordRequest(msgspec.Struct):
    current_password: str
    new_password: str


class DeleteAccountRequest(msgspec.Struct):
    """Self-service account deletion. Requires the user's current password
    AND a typed confirmation phrase ('DELETE') so it cannot be triggered
    by accident or by a CSRF-style replay."""
    current_password: str
    confirmation: str


class ForgotPasswordRequest(msgspec.Struct):
    email: str


class ResetPasswordRequest(msgspec.Struct):
    token: str
    new_password: str


class ImpersonatorInfo(msgspec.Struct):
    """Minimal info about the real super-user behind the wheel when impersonating."""
    id: str
    full_name: str
    email: str
    user_handle: str
    is_admin: bool
    is_super: bool


class ErrorDetail(msgspec.Struct):
    code: str
    message: str


class ErrorResponse(msgspec.Struct):
    error: ErrorDetail
