"""Update owner_email setting to admin.marathakalyanam@gmail.com.

Revision ID: 0010
Revises: 0009
Create Date: 2026-05-03 00:00:00.000000
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0010"
down_revision: Union[str, None] = "0009"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        "UPDATE settings SET value = '\"admin.marathakalyanam@gmail.com\"' "
        "WHERE key = 'owner_email'"
    )


def downgrade() -> None:
    op.execute(
        "UPDATE settings SET value = '\"ramanamborespam@gmail.com\"' "
        "WHERE key = 'owner_email'"
    )
