"""add meter_reading_templates registry for signed template fingerprints

Revision ID: 023
Revises: 022
Create Date: 2026-08-04
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSON

revision: str = "023"
down_revision: str = "022"
branch_labels = None
depends_on = None

SCHEMAS = ["demo", "pilot"]


def upgrade() -> None:
    for schema in SCHEMAS:
        op.create_table(
            "meter_reading_templates",
            sa.Column("id", UUID(as_uuid=True), primary_key=True),
            sa.Column("property_code", sa.String(20), nullable=False),
            sa.Column("template_type", sa.String(20), nullable=False),  # adhoc/daily/monthly/period
            sa.Column("period_start", sa.Date, nullable=True),
            sa.Column("period_end", sa.Date, nullable=True),
            sa.Column("roster_count", sa.Integer, nullable=False),
            sa.Column("roster", JSON, nullable=False),  # list of {resident_id, room_number, bed_code, full_name}
            sa.Column("roster_hash", sa.String(64), nullable=False),  # SHA-256 of canonical roster
            sa.Column("status", sa.String(20), nullable=False, server_default="generated"),  # generated/consumed/void
            sa.Column("generated_by", UUID(as_uuid=True), nullable=True),
            sa.Column("generated_at", sa.DateTime, nullable=False, server_default=sa.text("now()")),
            sa.Column("consumed_at", sa.DateTime, nullable=True),
            sa.Column("consumed_filename", sa.String(255), nullable=True),
            schema=schema,
        )


def downgrade() -> None:
    for schema in SCHEMAS:
        op.drop_table("meter_reading_templates", schema=schema)
