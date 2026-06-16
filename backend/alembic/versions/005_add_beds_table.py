"""add beds table

Revision ID: 005
Revises: 004
Create Date: 2026-05-25
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision: str = "005"
down_revision: Union[str, None] = "004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    
    # Ensure bed_type enum exists (created by 003, but be safe)
    bed_type_enum = sa.Enum("lower_bunk", "upper_bunk", "loft_type", name="bed_type", create_type=False)
    bed_type_enum.create(bind, checkfirst=True)
    
    # Create bed_status enum if not exists
    bed_status_enum = sa.Enum("available", "reserved", "occupied", name="bed_status", create_type=False)
    bed_status_enum.create(bind, checkfirst=True)
    
    # Create table using raw SQL to avoid SQLAlchemy auto-creating enums
    op.execute("""
        CREATE TABLE beds (
            id UUID PRIMARY KEY,
            bed_code VARCHAR(20) NOT NULL UNIQUE,
            room_id UUID NOT NULL REFERENCES rooms(id),
            bed_number INTEGER NOT NULL,
            bed_type bed_type,
            rate_per_bed NUMERIC(10, 2) NOT NULL,
            status bed_status NOT NULL DEFAULT 'available'
        )
    """)
    op.create_index("ix_beds_room_id", "beds", ["room_id"])
    op.create_index("ix_beds_status", "beds", ["status"])


def downgrade() -> None:
    op.drop_index("ix_beds_status", table_name="beds")
    op.drop_index("ix_beds_room_id", table_name="beds")
    op.drop_table("beds")
    op.execute("DROP TYPE bed_status")
