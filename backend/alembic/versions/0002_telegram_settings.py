"""Add Telegram notification settings.

Revision ID: 0002
Revises: 0001
Create Date: 2026-05-03 00:00:00.000000

"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        INSERT INTO settings (key, value, updated_at)
        VALUES
            ('matrimony_tg_token',   '""',   now()),
            ('matrimony_tg_chat_id', '""',   now()),
            ('matrimony_tg_enabled', 'true', now())
        ON CONFLICT (key) DO NOTHING
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DELETE FROM settings
        WHERE key IN ('matrimony_tg_token', 'matrimony_tg_chat_id', 'matrimony_tg_enabled')
        """
    )
