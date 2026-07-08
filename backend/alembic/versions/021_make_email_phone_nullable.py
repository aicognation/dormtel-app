"""make email and phone nullable in residents

Revision ID: 021
Revises: 020
Create Date: 2026-07-09
"""
from alembic import op
import sqlalchemy as sa

revision: str = "021"
down_revision: str = "020"
branch_labels = None
depends_on = None

SCHEMAS = ["demo", "pilot"]


def upgrade() -> None:
    for schema in SCHEMAS:
        op.alter_column(
            "residents",
            "email",
            existing_type=sa.String(),
            nullable=True,
            schema=schema,
        )
        op.alter_column(
            "residents",
            "phone",
            existing_type=sa.String(),
            nullable=True,
            schema=schema,
        )


def downgrade() -> None:
    for schema in SCHEMAS:
        op.alter_column(
            "residents",
            "phone",
            existing_type=sa.String(),
            nullable=False,
            schema=schema,
        )
        op.alter_column(
            "residents",
            "email",
            existing_type=sa.String(),
            nullable=False,
            schema=schema,
        )
