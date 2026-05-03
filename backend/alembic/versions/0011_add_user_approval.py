"""Add is_approved to users table, is_prod setting, and relax email/phone uniqueness.

Revision ID: 0011
Revises: 0010
Create Date: 2026-05-03 00:00:00.000000
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0011"
down_revision: Union[str, None] = "0010"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Add is_approved column — default false, backfill verified users as approved
    op.add_column(
        "users",
        sa.Column("is_approved", sa.Boolean(), nullable=False, server_default="false"),
    )
    op.execute("UPDATE users SET is_approved = TRUE WHERE email_verified = TRUE")

    # 2. Drop unique constraints/indexes on email and phone.
    # Use raw SQL with IF EXISTS to handle different environments where constraint
    # names may vary (named constraint vs unique index only).
    op.execute("ALTER TABLE users DROP CONSTRAINT IF EXISTS users_email_key")
    op.execute("ALTER TABLE users DROP CONSTRAINT IF EXISTS users_phone_number_key")
    op.execute("DROP INDEX IF EXISTS ix_users_phone_number")
    # ix_users_email may already be non-unique — only drop if it's a unique index
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM pg_indexes
                WHERE tablename = 'users'
                  AND indexname = 'ix_users_email'
                  AND indexdef LIKE '%UNIQUE%'
            ) THEN
                DROP INDEX ix_users_email;
            END IF;
        END$$
    """)

    # Re-create as non-unique indexes for query performance (skip if already exist)
    op.execute("CREATE INDEX IF NOT EXISTS ix_users_email ON users (email)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_users_phone_number ON users (phone_number)")

    # 3. Seed is_prod setting (false by default — uniqueness checks disabled in dev)
    op.execute(
        """
        INSERT INTO settings (key, value, updated_at)
        VALUES ('is_prod', 'false', now())
        ON CONFLICT (key) DO NOTHING
        """
    )


def downgrade() -> None:
    # Remove is_prod setting
    op.execute("DELETE FROM settings WHERE key = 'is_prod'")

    # Restore unique indexes on email and phone
    op.drop_index("ix_users_email", table_name="users")
    op.drop_index("ix_users_phone_number", table_name="users")
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.create_index("ix_users_phone_number", "users", ["phone_number"], unique=True)
    op.create_unique_constraint("users_email_key", "users", ["email"])
    op.create_unique_constraint("users_phone_number_key", "users", ["phone_number"])

    # Drop is_approved column
    op.drop_column("users", "is_approved")
