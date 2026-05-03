"""Auth schemas."""
from __future__ import annotations

import uuid

import msgspec


class RegisterRequest(msgspec.Struct):
    email: str
    password: str
    user_handle: str
    phone_number: str


class LoginRequest(msgspec.Struct):
    identifier: str  # email address OR user_handle
    password: str


class VerifyEmailRequest(msgspec.Struct):
    token: str


class UserResponse(msgspec.Struct):
    user_id: str
    user_handle: str
    email: str
    is_admin: bool
    email_verified: bool


class RegisterResponse(msgspec.Struct):
    user_id: str


class ErrorDetail(msgspec.Struct):
    code: str
    message: str


class ErrorResponse(msgspec.Struct):
    error: ErrorDetail
