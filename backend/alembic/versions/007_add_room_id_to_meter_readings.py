"""add room_id to meter_readings

Revision ID: 007
Revises: 006
Create Date: 2026-05-26
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision: str = "007"
down_revision: Union[str, None] = "006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "meter_readings",
        sa.Column("room_id", UUID(as_uuid=True), sa.ForeignKey("rooms.id"), nullable=True),
    )
    op.create_index("ix_meter_readings_room_id", "meter_readings", ["room_id"])


def downgrade() -> None:
    op.drop_index("ix_meter_readings_room_id", table_name="meter_readings")
    op.drop_column("meter_readings", "room_id")
