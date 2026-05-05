"""Auth schemas."""
from __future__ import annotations

import uuid

import msgspec


class RegisterRequest(msgspec.Struct):
    email: str
    password: str
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


class ErrorDetail(msgspec.Struct):
    code: str
    message: str


class ErrorResponse(msgspec.Struct):
    error: ErrorDetail
