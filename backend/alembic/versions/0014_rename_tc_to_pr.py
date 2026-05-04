"""Rename profile_number prefix TC- → PR-

Revision ID: 0014
Revises: 0013
Create Date: 2026-05-04
"""
from alembic import op


revision = '0014'
down_revision = '0013'
branch_labels = None
depends_on = None


def upgrade():
    # Update all existing TC-###### profile_numbers to PR-######.
    # Same length (9 chars), same uniqueness constraint, just a prefix swap.
    op.execute(
        "UPDATE profiles SET profile_number = 'PR-' || SUBSTRING(profile_number FROM 4) "
        "WHERE profile_number LIKE 'TC-%'"
    )


def downgrade():
    op.execute(
        "UPDATE profiles SET profile_number = 'TC-' || SUBSTRING(profile_number FROM 4) "
        "WHERE profile_number LIKE 'PR-%'"
    )
