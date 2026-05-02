"""Expand profile fields — marital status, family, lifestyle, keywords, etc.

Revision ID: 0002
Revises: 0001
Create Date: 2026-05-02 00:00:00.000000
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# ---------------------------------------------------------------------------
# New enum definitions
# ---------------------------------------------------------------------------
_NEW_ENUMS = [
    (
        "marital_status_enum",
        "CREATE TYPE marital_status_enum AS ENUM ('never_married', 'divorced', 'widowed', 'awaiting_divorce')",
    ),
    (
        "body_type_enum",
        "CREATE TYPE body_type_enum AS ENUM ('slim', 'average', 'athletic', 'heavy')",
    ),
    (
        "blood_group_enum",
        "CREATE TYPE blood_group_enum AS ENUM ('A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-', 'unknown')",
    ),
    (
        "family_type_enum",
        "CREATE TYPE family_type_enum AS ENUM ('nuclear', 'joint')",
    ),
    (
        "family_status_enum",
        "CREATE TYPE family_status_enum AS ENUM ('middle_class', 'upper_middle', 'affluent', 'rich')",
    ),
    (
        "family_values_enum",
        "CREATE TYPE family_values_enum AS ENUM ('orthodox', 'traditional', 'moderate', 'liberal')",
    ),
    (
        "tobacco_alcohol_enum",
        "CREATE TYPE tobacco_alcohol_enum AS ENUM ('no', 'occasionally', 'yes')",
    ),
]


def upgrade() -> None:
    # ------------------------------------------------------------------
    # 1. Create new enum types (idempotent via DO $$ ... EXCEPTION block)
    # ------------------------------------------------------------------
    for _name, ddl in _NEW_ENUMS:
        op.execute(f"DO $$ BEGIN {ddl}; EXCEPTION WHEN duplicate_object THEN null; END $$;")

    # ------------------------------------------------------------------
    # 2. Extend diet_enum with jain and vegan (idempotent)
    # ------------------------------------------------------------------
    op.execute("ALTER TYPE diet_enum ADD VALUE IF NOT EXISTS 'jain'")
    op.execute("ALTER TYPE diet_enum ADD VALUE IF NOT EXISTS 'vegan'")

    # ------------------------------------------------------------------
    # 3. Add new columns to profiles
    # ------------------------------------------------------------------
    op.add_column(
        "profiles",
        sa.Column(
            "marital_status",
            postgresql.ENUM(
                "never_married", "divorced", "widowed", "awaiting_divorce",
                name="marital_status_enum", create_type=False,
            ),
            nullable=False,
            server_default="never_married",
        ),
    )
    op.add_column("profiles", sa.Column("sub_caste", sa.String(100), nullable=True))
    op.add_column("profiles", sa.Column("weight_kg", sa.Integer(), nullable=True))
    op.add_column(
        "profiles",
        sa.Column(
            "body_type",
            postgresql.ENUM("slim", "average", "athletic", "heavy", name="body_type_enum", create_type=False),
            nullable=True,
        ),
    )
    op.add_column(
        "profiles",
        sa.Column(
            "blood_group",
            postgresql.ENUM("A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-", "unknown",
                            name="blood_group_enum", create_type=False),
            nullable=True,
        ),
    )
    op.add_column("profiles", sa.Column("time_of_birth", sa.Time(), nullable=True))
    op.add_column("profiles", sa.Column("place_of_birth", sa.String(150), nullable=True))
    op.add_column("profiles", sa.Column("father_occupation", sa.String(150), nullable=True))
    op.add_column("profiles", sa.Column("mother_occupation", sa.String(150), nullable=True))
    op.add_column("profiles", sa.Column("num_brothers", sa.Integer(), nullable=True))
    op.add_column("profiles", sa.Column("num_sisters", sa.Integer(), nullable=True))
    op.add_column("profiles", sa.Column("num_brothers_married", sa.Integer(), nullable=True))
    op.add_column("profiles", sa.Column("num_sisters_married", sa.Integer(), nullable=True))
    op.add_column(
        "profiles",
        sa.Column(
            "family_type",
            postgresql.ENUM("nuclear", "joint", name="family_type_enum", create_type=False),
            nullable=True,
        ),
    )
    op.add_column(
        "profiles",
        sa.Column(
            "family_status",
            postgresql.ENUM("middle_class", "upper_middle", "affluent", "rich",
                            name="family_status_enum", create_type=False),
            nullable=True,
        ),
    )
    op.add_column(
        "profiles",
        sa.Column(
            "family_values",
            postgresql.ENUM("orthodox", "traditional", "moderate", "liberal",
                            name="family_values_enum", create_type=False),
            nullable=True,
        ),
    )
    op.add_column("profiles", sa.Column("native_place", sa.String(150), nullable=True))
    op.add_column("profiles", sa.Column("college_university", sa.String(200), nullable=True))
    op.add_column("profiles", sa.Column("employer", sa.String(200), nullable=True))
    op.add_column("profiles", sa.Column("work_location", sa.String(150), nullable=True))
    op.add_column(
        "profiles",
        sa.Column(
            "smokes",
            postgresql.ENUM("no", "occasionally", "yes", name="tobacco_alcohol_enum", create_type=False),
            nullable=True,
        ),
    )
    op.add_column(
        "profiles",
        sa.Column(
            "drinks",
            postgresql.ENUM("no", "occasionally", "yes", name="tobacco_alcohol_enum", create_type=False),
            nullable=True,
        ),
    )
    op.add_column("profiles", sa.Column("hobbies", sa.Text(), nullable=True))
    op.add_column(
        "profiles",
        sa.Column("partner_preference_keywords", postgresql.JSON(astext_type=sa.Text()), nullable=True),
    )

    # ------------------------------------------------------------------
    # 4. Backfill partner_preference_keywords from partner_expectations
    #    Pure SQL: tokenise and filter right in the database using a
    #    simple regexp_split_to_array approach.  The Python extractor is
    #    the authoritative implementation; this backfill uses an
    #    equivalent SQL approximation (lowercase, split on non-word chars,
    #    drop tokens < 3 chars).  Stopword filtering is omitted in SQL
    #    for simplicity — a subsequent re-index via the Python service can
    #    be run if needed.
    # ------------------------------------------------------------------
    op.execute(
        """
        UPDATE profiles
        SET partner_preference_keywords = (
            SELECT to_json(array_agg(DISTINCT tok ORDER BY tok))
            FROM (
                SELECT tok
                FROM unnest(
                    regexp_split_to_array(lower(partner_expectations), '[^a-z]+')
                ) AS tok
                WHERE length(tok) >= 3
                LIMIT 50
            ) sub
        )
        WHERE partner_expectations IS NOT NULL
          AND partner_expectations <> ''
        """
    )


def downgrade() -> None:
    # Drop new columns
    op.drop_column("profiles", "partner_preference_keywords")
    op.drop_column("profiles", "hobbies")
    op.drop_column("profiles", "drinks")
    op.drop_column("profiles", "smokes")
    op.drop_column("profiles", "work_location")
    op.drop_column("profiles", "employer")
    op.drop_column("profiles", "college_university")
    op.drop_column("profiles", "native_place")
    op.drop_column("profiles", "family_values")
    op.drop_column("profiles", "family_status")
    op.drop_column("profiles", "family_type")
    op.drop_column("profiles", "num_sisters_married")
    op.drop_column("profiles", "num_brothers_married")
    op.drop_column("profiles", "num_sisters")
    op.drop_column("profiles", "num_brothers")
    op.drop_column("profiles", "mother_occupation")
    op.drop_column("profiles", "father_occupation")
    op.drop_column("profiles", "place_of_birth")
    op.drop_column("profiles", "time_of_birth")
    op.drop_column("profiles", "blood_group")
    op.drop_column("profiles", "body_type")
    op.drop_column("profiles", "weight_kg")
    op.drop_column("profiles", "sub_caste")
    op.drop_column("profiles", "marital_status")

    # Drop new enum types
    op.execute("DROP TYPE IF EXISTS tobacco_alcohol_enum")
    op.execute("DROP TYPE IF EXISTS family_values_enum")
    op.execute("DROP TYPE IF EXISTS family_status_enum")
    op.execute("DROP TYPE IF EXISTS family_type_enum")
    op.execute("DROP TYPE IF EXISTS blood_group_enum")
    op.execute("DROP TYPE IF EXISTS body_type_enum")
    op.execute("DROP TYPE IF EXISTS marital_status_enum")

    # NOTE: We do NOT remove 'jain' / 'vegan' from diet_enum.
    # PostgreSQL does not support removing enum values without a table rewrite.
    # The downgrade leaves diet_enum with the extra values in place — this is safe.
