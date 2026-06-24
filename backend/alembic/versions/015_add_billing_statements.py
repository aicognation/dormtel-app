"""add billing_statements table

Revision ID: 015
Revises: 014
Create Date: 2026-06-23
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSON

revision: str = "015"
down_revision: Union[str, None] = "014"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "billing_statements",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("resident_id", UUID(as_uuid=True), sa.ForeignKey("residents.id", ondelete="CASCADE"), nullable=False),
        sa.Column("billing_period", sa.String(20), nullable=False),
        sa.Column("scope_type", sa.String(20), nullable=False, server_default="resident"),
        sa.Column("scope_target", sa.String(100), nullable=True),
        sa.Column("file_path", sa.String(500), nullable=False),
        sa.Column("file_name", sa.String(255), nullable=False),
        sa.Column("file_size", sa.Integer, nullable=True),
        sa.Column("metadata_json", JSON, nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="generated"),
        sa.Column("sent_at", sa.DateTime, nullable=True),
        sa.Column("sent_to", sa.String(255), nullable=True),
        sa.Column("email_status", sa.String(50), nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.text("NOW()")),
    )
    op.create_index("idx_billing_statements_resident_period", "billing_statements", ["resident_id", "billing_period"], unique=False)
    op.create_index("idx_billing_statements_created_at", "billing_statements", ["created_at"], unique=False)


def downgrade() -> None:
    op.drop_index("idx_billing_statements_created_at", table_name="billing_statements")
    op.drop_index("idx_billing_statements_resident_period", table_name="billing_statements")
    op.drop_table("billing_statements")
