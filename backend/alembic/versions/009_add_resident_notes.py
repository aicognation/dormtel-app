"""add resident notes and audit fields

Revision ID: 009
Revises: 008
Create Date: 2026-05-29
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision: str = "009"
down_revision: Union[str, None] = "008"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("residents", sa.Column("notes", sa.Text, nullable=True))
    op.add_column("residents", sa.Column("created_by", UUID(as_uuid=True), sa.ForeignKey("staff.id"), nullable=True))
    op.add_column("residents", sa.Column("updated_by", UUID(as_uuid=True), sa.ForeignKey("staff.id"), nullable=True))


def downgrade() -> None:
    op.drop_column("residents", "updated_by")
    op.drop_column("residents", "created_by")
    op.drop_column("residents", "notes")
