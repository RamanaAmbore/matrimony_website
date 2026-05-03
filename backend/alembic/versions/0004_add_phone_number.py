"""Add phone_number column to users table.

Revision ID: 0004
Revises: 0003
Create Date: 2026-05-02 00:00:00.000000

The User model already declared ``phone_number`` (unique, NOT NULL) but no
migration had ever introduced the column.  This revision adds it.

Backfill strategy:
  * Seed the bootstrap admin (handle 'rambo' or legacy email
    'rambo@marathakalyanam.com') with '+91 9840770711'.
  * For any other existing rows, generate a placeholder of the form
    '+0000000000<n>' so the NOT NULL + UNIQUE constraints can be enforced
    without losing data.  The operator can edit these via /admin later.
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op

revision: str = "0004"
down_revision: Union[str, None] = "0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Add column nullable first so we can backfill safely
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'users' AND column_name = 'phone_number'
            ) THEN
                ALTER TABLE users ADD COLUMN phone_number VARCHAR(32);
            END IF;
        END $$;
        """
    )

    # 2. Backfill bootstrap admin
    op.execute(
        """
        UPDATE users
        SET phone_number = '+91 9840770711'
        WHERE (lower(user_handle) = 'rambo'
               OR email IN ('rambo@marathakalyanam.com',
                            'ramanaamborespam@gmail.com',
                            'ramanamborespam@gmail.com'))
          AND phone_number IS NULL;
        """
    )

    # 3. Backfill remaining rows with unique placeholders
    op.execute(
        """
        DO $$
        DECLARE
            rec RECORD;
            counter INT := 1;
        BEGIN
            FOR rec IN
                SELECT id FROM users WHERE phone_number IS NULL ORDER BY created_at
            LOOP
                UPDATE users
                SET phone_number = '+00' || lpad(counter::TEXT, 12, '0')
                WHERE id = rec.id;
                counter := counter + 1;
            END LOOP;
        END $$;
        """
    )

    # 4. Enforce NOT NULL
    op.execute(
        """
        DO $$
        BEGIN
            BEGIN
                ALTER TABLE users ALTER COLUMN phone_number SET NOT NULL;
            EXCEPTION WHEN others THEN
                NULL;
            END;
        END $$;
        """
    )

    # 5. Unique index
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_indexes
                WHERE tablename = 'users'
                  AND indexname = 'ix_users_phone_number'
            ) THEN
                CREATE UNIQUE INDEX ix_users_phone_number ON users (phone_number);
            END IF;
        END $$;
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_users_phone_number")
    op.drop_column("users", "phone_number")
