"""add miscellaneous transactions table

Revision ID: 010
Revises: 009
Create Date: 2026-05-29
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision: str = "010"
down_revision: Union[str, None] = "009"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "miscellaneous_transactions",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("resident_id", UUID(as_uuid=True), sa.ForeignKey("residents.id", ondelete="SET NULL"), nullable=True),
        sa.Column("branch", sa.String(50), nullable=True),
        sa.Column("room_id", UUID(as_uuid=True), sa.ForeignKey("rooms.id", ondelete="SET NULL"), nullable=True),
        sa.Column("description", sa.Text, nullable=False),
        sa.Column("amount", sa.Numeric(10, 2), nullable=False),
        sa.Column("category", sa.String(50), server_default="other", nullable=False),
        sa.Column("transaction_date", sa.Date, nullable=False),
        sa.Column("status", sa.String(20), server_default="pending", nullable=False),
        sa.Column("recorded_by", UUID(as_uuid=True), sa.ForeignKey("staff.id"), nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_misc_tx_branch", "miscellaneous_transactions", ["branch"])
    op.create_index("ix_misc_tx_date", "miscellaneous_transactions", ["transaction_date"])
    op.create_index("ix_misc_tx_status", "miscellaneous_transactions", ["status"])


def downgrade() -> None:
    op.drop_index("ix_misc_tx_status", table_name="miscellaneous_transactions")
    op.drop_index("ix_misc_tx_date", table_name="miscellaneous_transactions")
    op.drop_index("ix_misc_tx_branch", table_name="miscellaneous_transactions")
    op.drop_table("miscellaneous_transactions")
