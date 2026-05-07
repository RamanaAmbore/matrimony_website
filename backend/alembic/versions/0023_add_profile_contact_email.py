"""Add contact_email to profiles.

Mirrors the contact_phone column added in 0022. Each profile carries
its own contact email; the frontend defaults both fields from the
owning User's registration data on a fresh profile but lets the
creator override either value. A single User may own multiple
profiles with identical or distinct contact_email / contact_phone
combinations — uniqueness is not enforced.

Revision ID: 0023
Revises: 0022
Create Date: 2026-05-07
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = '0023'
down_revision = '0022'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        'profiles',
        sa.Column('contact_email', sa.String(length=255), nullable=True),
    )


def downgrade() -> None:
    op.drop_column('profiles', 'contact_email')
