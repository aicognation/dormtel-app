"""add contract_end_date to residents

Revision ID: 004
Revises: 003
Create Date: 2026-05-25
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "004"
down_revision: Union[str, None] = "003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("residents", sa.Column("contract_end_date", sa.Date))


def downgrade() -> None:
    op.drop_column("residents", "contract_end_date")
