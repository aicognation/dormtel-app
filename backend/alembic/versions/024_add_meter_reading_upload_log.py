"""add meter_reading_upload_log for audit trail

Revision ID: 024
Revises: 023
Create Date: 2026-08-04
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSON

revision: str = "024"
down_revision: str = "023"
branch_labels = None
depends_on = None

SCHEMAS = ["demo", "pilot"]


def upgrade() -> None:
    for schema in SCHEMAS:
        op.create_table(
            "meter_reading_upload_log",
            sa.Column("id", UUID(as_uuid=True), primary_key=True),
            sa.Column("property_code", sa.String(20), nullable=False),
            sa.Column("uploaded_by", UUID(as_uuid=True), nullable=True),
            sa.Column("uploaded_at", sa.DateTime, nullable=False, server_default=sa.text("now()")),
            sa.Column("source_filename", sa.String(255), nullable=False),
            sa.Column("template_id", UUID(as_uuid=True), nullable=True),  # FK to meter_reading_templates
            sa.Column("template_type", sa.String(20), nullable=True),
            sa.Column("period_start", sa.Date, nullable=True),
            sa.Column("period_end", sa.Date, nullable=True),
            sa.Column("upload_kind", sa.String(20), nullable=False),  # daily_sheet / standard
            sa.Column("rows_presented", sa.Integer, nullable=False, server_default="0"),
            sa.Column("residents_matched", sa.Integer, nullable=False, server_default="0"),
            sa.Column("readings_imported", sa.Integer, nullable=False, server_default="0"),
            sa.Column("skipped", sa.Integer, nullable=False, server_default="0"),
            sa.Column("allow_missing", sa.Boolean, nullable=False, server_default="false"),
            sa.Column("result", sa.String(20), nullable=False),  # accepted / rejected / partial
            sa.Column("issues", JSON, nullable=True),  # [{severity, code, message}]
            sa.Column("archive_upload_id", UUID(as_uuid=True), nullable=True),  # FK to archive DB uploads
            schema=schema,
        )


def downgrade() -> None:
    for schema in SCHEMAS:
        op.drop_table("meter_reading_upload_log", schema=schema)
