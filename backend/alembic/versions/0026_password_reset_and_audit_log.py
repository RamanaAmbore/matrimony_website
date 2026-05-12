"""Add password reset columns to users, create audit_log table, seed setting.

Changes:
  1. Add three columns to `users`:
       - password_reset_token     VARCHAR(64) nullable, indexed
       - password_reset_expires_at TIMESTAMPTZ nullable
       - must_change_password      BOOLEAN NOT NULL DEFAULT false

  2. Create `audit_log` table with actor/target FK to users.

  3. Seed setting `password_reset_ttl_hours = 1`.

Revision ID: 0026
Revises: 0025
Create Date: 2026-05-11
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID


revision = '0026'
down_revision = '0025'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── 1. users: password reset columns ───────────────────────────────────
    op.add_column(
        'users',
        sa.Column(
            'password_reset_token',
            sa.String(64),
            nullable=True,
        ),
    )
    op.create_index(
        'ix_users_password_reset_token',
        'users',
        ['password_reset_token'],
    )
    op.add_column(
        'users',
        sa.Column(
            'password_reset_expires_at',
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )
    op.add_column(
        'users',
        sa.Column(
            'must_change_password',
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )
    # Remove server_default after backfill so future rows don't inherit it
    op.alter_column('users', 'must_change_password', server_default=None)

    # ── 2. audit_log table ──────────────────────────────────────────────────
    op.create_table(
        'audit_log',
        sa.Column(
            'id',
            UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        sa.Column(
            'actor_user_id',
            UUID(as_uuid=True),
            sa.ForeignKey('users.id', ondelete='CASCADE'),
            nullable=False,
        ),
        sa.Column(
            'target_user_id',
            UUID(as_uuid=True),
            sa.ForeignKey('users.id', ondelete='SET NULL'),
            nullable=True,
        ),
        sa.Column(
            'action',
            sa.String(50),
            nullable=False,
        ),
        sa.Column(
            'audit_metadata',
            JSONB,
            nullable=True,
        ),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index('ix_audit_log_actor_user_id', 'audit_log', ['actor_user_id'])
    op.create_index('ix_audit_log_target_user_id', 'audit_log', ['target_user_id'])
    op.create_index('ix_audit_log_action', 'audit_log', ['action'])
    op.create_index('ix_audit_log_created_at', 'audit_log', ['created_at'])

    # ── 3. seed new setting ─────────────────────────────────────────────────
    op.execute(
        """
        INSERT INTO settings (key, value, updated_at)
        VALUES ('password_reset_ttl_hours', '1', now())
        ON CONFLICT (key) DO NOTHING
        """
    )


def downgrade() -> None:
    # Remove setting
    op.execute("DELETE FROM settings WHERE key = 'password_reset_ttl_hours'")

    # Drop audit_log
    op.drop_index('ix_audit_log_created_at', table_name='audit_log')
    op.drop_index('ix_audit_log_action', table_name='audit_log')
    op.drop_index('ix_audit_log_target_user_id', table_name='audit_log')
    op.drop_index('ix_audit_log_actor_user_id', table_name='audit_log')
    op.drop_table('audit_log')

    # Drop user columns
    op.drop_column('users', 'must_change_password')
    op.drop_column('users', 'password_reset_expires_at')
    op.drop_index('ix_users_password_reset_token', table_name='users')
    op.drop_column('users', 'password_reset_token')
