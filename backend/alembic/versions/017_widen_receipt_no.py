"""widen payments receipt_no column for proof-of-payment file paths

Revision ID: 017
Revises: 016
Create Date: 2026-06-25
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "017"
down_revision: Union[str, None] = "016"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    for schema in [None, "demo", "pilot"]:
        table_prefix = f"{schema}." if schema else ""
        op.execute(
            sa.text(
                f"ALTER TABLE {table_prefix}payments "
                f"ALTER COLUMN receipt_no TYPE VARCHAR(500)"
            )
        )


def downgrade() -> None:
    for schema in [None, "demo", "pilot"]:
        table_prefix = f"{schema}." if schema else ""
        op.execute(
            sa.text(
                f"ALTER TABLE {table_prefix}payments "
                f"ALTER COLUMN receipt_no TYPE VARCHAR(50)"
            )
        )
