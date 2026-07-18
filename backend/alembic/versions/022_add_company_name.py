"""add company_name to residents

Revision ID: 022
Revises: 021
Create Date: 2026-07-19
"""
from alembic import op
import sqlalchemy as sa

revision: str = "022"
down_revision: str = "021"
branch_labels = None
depends_on = None

SCHEMAS = ["demo", "pilot"]


def upgrade() -> None:
    for schema in SCHEMAS:
        op.add_column(
            "residents",
            sa.Column("company_name", sa.String(255), nullable=True),
            schema=schema,
        )


def downgrade() -> None:
    for schema in SCHEMAS:
        op.drop_column("residents", "company_name", schema=schema)
