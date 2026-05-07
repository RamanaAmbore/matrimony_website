"""Make profiles.contact_phone + contact_email mandatory.

After 0024 backfilled both columns from the owning User, every row
should already be non-NULL. Defensive re-backfill here in case any
row slipped in between 0023 (column added) and 0024 (backfill) on a
slow rollout — same WHERE-NULL UPDATE re-runs idempotently.

Then both columns flip to NOT NULL. Any NULL row remaining at this
point indicates a User without a phone or email, which is impossible
under our /auth/register schema (both are required at signup); the
NOT NULL constraint will surface the inconsistency rather than mask
it.

Revision ID: 0025
Revises: 0024
Create Date: 2026-05-07
"""
from __future__ import annotations

from alembic import op


revision = '0025'
down_revision = '0024'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Defensive re-backfill — same logic as 0024, idempotent.
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

    op.alter_column('profiles', 'contact_phone', nullable=False)
    op.alter_column('profiles', 'contact_email', nullable=False)


def downgrade() -> None:
    op.alter_column('profiles', 'contact_phone', nullable=True)
    op.alter_column('profiles', 'contact_email', nullable=True)
