"""add electric charge breakdown columns to meter_reading_imports

Revision ID: 018
Revises: 017
Create Date: 2026-06-25
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "018"
down_revision: Union[str, None] = "017"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

NEW_COLUMNS = [
    ("peso_kwh", "NUMERIC(10,4)"),
    ("sub_total", "NUMERIC(10,2)"),
    ("total_with_vat", "NUMERIC(10,2)"),
    ("elec_bill", "NUMERIC(10,2)"),
]


def upgrade() -> None:
    for schema in [None, "demo", "pilot"]:
        table_prefix = f"{schema}." if schema else ""
        for col_name, col_type in NEW_COLUMNS:
            op.execute(
                sa.text(
                    f"ALTER TABLE {table_prefix}meter_reading_imports "
                    f"ADD COLUMN IF NOT EXISTS {col_name} {col_type}"
                )
            )


def downgrade() -> None:
    for schema in [None, "demo", "pilot"]:
        table_prefix = f"{schema}." if schema else ""
        for col_name, _ in reversed(NEW_COLUMNS):
            op.execute(
                sa.text(
                    f"ALTER TABLE {table_prefix}meter_reading_imports "
                    f"DROP COLUMN IF EXISTS {col_name}"
                )
            )
