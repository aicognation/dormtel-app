"""add meter_reading_imports table

Revision ID: 014
Revises: 013
Create Date: 2026-06-16
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSON

revision: str = "014"
down_revision: Union[str, None] = "013"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "meter_reading_imports",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("resident_id", UUID(as_uuid=True), sa.ForeignKey("residents.id"), nullable=False),
        sa.Column("building", sa.String(50), nullable=False),
        sa.Column("year", sa.Integer, nullable=False),
        sa.Column("month", sa.Integer, nullable=False),
        sa.Column("total_electric_usage", sa.Numeric(10, 2), nullable=True),
        sa.Column("water_bill", sa.Numeric(10, 2), nullable=True),
        sa.Column("water_days", sa.Integer, nullable=True),
        sa.Column("water_rate", sa.Numeric(10, 2), nullable=True),
        sa.Column("misc_charges", JSON, nullable=True),
        sa.Column("source_filename", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.text("NOW()")),
    )
    op.create_index("idx_meter_imports_resident_period", "meter_reading_imports", ["resident_id", "year", "month"], unique=False)
    op.create_index("idx_meter_imports_building_period", "meter_reading_imports", ["building", "year", "month"], unique=False)


def downgrade() -> None:
    op.drop_index("idx_meter_imports_building_period", table_name="meter_reading_imports")
    op.drop_index("idx_meter_imports_resident_period", table_name="meter_reading_imports")
    op.drop_table("meter_reading_imports")
