"""Make optional profile fields nullable for draft wizard support.

Revision ID: 0007_nullable_profile_fields
Revises: 0006_add_family_name_fields
Create Date: 2026-05-03

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "0007_nullable_profile_fields"
down_revision = "0006_add_family_name_fields"
branch_labels = None
depends_on = None

# Columns to make nullable. Each entry is (column_name, column_type_sql).
# column_type_sql is only needed for down() to restore NOT NULL with a default.
_NULLABLE_COLUMNS = [
    "complexion",
    "education",
    "occupation",
    "city",
    "state",
    "gotra",
    "kuldevata",
    "devak",
    "surname_clan",
    "nakshatram",
    "rashi",
    "last_name",
    "diet",
    "height_cm",
]


def upgrade() -> None:
    for col in _NULLABLE_COLUMNS:
        op.execute(f"ALTER TABLE profiles ALTER COLUMN {col} DROP NOT NULL")


def downgrade() -> None:
    # Restore NOT NULL. Rows that have NULL in these columns will be set to a
    # placeholder value first so the constraint can be re-applied cleanly.
    placeholders: dict[str, str] = {
        "complexion":   "UPDATE profiles SET complexion = '' WHERE complexion IS NULL",
        "education":    "UPDATE profiles SET education = '' WHERE education IS NULL",
        "occupation":   "UPDATE profiles SET occupation = '' WHERE occupation IS NULL",
        "city":         "UPDATE profiles SET city = '' WHERE city IS NULL",
        "state":        "UPDATE profiles SET state = '' WHERE state IS NULL",
        "gotra":        "UPDATE profiles SET gotra = '' WHERE gotra IS NULL",
        "kuldevata":    "UPDATE profiles SET kuldevata = '' WHERE kuldevata IS NULL",
        "devak":        "UPDATE profiles SET devak = '' WHERE devak IS NULL",
        "surname_clan": "UPDATE profiles SET surname_clan = '' WHERE surname_clan IS NULL",
        "nakshatram":   "UPDATE profiles SET nakshatram = '' WHERE nakshatram IS NULL",
        "rashi":        "UPDATE profiles SET rashi = '' WHERE rashi IS NULL",
        "last_name":    "UPDATE profiles SET last_name = '' WHERE last_name IS NULL",
        "diet":         "UPDATE profiles SET diet = 'veg' WHERE diet IS NULL",
        "height_cm":    "UPDATE profiles SET height_cm = 0 WHERE height_cm IS NULL",
    }
    for col in _NULLABLE_COLUMNS:
        if col in placeholders:
            op.execute(placeholders[col])
        op.execute(f"ALTER TABLE profiles ALTER COLUMN {col} SET NOT NULL")
