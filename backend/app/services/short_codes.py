"""Short-code ID generation for public-facing identifiers.

Generates 6-character alphanumeric uppercase codes (A–Z + 0–9, 36^6 ≈ 2.2 billion
values) with a family prefix:

    MK-XXXXXX  — User handles
    PR-XXXXXX  — Profile numbers
    RQ-XXXXXX  — Request numbers

Uses ``secrets.choice`` for cryptographic-quality randomness and retries up to
*attempts* times on a DB collision before raising RuntimeError.
"""
from __future__ import annotations

import secrets
from typing import TYPE_CHECKING, Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.attributes import InstrumentedAttribute

_ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"


def generate_short_code(prefix: str) -> str:
    """Return a new random ``PREFIX-XXXXXX`` code (not guaranteed unique)."""
    return f"{prefix}-" + "".join(secrets.choice(_ALPHABET) for _ in range(6))


async def generate_unique_code(
    db: AsyncSession,
    model: Any,
    column: InstrumentedAttribute,  # type: ignore[type-arg]
    prefix: str,
    attempts: int = 10,
) -> str:
    """Generate a ``PREFIX-XXXXXX`` code that does not already exist in the DB.

    Args:
        db:       Active async SQLAlchemy session.
        model:    The ORM model class (e.g. ``Profile``).
        column:   The mapped column attribute to check (e.g. ``Profile.profile_number``).
        prefix:   Code family prefix, e.g. ``"PR"``, ``"MK"``, ``"RQ"``.
        attempts: Maximum number of retries on collision before raising.

    Returns:
        A unique short code string.

    Raises:
        RuntimeError: if *attempts* collisions occur in a row.
    """
    for _ in range(attempts):
        candidate = generate_short_code(prefix)
        result = await db.execute(select(model).where(column == candidate))
        if result.scalar_one_or_none() is None:
            return candidate
    raise RuntimeError(
        f"Could not generate unique {prefix}-XXXXXX code after {attempts} attempts"
    )
