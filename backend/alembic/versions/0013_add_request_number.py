"""Add request_number to detail_requests (RQ- + 9 digits, 12 chars total)

Revision ID: 0013
Revises: 0012
Create Date: 2026-05-04
"""
from alembic import op
import sqlalchemy as sa

revision = '0013'
down_revision = '0012'
branch_labels = None
depends_on = None


def upgrade():
    # Add nullable so we can backfill existing rows.
    op.add_column('detail_requests', sa.Column('request_number', sa.String(12), nullable=True))

    # Backfill: assign sequential RQ-#########  (zero-padded, ordered by created_at)
    op.execute("""
        WITH numbered AS (
            SELECT id, ROW_NUMBER() OVER (ORDER BY created_at) AS rn
            FROM detail_requests
        )
        UPDATE detail_requests
        SET request_number = 'RQ-' || LPAD(numbered.rn::text, 9, '0')
        FROM numbered
        WHERE detail_requests.id = numbered.id
    """)

    # Catch any rows missed (shouldn't be any, but be safe).
    op.execute(
        "UPDATE detail_requests SET request_number = 'RQ-000000000' "
        "WHERE request_number IS NULL"
    )

    # Lock down: NOT NULL + UNIQUE
    op.alter_column('detail_requests', 'request_number', nullable=False)
    op.create_unique_constraint(
        'uq_detail_requests_request_number', 'detail_requests', ['request_number']
    )


def downgrade():
    op.drop_constraint(
        'uq_detail_requests_request_number', 'detail_requests', type_='unique'
    )
    op.drop_column('detail_requests', 'request_number')
