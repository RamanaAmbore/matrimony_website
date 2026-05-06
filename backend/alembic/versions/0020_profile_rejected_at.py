"""Add profiles.rejected_at — used by submit_profile to require an actual edit before re-submission.

Revision ID: 0020
Revises: 0019
Create Date: 2026-05-06
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = '0020'
down_revision = '0019'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # G6: track when a profile was last rejected. Owner can only re-submit
    # if updated_at advances past rejected_at — i.e. they actually edited
    # something. Without this column, the submit endpoint allows immediate
    # re-submission of a freshly-rejected profile with the same content.
    op.add_column(
        'profiles',
        sa.Column('rejected_at', sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column('profiles', 'rejected_at')
