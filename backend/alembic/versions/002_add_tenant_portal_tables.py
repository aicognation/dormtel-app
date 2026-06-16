"""add tenant portal tables

Revision ID: 002
Revises: 001
Create Date: 2026-05-18
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    service_category = sa.Enum(
        "plumbing", "electrical", "aircon", "pest_control", "wifi",
        "water_supply", "lock_key", "cleaning", "appliance", "other",
        name="service_category"
    )
    service_priority = sa.Enum("low", "medium", "high", "urgent", name="service_priority")
    service_status = sa.Enum(
        "submitted", "acknowledged", "in_progress", "resolved", "closed",
        name="service_status"
    )
    announcement_category = sa.Enum(
        "general", "maintenance", "billing", "event", "emergency",
        name="announcement_category"
    )
    announcement_priority = sa.Enum("normal", "important", "urgent", name="announcement_priority")

    op.create_table(
        "service_requests",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("resident_id", UUID(as_uuid=True), sa.ForeignKey("residents.id"), nullable=False),
        sa.Column("category", service_category, nullable=False),
        sa.Column("subject", sa.String(255), nullable=False),
        sa.Column("description", sa.Text),
        sa.Column("location", sa.String(100)),
        sa.Column("priority", service_priority, nullable=False, server_default="medium"),
        sa.Column("status", service_status, nullable=False, server_default="submitted"),
        sa.Column("resolution_notes", sa.Text),
        sa.Column("submitted_at", sa.DateTime, nullable=False),
        sa.Column("resolved_at", sa.DateTime),
        sa.Column("created_at", sa.DateTime, nullable=False),
    )

    op.create_table(
        "announcements",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("category", announcement_category, nullable=False),
        sa.Column("priority", announcement_priority, nullable=False, server_default="normal"),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("published_at", sa.DateTime, nullable=False),
        sa.Column("created_at", sa.DateTime, nullable=False),
    )


def downgrade() -> None:
    op.drop_table("announcements")
    op.drop_table("service_requests")

    for enum_name in [
        "announcement_priority", "announcement_category",
        "service_status", "service_priority", "service_category",
    ]:
        sa.Enum(name=enum_name).drop(op.get_bind(), checkfirst=True)
