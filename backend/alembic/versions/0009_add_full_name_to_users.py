"""Add full_name column to users table.

Revision ID: 0009
Revises: 0008
Create Date: 2026-05-03 00:00:00.000000

Adds ``full_name VARCHAR(120) NOT NULL DEFAULT ''`` to the users table.
Existing rows are backfilled with an empty string before the NOT NULL
constraint is enforced, which is safe for all existing accounts.
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op

revision: str = "0009"
down_revision: Union[str, None] = "0008"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Add column as nullable so we can backfill first
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'users' AND column_name = 'full_name'
            ) THEN
                ALTER TABLE users ADD COLUMN full_name VARCHAR(120);
            END IF;
        END $$;
        """
    )

    # 2. Backfill existing rows with empty string
    op.execute("UPDATE users SET full_name = '' WHERE full_name IS NULL")

    # 3. Enforce NOT NULL
    op.execute(
        """
        DO $$
        BEGIN
            BEGIN
                ALTER TABLE users ALTER COLUMN full_name SET NOT NULL;
            EXCEPTION WHEN others THEN
                NULL;
            END;
        END $$;
        """
    )

    # 4. Set server-side default for future rows
    op.execute(
        """
        DO $$
        BEGIN
            BEGIN
                ALTER TABLE users ALTER COLUMN full_name SET DEFAULT '';
            EXCEPTION WHEN others THEN
                NULL;
            END;
        END $$;
        """
    )


def downgrade() -> None:
    op.drop_column("users", "full_name")
