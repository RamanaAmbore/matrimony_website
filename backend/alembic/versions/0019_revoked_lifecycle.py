"""Soft-revoke lifecycle: rename rejected→revoked in enums; add is_revoked to users.

Revision ID: 0019
Revises: 0018
Create Date: 2026-05-05
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = '0019'
down_revision = '0018'
branch_labels = None
depends_on = None


# Enum renames: (type_name, old_label, new_label)
_ENUM_RENAMES = [
    ('profile_status_enum', 'rejected', 'revoked'),
    ('request_status_enum', 'rejected', 'revoked'),
]


def upgrade() -> None:
    # 1. Rename enum values idempotently (same pattern as 0018).
    for enum_type, old, new in _ENUM_RENAMES:
        op.execute(
            f"""
            DO $do$
            BEGIN
                IF EXISTS (
                    SELECT 1 FROM pg_enum e
                    JOIN pg_type t ON e.enumtypid = t.oid
                    WHERE t.typname = '{enum_type}' AND e.enumlabel = '{old}'
                ) AND NOT EXISTS (
                    SELECT 1 FROM pg_enum e
                    JOIN pg_type t ON e.enumtypid = t.oid
                    WHERE t.typname = '{enum_type}' AND e.enumlabel = '{new}'
                ) THEN
                    ALTER TYPE {enum_type} RENAME VALUE '{old}' TO '{new}';
                END IF;
            END $do$;
            """
        )

    # 2. Add is_revoked boolean to users (idempotent via IF NOT EXISTS).
    op.execute(
        """
        DO $do$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'users' AND column_name = 'is_revoked'
            ) THEN
                ALTER TABLE users ADD COLUMN is_revoked BOOLEAN NOT NULL DEFAULT false;
            END IF;
        END $do$;
        """
    )


def downgrade() -> None:
    # Intentional no-op: reversing enum renames on live data is risky and
    # rarely needed. Drop is_revoked manually if truly required.
    pass
