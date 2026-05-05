"""Align Postgres enum values with the Python enum .value strings.

Background: the Python enum classes use NAME != VALUE for several members
(DietEnum.non_veg = 'non-veg', BloodGroupEnum.a_pos = 'A+', etc.). For a long
time SQLAlchemy was serializing by NAME, so DBs created via
`Base.metadata.create_all()` ended up with the NAMES as their enum members
('non_veg', 'a_pos'). Production was created via an early migration that
already used the VALUES.

After the values_callable fix on the model columns, all queries serialize
using the VALUES. So any DB where the enum still carries names will reject
inserts with "invalid input value for enum diet_enum: 'non-veg'".

This migration is idempotent: it renames each stale label to the value form,
but only if the stale label actually exists. Production (which already has
the value form) becomes a no-op.

Revision ID: 0018
Revises: 0017
Create Date: 2026-05-05
"""
from __future__ import annotations

from alembic import op


revision = '0018'
down_revision = '0017'
branch_labels = None
depends_on = None


# Each tuple: (enum_type_name, old_label, new_label)
RENAMES = [
    # diet_enum
    ('diet_enum', 'non_veg', 'non-veg'),
    # blood_group_enum
    ('blood_group_enum', 'a_pos', 'A+'),
    ('blood_group_enum', 'a_neg', 'A-'),
    ('blood_group_enum', 'b_pos', 'B+'),
    ('blood_group_enum', 'b_neg', 'B-'),
    ('blood_group_enum', 'ab_pos', 'AB+'),
    ('blood_group_enum', 'ab_neg', 'AB-'),
    ('blood_group_enum', 'o_pos', 'O+'),
    ('blood_group_enum', 'o_neg', 'O-'),
]


def upgrade() -> None:
    for enum_type, old, new in RENAMES:
        # Only rename if the old label exists AND the new label doesn't.
        # This covers all four states: stale-only, mixed, prod-already-correct,
        # and brand-new DB.
        op.execute(
            f"""
            DO $do$
            BEGIN
                IF EXISTS (
                    SELECT 1 FROM pg_enum e
                    JOIN pg_type t ON e.enumtypid = t.oid
                    WHERE t.typname = '{enum_type}' AND e.enumlabel = '{old}'
                ) AND NOT EXISTS (
                    SELECT 1 FROM pg_enum e
                    JOIN pg_type t ON e.enumtypid = t.oid
                    WHERE t.typname = '{enum_type}' AND e.enumlabel = '{new}'
                ) THEN
                    ALTER TYPE {enum_type} RENAME VALUE '{old}' TO '{new}';
                END IF;
            END $do$;
            """
        )


def downgrade() -> None:
    # Reverse: rename values back to names. Same idempotency guard.
    for enum_type, old, new in reversed(RENAMES):
        op.execute(
            f"""
            DO $do$
            BEGIN
                IF EXISTS (
                    SELECT 1 FROM pg_enum e
                    JOIN pg_type t ON e.enumtypid = t.oid
                    WHERE t.typname = '{enum_type}' AND e.enumlabel = '{new}'
                ) AND NOT EXISTS (
                    SELECT 1 FROM pg_enum e
                    JOIN pg_type t ON e.enumtypid = t.oid
                    WHERE t.typname = '{enum_type}' AND e.enumlabel = '{old}'
                ) THEN
                    ALTER TYPE {enum_type} RENAME VALUE '{new}' TO '{old}';
                END IF;
            END $do$;
            """
        )
