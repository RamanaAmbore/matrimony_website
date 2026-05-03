"""Initial schema with all tables and settings seed.

Revision ID: 0001
Revises:
Create Date: 2026-05-02 00:00:00.000000

"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create enums
    gender_enum = postgresql.ENUM("bride", "groom", name="gender_enum", create_type=False)
    manglik_enum = postgresql.ENUM("yes", "no", "partial", "unknown", name="manglik_enum", create_type=False)
    diet_enum = postgresql.ENUM("veg", "non-veg", "eggetarian", name="diet_enum", create_type=False)
    profile_status_enum = postgresql.ENUM("draft", "pending", "approved", "rejected", name="profile_status_enum", create_type=False)
    request_status_enum = postgresql.ENUM("pending", "approved", "rejected", name="request_status_enum", create_type=False)

    # Postgres has no CREATE TYPE IF NOT EXISTS, so wrap each in a DO block
    # that swallows the duplicate_object exception. Keeps the migration safe
    # to re-run after a partial failure.
    for ddl in (
        "CREATE TYPE gender_enum AS ENUM ('bride', 'groom')",
        "CREATE TYPE manglik_enum AS ENUM ('yes', 'no', 'partial', 'unknown')",
        "CREATE TYPE diet_enum AS ENUM ('veg', 'non-veg', 'eggetarian')",
        "CREATE TYPE profile_status_enum AS ENUM ('draft', 'pending', 'approved', 'rejected')",
        "CREATE TYPE request_status_enum AS ENUM ('pending', 'approved', 'rejected')",
    ):
        op.execute(f"DO $$ BEGIN {ddl}; EXCEPTION WHEN duplicate_object THEN null; END $$;")

    # users table
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("password_hash", sa.String(512), nullable=False),
        sa.Column("email_verified", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("email_verification_token", sa.String(64), nullable=True),
        sa.Column("is_admin", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )
    op.create_index("ix_users_email", "users", ["email"])

    # settings table
    op.create_table(
        "settings",
        sa.Column("key", sa.String(100), nullable=False),
        sa.Column("value", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(["updated_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("key"),
    )

    # profiles table
    op.create_table(
        "profiles",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("owner_user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("gender", postgresql.ENUM("bride", "groom", name="gender_enum", create_type=False), nullable=False),
        sa.Column("first_name", sa.String(100), nullable=False),
        sa.Column("last_name", sa.String(100), nullable=False),
        sa.Column("dob", sa.Date(), nullable=False),
        sa.Column("height_cm", sa.Integer(), nullable=False),
        sa.Column("complexion", sa.String(50), nullable=False),
        sa.Column("education", sa.String(200), nullable=False),
        sa.Column("occupation", sa.String(200), nullable=False),
        sa.Column("annual_income_inr", sa.BigInteger(), nullable=True),
        sa.Column("city", sa.String(100), nullable=False),
        sa.Column("state", sa.String(100), nullable=False),
        sa.Column("country", sa.String(100), nullable=False, server_default="India"),
        sa.Column("gotra", sa.String(100), nullable=False),
        sa.Column("kuldevata", sa.String(100), nullable=False),
        sa.Column("devak", sa.String(100), nullable=False),
        sa.Column("surname_clan", sa.String(100), nullable=False),
        sa.Column("nakshatram", sa.String(100), nullable=False),
        sa.Column("rashi", sa.String(100), nullable=False),
        sa.Column("manglik", postgresql.ENUM("yes", "no", "partial", "unknown", name="manglik_enum", create_type=False), nullable=False, server_default="unknown"),
        sa.Column("mother_tongue", sa.String(50), nullable=False, server_default="Telugu"),
        sa.Column("diet", postgresql.ENUM("veg", "non-veg", "eggetarian", name="diet_enum", create_type=False), nullable=False),
        sa.Column("about", sa.Text(), nullable=False, server_default=""),
        sa.Column("partner_expectations", sa.Text(), nullable=False, server_default=""),
        sa.Column("status", postgresql.ENUM("draft", "pending", "approved", "rejected", name="profile_status_enum", create_type=False), nullable=False, server_default="draft"),
        sa.Column("admin_notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["owner_user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_profiles_owner_user_id", "profiles", ["owner_user_id"])

    # photos table
    op.create_table(
        "photos",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("profile_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("original_filename", sa.String(255), nullable=False),
        sa.Column("passport_path", sa.String(500), nullable=False),
        sa.Column("blurred_path", sa.String(500), nullable=False),
        sa.Column("thumb_path", sa.String(500), nullable=False),
        sa.Column("byte_size", sa.Integer(), nullable=False),
        sa.Column("is_primary", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["profile_id"], ["profiles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_photos_profile_id", "photos", ["profile_id"])

    # detail_requests table
    op.create_table(
        "detail_requests",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("requester_user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("profile_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("status", postgresql.ENUM("pending", "approved", "rejected", name="request_status_enum", create_type=False), nullable=False, server_default="pending"),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column("admin_notes", sa.Text(), nullable=True),
        sa.Column("responded_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["profile_id"], ["profiles.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["requester_user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("requester_user_id", "profile_id", name="uq_request_user_profile"),
    )
    op.create_index("ix_detail_requests_requester_user_id", "detail_requests", ["requester_user_id"])
    op.create_index("ix_detail_requests_profile_id", "detail_requests", ["profile_id"])

    # Seed default settings
    op.execute("""
        INSERT INTO settings (key, value, updated_at) VALUES
        ('owner_email', '"admin.marathakalyanam@gmail.com"', NOW()),
        ('smtp_host', '"localhost"', NOW()),
        ('smtp_port', '1025', NOW()),
        ('smtp_user', '""', NOW()),
        ('smtp_password', '""', NOW()),
        ('smtp_from', '"no-reply@marathakalyanam.com"', NOW()),
        ('photo_max_kb', '500', NOW()),
        ('photo_passport_width', '413', NOW()),
        ('photo_passport_height', '531', NOW()),
        ('photo_blur_width', '600', NOW()),
        ('photo_blur_radius', '14', NOW()),
        ('photo_thumb_size', '150', NOW()),
        ('photos_max_per_profile', '5', NOW()),
        ('upload_max_mb', '10', NOW()),
        ('require_face_detection', 'true', NOW()),
        ('require_admin_approval_for_profiles', 'true', NOW())
    """)


def downgrade() -> None:
    op.drop_table("detail_requests")
    op.drop_table("photos")
    op.drop_table("profiles")
    op.drop_table("settings")
    op.drop_table("users")
    op.execute("DROP TYPE IF EXISTS request_status_enum")
    op.execute("DROP TYPE IF EXISTS profile_status_enum")
    op.execute("DROP TYPE IF EXISTS diet_enum")
    op.execute("DROP TYPE IF EXISTS manglik_enum")
    op.execute("DROP TYPE IF EXISTS gender_enum")
