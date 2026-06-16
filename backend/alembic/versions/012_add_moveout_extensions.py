"""add moveout extension fields

Revision ID: 012
Revises: 011
Create Date: 2026-06-11
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision: str = "012"
down_revision: Union[str, None] = "011"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("move_outs", sa.Column("extended_date", sa.Date, nullable=True))
    op.add_column("move_outs", sa.Column("extended_by", UUID(as_uuid=True), sa.ForeignKey("staff.id"), nullable=True))
    op.add_column("move_outs", sa.Column("extension_reason", sa.Text, nullable=True))
    op.add_column("move_outs", sa.Column("is_end_of_month_flag", sa.Boolean, nullable=True, server_default=sa.false()))


def downgrade() -> None:
    op.drop_column("move_outs", "extended_date")
    op.drop_column("move_outs", "extended_by")
    op.drop_column("move_outs", "extension_reason")
    op.drop_column("move_outs", "is_end_of_month_flag")
