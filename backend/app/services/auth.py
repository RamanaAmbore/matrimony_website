"""Authentication service — password hashing, session helpers."""
from __future__ import annotations

import secrets
import uuid

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

_ph = PasswordHasher(time_cost=2, memory_cost=65536, parallelism=2)


def hash_password(password: str) -> str:
    return _ph.hash(password)


def verify_password(password: str, hash_: str) -> bool:
    try:
        return _ph.verify(hash_, password)
    except VerifyMismatchError:
        return False


def generate_token() -> str:
    """Generate a 32-byte URL-safe token."""
    return secrets.token_urlsafe(32)


def new_uuid() -> uuid.UUID:
    return uuid.uuid4()
