"""Add profile_number to profiles

Revision ID: 0012
Revises: 0011
Create Date: 2026-05-04
"""
from alembic import op
import sqlalchemy as sa

revision = '0012'
down_revision = '0011'
branch_labels = None
depends_on = None


def upgrade():
    # Add nullable first
    op.add_column('profiles', sa.Column('profile_number', sa.String(9), nullable=True))

    # Assign sequential TC-###### to existing profiles (zero-padded row number)
    op.execute("""
        WITH numbered AS (
            SELECT id, ROW_NUMBER() OVER (ORDER BY created_at) AS rn
            FROM profiles
        )
        UPDATE profiles
        SET profile_number = 'TC-' || LPAD(numbered.rn::text, 6, '0')
        FROM numbered
        WHERE profiles.id = numbered.id
    """)

    # Set default for existing null rows (if any were missed), then make not-null
    op.execute("UPDATE profiles SET profile_number = 'TC-000000' WHERE profile_number IS NULL")
    op.alter_column('profiles', 'profile_number', nullable=False)
    op.create_unique_constraint('uq_profiles_profile_number', 'profiles', ['profile_number'])


def downgrade():
    op.drop_constraint('uq_profiles_profile_number', 'profiles', type_='unique')
    op.drop_column('profiles', 'profile_number')
