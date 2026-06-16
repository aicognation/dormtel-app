"""add resident_id to meter_readings

Revision ID: 011
Revises: 010
Create Date: 2026-06-11
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision: str = "011"
down_revision: Union[str, None] = "010"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "meter_readings",
        sa.Column("resident_id", UUID(as_uuid=True), sa.ForeignKey("residents.id"), nullable=True),
    )
    op.create_index("ix_meter_readings_resident_id", "meter_readings", ["resident_id"])


def downgrade() -> None:
    op.drop_index("ix_meter_readings_resident_id", table_name="meter_readings")
    op.drop_column("meter_readings", "resident_id")
