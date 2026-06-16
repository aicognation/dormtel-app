"""link residents to beds

Revision ID: 006
Revises: 005
Create Date: 2026-05-25
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision: str = "006"
down_revision: Union[str, None] = "005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add bed_id column
    op.add_column("residents", sa.Column("bed_id", UUID(as_uuid=True), sa.ForeignKey("beds.id"), nullable=True))
    op.create_index("ix_residents_bed_id", "residents", ["bed_id"])

    # Backfill bed_id from room_id + bed_number via a temp mapping
    # For seed/demo environments this will be handled by re-seeding.
    # For production, a data migration script would be run separately.

    # Drop old columns
    op.drop_constraint("residents_room_id_fkey", "residents", type_="foreignkey")
    op.execute("DROP INDEX IF EXISTS ix_residents_room_id")
    op.drop_column("residents", "room_id")
    op.drop_column("residents", "bed_number")


def downgrade() -> None:
    op.add_column("residents", sa.Column("room_id", UUID(as_uuid=True), sa.ForeignKey("rooms.id"), nullable=True))
    op.add_column("residents", sa.Column("bed_number", sa.Integer, nullable=True))
    op.create_index("ix_residents_room_id", "residents", ["room_id"])
    op.drop_index("ix_residents_bed_id", table_name="residents")
    op.drop_column("residents", "bed_id")
