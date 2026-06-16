"""add auth tables

Revision ID: 008
Revises: 007
Create Date: 2026-05-29
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision: str = "008"
down_revision: Union[str, None] = "007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Staff enhancements
    op.add_column("staff", sa.Column("password_hash", sa.String(255), nullable=True))
    op.add_column("staff", sa.Column("managed_branch", sa.String(50), nullable=True))
    op.add_column("staff", sa.Column("is_active", sa.Boolean, server_default="true"))
    op.add_column("staff", sa.Column("is_verified", sa.Boolean, server_default="false"))
    op.add_column("staff", sa.Column("email_verified_at", sa.DateTime, nullable=True))
    op.add_column("staff", sa.Column("last_login_at", sa.DateTime, nullable=True))

    # Verification codes
    op.create_table(
        "verification_codes",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("staff_id", UUID(as_uuid=True), sa.ForeignKey("staff.id", ondelete="CASCADE"), nullable=False),
        sa.Column("code", sa.String(10), nullable=False),
        sa.Column("purpose", sa.String(20), nullable=False),
        sa.Column("expires_at", sa.DateTime, nullable=False),
        sa.Column("used_at", sa.DateTime, nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_verification_codes_staff_id", "verification_codes", ["staff_id"])
    op.create_index("ix_verification_codes_code", "verification_codes", ["code"])

    # Password resets
    op.create_table(
        "password_resets",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("staff_id", UUID(as_uuid=True), sa.ForeignKey("staff.id", ondelete="CASCADE"), nullable=False),
        sa.Column("token_hash", sa.String(255), nullable=False),
        sa.Column("expires_at", sa.DateTime, nullable=False),
        sa.Column("used_at", sa.DateTime, nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_password_resets_staff_id", "password_resets", ["staff_id"])

    # Notifications table for Super Admin
    op.create_table(
        "notifications",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("staff_id", UUID(as_uuid=True), sa.ForeignKey("staff.id", ondelete="CASCADE"), nullable=False),
        sa.Column("type", sa.String(50), nullable=False),
        sa.Column("message", sa.Text, nullable=False),
        sa.Column("is_read", sa.Boolean, server_default="false"),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_notifications_staff_id", "notifications", ["staff_id"])
    op.create_index("ix_notifications_is_read", "notifications", ["is_read"])


def downgrade() -> None:
    op.drop_index("ix_notifications_is_read", table_name="notifications")
    op.drop_index("ix_notifications_staff_id", table_name="notifications")
    op.drop_table("notifications")
    op.drop_index("ix_password_resets_staff_id", table_name="password_resets")
    op.drop_table("password_resets")
    op.drop_index("ix_verification_codes_code", table_name="verification_codes")
    op.drop_index("ix_verification_codes_staff_id", table_name="verification_codes")
    op.drop_table("verification_codes")
    op.drop_column("staff", "last_login_at")
    op.drop_column("staff", "email_verified_at")
    op.drop_column("staff", "is_verified")
    op.drop_column("staff", "is_active")
    op.drop_column("staff", "managed_branch")
    op.drop_column("staff", "password_hash")
