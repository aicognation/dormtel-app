"""drop unique constraints on residents email and phone

Revision ID: 016
Revises: 015
Create Date: 2026-06-24
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "016"
down_revision: Union[str, None] = "015"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Drop unique constraints on email and phone in all schemas
    for schema in [None, "demo", "pilot"]:
        kwargs = {"schema": schema} if schema else {}
        table = "residents"

        # Drop unique constraints by name patterns PostgreSQL uses
        op.execute(
            sa.text(
                f"DO $$ DECLARE r RECORD; "
                f"BEGIN "
                f"  FOR r IN "
                f"    SELECT conname FROM pg_constraint c "
                f"    JOIN pg_class t ON c.conrelid = t.oid "
                f"    JOIN pg_namespace n ON t.relnamespace = n.oid "
                f"    WHERE t.relname = '{table}' "
                f"    AND n.nspname = '{schema or 'public'}' "
                f"    AND c.contype = 'u' "
                f"  LOOP "
                f"    EXECUTE 'ALTER TABLE {schema + '.' if schema else ''}{table} DROP CONSTRAINT ' || quote_ident(r.conname); "
                f"  END LOOP; "
                f"END $$;"
            )
        )


def downgrade() -> None:
    # Re-add unique constraints
    for schema in [None, "demo", "pilot"]:
        kwargs = {"schema": schema} if schema else {}
        table_prefix = f"{schema}." if schema else ""
        op.execute(
            sa.text(
                f"ALTER TABLE {table_prefix}residents "
                f"ADD CONSTRAINT residents_email_key UNIQUE (email)"
            )
        )
        op.execute(
            sa.text(
                f"ALTER TABLE {table_prefix}residents "
                f"ADD CONSTRAINT residents_phone_key UNIQUE (phone)"
            )
        )
