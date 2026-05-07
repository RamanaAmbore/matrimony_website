"""Backfill profile contact fields from owning User.

Profiles created before 0022 / 0023 have NULL contact_phone and
contact_email. New profiles seed both from the owner's registration
data on the frontend, but legacy rows still need to be filled in.

Strategy: one UPDATE per column, scoped to NULLs only, sourced from
the joined User row. Idempotent — re-running only touches rows that
are still NULL, and once filled in they stay filled in.

Downgrade is intentionally a no-op: we don't have a way to tell which
rows were originally NULL and which were authored, so reverting would
risk wiping legitimately-entered values.

Revision ID: 0024
Revises: 0023
Create Date: 2026-05-07
"""
from __future__ import annotations

from alembic import op


revision = '0024'
down_revision = '0023'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Postgres-specific UPDATE … FROM. Trim whitespace before assigning
    # so a stray trailing newline on a User row doesn't propagate.
    op.execute(
        """
        UPDATE profiles
           SET contact_phone = TRIM(u.phone_number)
          FROM users u
         WHERE profiles.owner_user_id = u.id
           AND profiles.contact_phone IS NULL
           AND u.phone_number IS NOT NULL
           AND TRIM(u.phone_number) <> ''
        """
    )
    op.execute(
        """
        UPDATE profiles
           SET contact_email = TRIM(u.email)
          FROM users u
         WHERE profiles.owner_user_id = u.id
           AND profiles.contact_email IS NULL
           AND u.email IS NOT NULL
           AND TRIM(u.email) <> ''
        """
    )


def downgrade() -> None:
    # Intentional no-op — see module docstring.
    pass
