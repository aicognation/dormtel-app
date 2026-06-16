"""initial schema

Revision ID: 001
Revises:
Create Date: 2025-05-16
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, INET

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Enums
    resident_status = sa.Enum("prospect", "reserved", "active", "inactive", "moved_out", name="resident_status")
    room_status = sa.Enum("available", "full", "maintenance", name="room_status")
    inquiry_source = sa.Enum("facebook", "instagram", "tiktok", "walkin", "phone", name="inquiry_source")
    inquiry_status = sa.Enum("new", "responded", "escalated", "converted", "closed", name="inquiry_status")
    meter_status = sa.Enum("pending", "approved", "rejected", "estimated", name="meter_status")
    billing_status = sa.Enum("draft", "pending_review", "approved", "distributed", "paid", "overdue", name="billing_status")
    payment_method = sa.Enum("gcash", "maya", "bank_transfer", "cash", name="payment_method")
    payment_status = sa.Enum("pending", "verified", "matched", "unreconciled", "refunded", name="payment_status")
    ledger_type = sa.Enum("debit", "credit", name="ledger_type")
    checkpoint_status = sa.Enum("pending", "decided", "escalated", "timeout", name="checkpoint_status")
    checkpoint_decision = sa.Enum("approve", "reject", "hold", name="checkpoint_decision")
    staff_role = sa.Enum("manager", "admin", "dm", name="staff_role")
    audit_action = sa.Enum("create", "update", "delete", name="audit_action")
    moveout_status = sa.Enum("requested", "clearance", "final_billing", "refund_pending", "completed", name="moveout_status")

    # Staff table (referenced by FKs)
    op.create_table(
        "staff",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("email", sa.String(255), unique=True, nullable=False),
        sa.Column("role", staff_role, nullable=False),
        sa.Column("phone", sa.String(20)),
        sa.Column("created_at", sa.DateTime, nullable=False),
    )

    # Rooms table
    op.create_table(
        "rooms",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("room_number", sa.String(20), nullable=False, unique=True),
        sa.Column("building", sa.String(50)),
        sa.Column("capacity", sa.Integer, nullable=False),
        sa.Column("occupied_beds", sa.Integer, nullable=False, server_default="0"),
        sa.Column("rate_per_bed", sa.Numeric(10, 2), nullable=False),
        sa.Column("status", room_status, nullable=False, server_default="available"),
    )

    # Residents table
    op.create_table(
        "residents",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("email", sa.String(255), unique=True, nullable=False),
        sa.Column("phone", sa.String(20), unique=True, nullable=False),
        sa.Column("id_type", sa.String(50)),
        sa.Column("id_number", sa.String(100)),
        sa.Column("status", resident_status, nullable=False, server_default="prospect"),
        sa.Column("room_id", UUID(as_uuid=True), sa.ForeignKey("rooms.id")),
        sa.Column("bed_number", sa.Integer),
        sa.Column("move_in_date", sa.Date),
        sa.Column("move_out_date", sa.Date),
        sa.Column("monthly_rate", sa.Numeric(10, 2), nullable=False),
        sa.Column("deposit_paid", sa.Numeric(10, 2)),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
    )

    # Inquiries table
    op.create_table(
        "inquiries",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("source", inquiry_source, nullable=False),
        sa.Column("external_id", sa.String(255)),
        sa.Column("content", sa.Text),
        sa.Column("sentiment_score", sa.Numeric(3, 2)),
        sa.Column("lead_score", sa.Integer),
        sa.Column("status", inquiry_status, nullable=False, server_default="new"),
        sa.Column("assigned_to", UUID(as_uuid=True), sa.ForeignKey("staff.id")),
        sa.Column("resident_id", UUID(as_uuid=True), sa.ForeignKey("residents.id")),
        sa.Column("created_at", sa.DateTime, nullable=False),
    )

    # Meter readings table
    op.create_table(
        "meter_readings",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("building", sa.String(50), nullable=False),
        sa.Column("reading_date", sa.Date, nullable=False),
        sa.Column("electric_reading", sa.Numeric(10, 2)),
        sa.Column("water_reading", sa.Numeric(10, 2)),
        sa.Column("submitted_by", UUID(as_uuid=True), sa.ForeignKey("staff.id")),
        sa.Column("photo_url", sa.String(500)),
        sa.Column("variance_pct", sa.Numeric(5, 2)),
        sa.Column("status", meter_status, nullable=False, server_default="pending"),
        sa.Column("approved_by", UUID(as_uuid=True), sa.ForeignKey("staff.id")),
    )

    # Billings table
    op.create_table(
        "billings",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("resident_id", UUID(as_uuid=True), sa.ForeignKey("residents.id"), nullable=False),
        sa.Column("billing_period", sa.String(20), nullable=False),
        sa.Column("rent_amount", sa.Numeric(10, 2), nullable=False),
        sa.Column("electric_charge", sa.Numeric(10, 2)),
        sa.Column("water_charge", sa.Numeric(10, 2)),
        sa.Column("other_charges", sa.Numeric(10, 2)),
        sa.Column("previous_balance", sa.Numeric(10, 2)),
        sa.Column("total_amount", sa.Numeric(10, 2), nullable=False),
        sa.Column("variance_pct", sa.Numeric(5, 2)),
        sa.Column("status", billing_status, nullable=False, server_default="draft"),
        sa.Column("approved_by", UUID(as_uuid=True), sa.ForeignKey("staff.id")),
        sa.Column("distributed_at", sa.DateTime),
        sa.Column("pdf_url", sa.String(500)),
        sa.Column("payment_link", sa.String(500)),
        sa.Column("created_at", sa.DateTime, nullable=False),
    )

    # Payments table
    op.create_table(
        "payments",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("resident_id", UUID(as_uuid=True), sa.ForeignKey("residents.id"), nullable=False),
        sa.Column("billing_id", UUID(as_uuid=True), sa.ForeignKey("billings.id")),
        sa.Column("amount", sa.Numeric(10, 2), nullable=False),
        sa.Column("method", payment_method, nullable=False),
        sa.Column("gateway_ref", sa.String(255)),
        sa.Column("status", payment_status, nullable=False, server_default="pending"),
        sa.Column("matched_at", sa.DateTime),
        sa.Column("sales_invoice_no", sa.String(50)),
        sa.Column("receipt_no", sa.String(50)),
        sa.Column("webhook_payload", sa.JSON),
        sa.Column("created_at", sa.DateTime, nullable=False),
    )

    # Ledger entries table
    op.create_table(
        "ledger_entries",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("resident_id", UUID(as_uuid=True), sa.ForeignKey("residents.id"), nullable=False),
        sa.Column("entry_type", ledger_type, nullable=False),
        sa.Column("amount", sa.Numeric(10, 2), nullable=False),
        sa.Column("description", sa.String(255)),
        sa.Column("reference_id", UUID(as_uuid=True)),
        sa.Column("running_balance", sa.Numeric(10, 2), nullable=False),
        sa.Column("created_at", sa.DateTime, nullable=False),
    )

    # Checkpoints table
    op.create_table(
        "checkpoints",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("checkpoint_id", sa.String(20), nullable=False, unique=True),
        sa.Column("workflow_id", UUID(as_uuid=True)),
        sa.Column("stage", sa.String(50), nullable=False),
        sa.Column("status", checkpoint_status, nullable=False, server_default="pending"),
        sa.Column("decision", checkpoint_decision),
        sa.Column("decided_by", UUID(as_uuid=True), sa.ForeignKey("staff.id")),
        sa.Column("sla_deadline", sa.DateTime, nullable=False),
        sa.Column("context_package", sa.JSON),
    )

    # Audit logs table
    op.create_table(
        "audit_logs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("table_name", sa.String(50), nullable=False),
        sa.Column("record_id", UUID(as_uuid=True), nullable=False),
        sa.Column("action", audit_action, nullable=False),
        sa.Column("old_values", sa.JSON),
        sa.Column("new_values", sa.JSON),
        sa.Column("actor", sa.String(100)),
        sa.Column("ip_address", INET),
        sa.Column("created_at", sa.DateTime, nullable=False),
    )

    # Move-outs table
    op.create_table(
        "move_outs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("resident_id", UUID(as_uuid=True), sa.ForeignKey("residents.id"), nullable=False),
        sa.Column("requested_date", sa.Date, nullable=False),
        sa.Column("actual_date", sa.Date),
        sa.Column("reason", sa.Text),
        sa.Column("forwarding_contact", sa.String(255)),
        sa.Column("status", moveout_status, nullable=False, server_default="requested"),
        sa.Column("final_billing_id", UUID(as_uuid=True), sa.ForeignKey("billings.id")),
        sa.Column("refund_amount", sa.Numeric(10, 2)),
        sa.Column("accounting_submitted_at", sa.DateTime),
        sa.Column("accounting_resolved_at", sa.DateTime),
        sa.Column("created_at", sa.DateTime, nullable=False),
    )


def downgrade() -> None:
    op.drop_table("move_outs")
    op.drop_table("audit_logs")
    op.drop_table("checkpoints")
    op.drop_table("ledger_entries")
    op.drop_table("payments")
    op.drop_table("billings")
    op.drop_table("meter_readings")
    op.drop_table("inquiries")
    op.drop_table("residents")
    op.drop_table("rooms")
    op.drop_table("staff")

    for enum_name in [
        "moveout_status", "audit_action", "checkpoint_decision", "checkpoint_status",
        "ledger_type", "payment_status", "payment_method", "billing_status",
        "meter_status", "inquiry_status", "inquiry_source", "room_status",
        "resident_status", "staff_role",
    ]:
        sa.Enum(name=enum_name).drop(op.get_bind(), checkfirst=True)
