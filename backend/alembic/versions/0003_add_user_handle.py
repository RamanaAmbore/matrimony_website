"""Add user_handle column to users table.

Revision ID: 0003
Revises: 0002
Create Date: 2026-05-02 00:00:00.000000

Backfill strategy for existing rows:
  The only expected existing user on the live server is the bootstrap admin
  (rambo@marathakalyanam.com).  The migration hard-codes handle='rambo' for
  that row, then falls back to lower(split_part(email, '@', 1)) for any other
  rows, deduplicating with _2, _3, … suffixes if collisions arise.
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ------------------------------------------------------------------
    # 1. Add user_handle column — nullable first so we can backfill safely
    # ------------------------------------------------------------------
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'users' AND column_name = 'user_handle'
            ) THEN
                ALTER TABLE users ADD COLUMN user_handle VARCHAR(40);
            END IF;
        END $$;
        """
    )

    # ------------------------------------------------------------------
    # 2. Backfill: hard-code 'rambo' for the bootstrap admin, then derive
    #    handles from email local-part for all other rows.
    # ------------------------------------------------------------------
    # Hard-code for the known bootstrap admin
    op.execute(
        """
        UPDATE users
        SET user_handle = 'rambo'
        WHERE email = 'rambo@marathakalyanam.com'
          AND user_handle IS NULL;
        """
    )

    # For all remaining rows without a handle, derive from email local-part
    # and deduplicate by appending _2, _3, … if needed.
    op.execute(
        """
        DO $$
        DECLARE
            rec RECORD;
            base_handle TEXT;
            candidate TEXT;
            suffix INT;
        BEGIN
            FOR rec IN
                SELECT id, email
                FROM users
                WHERE user_handle IS NULL
                ORDER BY created_at
            LOOP
                -- Take the part before '@', lowercase, replace non-alphanum/underscore with '_'
                base_handle := regexp_replace(
                    lower(split_part(rec.email, '@', 1)),
                    '[^a-z0-9_]', '_', 'g'
                );
                -- Ensure it starts with a letter; prefix 'u_' if not
                IF base_handle !~ '^[a-z]' THEN
                    base_handle := 'u_' || base_handle;
                END IF;
                -- Truncate to 30 chars
                base_handle := left(base_handle, 30);
                -- Ensure minimum length of 3
                WHILE length(base_handle) < 3 LOOP
                    base_handle := base_handle || '_';
                END LOOP;

                candidate := base_handle;
                suffix := 2;
                -- Find a unique lower-cased handle
                WHILE EXISTS (
                    SELECT 1 FROM users WHERE lower(user_handle) = lower(candidate)
                ) LOOP
                    candidate := left(base_handle, 27) || '_' || suffix::TEXT;
                    suffix := suffix + 1;
                END LOOP;

                UPDATE users SET user_handle = candidate WHERE id = rec.id;
            END LOOP;
        END $$;
        """
    )

    # ------------------------------------------------------------------
    # 3. Now enforce NOT NULL
    # ------------------------------------------------------------------
    op.execute(
        """
        DO $$
        BEGIN
            BEGIN
                ALTER TABLE users ALTER COLUMN user_handle SET NOT NULL;
            EXCEPTION WHEN others THEN
                -- Already NOT NULL — skip
                NULL;
            END;
        END $$;
        """
    )

    # ------------------------------------------------------------------
    # 4. Create the case-insensitive unique index (idempotent)
    # ------------------------------------------------------------------
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_indexes
                WHERE tablename = 'users'
                  AND indexname = 'ix_users_user_handle_lower'
            ) THEN
                CREATE UNIQUE INDEX ix_users_user_handle_lower
                    ON users (lower(user_handle));
            END IF;
        END $$;
        """
    )

    # ------------------------------------------------------------------
    # 5. Create a plain btree index on user_handle for general lookups
    #    (idempotent)
    # ------------------------------------------------------------------
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_indexes
                WHERE tablename = 'users'
                  AND indexname = 'ix_users_user_handle'
            ) THEN
                CREATE INDEX ix_users_user_handle ON users (user_handle);
            END IF;
        END $$;
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_users_user_handle_lower")
    op.execute("DROP INDEX IF EXISTS ix_users_user_handle")
    op.drop_column("users", "user_handle")
