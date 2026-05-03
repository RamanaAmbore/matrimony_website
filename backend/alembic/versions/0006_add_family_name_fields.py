"""add father_name, mother_name, num_family_members to profiles

Revision ID: 0006
Revises: 0005
Create Date: 2026-05-03
"""
import sqlalchemy as sa
from alembic import op

revision = '0006'
down_revision = '0005'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('profiles', sa.Column('father_name', sa.String(100), nullable=True))
    op.add_column('profiles', sa.Column('mother_name', sa.String(100), nullable=True))
    op.add_column('profiles', sa.Column('num_family_members', sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column('profiles', 'num_family_members')
    op.drop_column('profiles', 'mother_name')
    op.drop_column('profiles', 'father_name')
