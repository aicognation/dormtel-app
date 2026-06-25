"""Create billing_statements table in demo and pilot schemas

Revision ID: 019
Revises: 018
Create Date: 2026-06-25
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSON

revision: str = "019"
down_revision: str = "018"

SCHEMAS = ["demo", "pilot"]


def upgrade() -> None:
    for schema in SCHEMAS:
        op.execute(f"""
            CREATE TABLE IF NOT EXISTS {schema}.billing_statements (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                resident_id UUID NOT NULL REFERENCES {schema}.residents(id),
                billing_period VARCHAR NOT NULL,
                scope_type VARCHAR NOT NULL DEFAULT 'resident',
                scope_target VARCHAR,
                file_path VARCHAR NOT NULL,
                file_name VARCHAR NOT NULL,
                file_size INTEGER,
                metadata_json JSON,
                status VARCHAR NOT NULL DEFAULT 'generated',
                sent_at TIMESTAMP,
                sent_to VARCHAR,
                email_status VARCHAR,
                created_at TIMESTAMP NOT NULL DEFAULT now()
            )
        """)


def downgrade() -> None:
    for schema in SCHEMAS:
        op.execute(f"DROP TABLE IF EXISTS {schema}.billing_statements")
