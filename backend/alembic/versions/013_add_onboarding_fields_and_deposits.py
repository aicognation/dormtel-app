"""add onboarding fields and deposits table

Revision ID: 013
Revises: 012
Create Date: 2026-06-16
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSON

revision: str = "013"
down_revision: Union[str, None] = "012"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _create_enum_type(name: str, values: list[str], schema: str = "public") -> None:
    """Helper to create PostgreSQL enum type if it doesn't exist."""
    values_str = ", ".join(f"'{v}'" for v in values)
    op.execute(f"DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = '{name}') THEN CREATE TYPE {schema}.{name} AS ENUM ({values_str}); END IF; END $$;")


def _drop_enum_type(name: str, schema: str = "public") -> None:
    op.execute(f"DROP TYPE IF EXISTS {schema}.{name} CASCADE")


def upgrade() -> None:
    # Create enum types first (required before adding columns that use them)
    _create_enum_type("dormer_type", ["student", "reviewee", "working_professional", "other"])
    _create_enum_type("deposit_type", ["advance", "security", "utility"])
    _create_enum_type("deposit_status", ["paid", "refunded", "forfeited", "pending"])

    # Add room_type to rooms
    op.add_column("rooms", sa.Column("room_type", sa.String(50), nullable=True))

    # Add new person/demographic fields to residents
    op.add_column("residents", sa.Column("source", sa.String(50), nullable=True))
    op.add_column("residents", sa.Column("location", sa.String(50), nullable=True))
    op.add_column(
        "residents",
        sa.Column("dormer_type", sa.Enum("student", "reviewee", "working_professional", "other", name="dormer_type"), nullable=True),
    )
    op.add_column("residents", sa.Column("board_exam_type", sa.String(100), nullable=True))
    op.add_column("residents", sa.Column("lease_term_months", sa.Integer, nullable=True))
    op.add_column("residents", sa.Column("previous_stays", JSON, nullable=True))

    # Create deposits table
    op.create_table(
        "deposits",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("resident_id", UUID(as_uuid=True), sa.ForeignKey("residents.id", ondelete="CASCADE"), nullable=False),
        sa.Column("deposit_type", sa.Enum("advance", "security", "utility", name="deposit_type"), nullable=False),
        sa.Column("amount", sa.Numeric(10, 2), nullable=False),
        sa.Column("receipt_number", sa.String(100), nullable=True),
        sa.Column("payment_date", sa.Date, nullable=True),
        sa.Column("status", sa.Enum("paid", "refunded", "forfeited", "pending", name="deposit_status"), nullable=False, server_default="paid"),
        sa.Column("refunded_amount", sa.Numeric(10, 2), nullable=True),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.text("NOW()")),
    )


def downgrade() -> None:
    op.drop_table("deposits")
    op.drop_column("residents", "previous_stays")
    op.drop_column("residents", "lease_term_months")
    op.drop_column("residents", "board_exam_type")
    op.drop_column("residents", "dormer_type")
    op.drop_column("residents", "location")
    op.drop_column("residents", "source")
    op.drop_column("rooms", "room_type")
    _drop_enum_type("deposit_status")
    _drop_enum_type("deposit_type")
    _drop_enum_type("dormer_type")
