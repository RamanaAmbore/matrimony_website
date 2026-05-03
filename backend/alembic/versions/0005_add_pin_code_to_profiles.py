"""add pin_code to profiles

Revision ID: 0005
Revises: 0004
Create Date: 2026-05-03
"""
from alembic import op
import sqlalchemy as sa

revision = '0005'
down_revision = '0004'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('profiles', sa.Column('pin_code', sa.String(10), nullable=True))


def downgrade() -> None:
    op.drop_column('profiles', 'pin_code')
