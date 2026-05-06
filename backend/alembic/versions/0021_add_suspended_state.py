"""Add user-level pause + suspend flags.

Industry conventions split temporary inactivity into two distinct
operational concepts:

  * is_paused     — vacation mode, user-controlled. Profile drops from
                    search, no new profiles, but login still works. The
                    user can flip this on/off themselves.

  * is_suspended  — admin-enforcement hold. Same external effect as
                    is_paused but only an admin (super) can clear it.
                    Used for investigations / TOS holds without the
                    permanence of is_revoked.

Both are independent of is_revoked (full ban — login blocked) and
is_approved (admin OK to create profiles). Profile and request status
enums are intentionally NOT extended; per-entity suspend is rare in
matrimony software and user-level visibility is sufficient.

Revision ID: 0021
Revises: 0020
Create Date: 2026-05-06
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = '0021'
down_revision = '0020'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        'users',
        sa.Column(
            'is_paused',
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )
    op.add_column(
        'users',
        sa.Column(
            'is_suspended',
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )
    op.alter_column('users', 'is_paused', server_default=None)
    op.alter_column('users', 'is_suspended', server_default=None)


def downgrade() -> None:
    op.drop_column('users', 'is_suspended')
    op.drop_column('users', 'is_paused')
