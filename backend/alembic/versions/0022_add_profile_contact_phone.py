"""Add contact_phone to profiles.

Admin-keyed profiles (admin creating a profile on behalf of someone who
called in) need to capture the candidate / family phone number for that
profile, separate from the User.phone_number on the admin's own
account. Nullable so existing rows and self-service signups don't have
to backfill.

Revision ID: 0022
Revises: 0021
Create Date: 2026-05-07
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = '0022'
down_revision = '0021'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        'profiles',
        sa.Column('contact_phone', sa.String(length=30), nullable=True),
    )


def downgrade() -> None:
    op.drop_column('profiles', 'contact_phone')
