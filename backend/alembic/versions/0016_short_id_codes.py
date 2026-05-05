"""Backfill short-code IDs for users, profiles, and detail_requests.

All three tables gain MK-/PR-/RQ-XXXXXX codes (6-char alphanumeric uppercase)
for rows that still carry the old numeric or human-typed handles.

Revision ID: 0016
Revises: 0015
Create Date: 2026-05-05
"""
from __future__ import annotations

import secrets

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text

revision = '0016'
down_revision = '0015'
branch_labels = None
depends_on = None

_ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"


def _rand_code(prefix: str) -> str:
    suffix = "".join(secrets.choice(_ALPHABET) for _ in range(6))
    return f"{prefix}-{suffix}"


def _backfill(conn, table: str, column: str, prefix: str) -> None:
    """Assign a unique PREFIX-XXXXXX value to every row in *table*.*column*
    that does not already start with the correct prefix.

    Strategy:
    1. Load the set of values that already look like valid short codes for this
       prefix (so we never duplicate them).
    2. For each row that still carries an old value, generate candidates until
       one is not in the taken set, then UPDATE.
    """
    # Fetch IDs and current column values for rows that need backfilling.
    rows = conn.execute(
        text(f"SELECT id, {column} FROM {table} WHERE {column} NOT LIKE :pattern"),
        {"pattern": f"{prefix}-%"},
    ).fetchall()

    if not rows:
        return

    # Build the set of already-assigned short codes so we avoid duplicates.
    taken_rows = conn.execute(
        text(f"SELECT {column} FROM {table} WHERE {column} LIKE :pattern"),
        {"pattern": f"{prefix}-%"},
    ).fetchall()
    taken: set[str] = {r[0] for r in taken_rows}

    for row_id, _old_val in rows:
        for _ in range(50):  # generous retry budget
            candidate = _rand_code(prefix)
            if candidate not in taken:
                taken.add(candidate)
                break
        else:
            raise RuntimeError(
                f"Could not generate unique {prefix}-XXXXXX after 50 attempts"
            )

        conn.execute(
            text(f"UPDATE {table} SET {column} = :code WHERE id = :id"),
            {"code": candidate, "id": row_id},
        )


def upgrade():
    conn = op.get_bind()
    _backfill(conn, "users", "user_handle", "MK")
    _backfill(conn, "profiles", "profile_number", "PR")
    _backfill(conn, "detail_requests", "request_number", "RQ")


def downgrade():
    # Intentional no-op: random codes cannot be deterministically reversed.
    pass
