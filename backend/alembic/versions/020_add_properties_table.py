"""add properties table

Revision ID: 020
Revises: 019
Create Date: 2026-06-30
"""
from alembic import op
import sqlalchemy as sa

revision: str = "020"
down_revision: str = "019"
branch_labels = None
depends_on = None

SCHEMAS = ["demo", "pilot"]


def upgrade() -> None:
    # Create properties table in the public schema (using op for default schema)
    op.create_table(
        "properties",
        sa.Column("code", sa.String(10), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("address", sa.String(255), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default="true"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()")),
    )
    # Seed data for public schema
    op.execute("""
        INSERT INTO properties (code, name, address, is_active)
        VALUES ('DT01', 'Recto Branch', NULL, true),
               ('DT02', 'Sta. Mesa Branch', NULL, true)
        ON CONFLICT (code) DO NOTHING
    """)

    # Create in demo and pilot schemas
    for schema in SCHEMAS:
        op.execute(f"""
            CREATE TABLE IF NOT EXISTS {schema}.properties (
                code VARCHAR(10) PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                address VARCHAR(255),
                is_active BOOLEAN DEFAULT true,
                created_at TIMESTAMP DEFAULT now()
            )
        """)
        # Seed data
        op.execute(f"""
            INSERT INTO {schema}.properties (code, name, address, is_active)
            VALUES ('DT01', 'Recto Branch', NULL, true),
                   ('DT02', 'Sta. Mesa Branch', NULL, true)
            ON CONFLICT (code) DO NOTHING
        """)


def downgrade() -> None:
    for schema in SCHEMAS:
        op.execute(f"DROP TABLE IF EXISTS {schema}.properties")
    op.drop_table("properties")
