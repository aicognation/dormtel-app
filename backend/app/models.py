import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Date, DateTime, Numeric, Enum, ForeignKey, Text, JSON, Boolean
from sqlalchemy.dialects.postgresql import UUID, INET
from sqlalchemy.orm import relationship
from app.database import Base

class Resident(Base):
    __tablename__ = "residents"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    full_name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    phone = Column(String(20), unique=True, nullable=False)
    id_type = Column(String(50))
    id_number = Column(String(100))
    status = Column(Enum("prospect", "reserved", "active", "inactive", "moved_out", name="resident_status"), nullable=False, default="prospect")
    room_id = Column(UUID(as_uuid=True), ForeignKey("rooms.id"))
    bed_number = Column(Integer)
    move_in_date = Column(Date)
    move_out_date = Column(Date)
    monthly_rate = Column(Numeric(10, 2), nullable=False)
    deposit_paid = Column(Numeric(10, 2))
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    room = relationship("Room", back_populates="residents")
    billings = relationship("Billing", back_populates="resident", cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="resident", cascade="all, delete-orphan")
    ledger_entries = relationship("LedgerEntry", back_populates="resident", cascade="all, delete-orphan")
    inquiries = relationship("Inquiry", back_populates="resident")

class Room(Base):
    __tablename__ = "rooms"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    room_number = Column(String(20), nullable=False, unique=True)
    building = Column(String(50))
    capacity = Column(Integer, nullable=False)
    occupied_beds = Column(Integer, nullable=False, default=0)
    rate_per_bed = Column(Numeric(10, 2), nullable=False)
    status = Column(Enum("available", "full", "maintenance", name="room_status"), nullable=False, default="available")
    residents = relationship("Resident", back_populates="room")

class Inquiry(Base):
    __tablename__ = "inquiries"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source = Column(Enum("facebook", "instagram", "tiktok", "walkin", "phone", name="inquiry_source"), nullable=False)
    external_id = Column(String(255))
    content = Column(Text)
    sentiment_score = Column(Numeric(3, 2))
    lead_score = Column(Integer)
    status = Column(Enum("new", "responded", "escalated", "converted", "closed", name="inquiry_status"), nullable=False, default="new")
    assigned_to = Column(UUID(as_uuid=True), ForeignKey("staff.id"))
    resident_id = Column(UUID(as_uuid=True), ForeignKey("residents.id"))
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    resident = relationship("Resident", back_populates="inquiries")

class MeterReading(Base):
    __tablename__ = "meter_readings"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    building = Column(String(50), nullable=False)
    reading_date = Column(Date, nullable=False)
    electric_reading = Column(Numeric(10, 2))
    water_reading = Column(Numeric(10, 2))
    submitted_by = Column(UUID(as_uuid=True), ForeignKey("staff.id"))
    photo_url = Column(String(500))
    variance_pct = Column(Numeric(5, 2))
    status = Column(Enum("pending", "approved", "rejected", "estimated", name="meter_status"), nullable=False, default="pending")
    approved_by = Column(UUID(as_uuid=True), ForeignKey("staff.id"))

class Billing(Base):
    __tablename__ = "billings"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    resident_id = Column(UUID(as_uuid=True), ForeignKey("residents.id"), nullable=False)
    billing_period = Column(String(20), nullable=False)
    rent_amount = Column(Numeric(10, 2), nullable=False)
    electric_charge = Column(Numeric(10, 2))
    water_charge = Column(Numeric(10, 2))
    other_charges = Column(Numeric(10, 2))
    previous_balance = Column(Numeric(10, 2))
    total_amount = Column(Numeric(10, 2), nullable=False)
    variance_pct = Column(Numeric(5, 2))
    status = Column(Enum("draft", "pending_review", "approved", "distributed", "paid", "overdue", name="billing_status"), nullable=False, default="draft")
    approved_by = Column(UUID(as_uuid=True), ForeignKey("staff.id"))
    distributed_at = Column(DateTime)
    pdf_url = Column(String(500))
    payment_link = Column(String(500))
    resident = relationship("Resident", back_populates="billings")

class Payment(Base):
    __tablename__ = "payments"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    resident_id = Column(UUID(as_uuid=True), ForeignKey("residents.id"), nullable=False)
    billing_id = Column(UUID(as_uuid=True), ForeignKey("billings.id"))
    amount = Column(Numeric(10, 2), nullable=False)
    method = Column(Enum("gcash", "maya", "bank_transfer", "cash", name="payment_method"), nullable=False)
    gateway_ref = Column(String(255))
    status = Column(Enum("pending", "verified", "matched", "unreconciled", "refunded", name="payment_status"), nullable=False, default="pending")
    matched_at = Column(DateTime)
    sales_invoice_no = Column(String(50))
    receipt_no = Column(String(50))
    webhook_payload = Column(JSON)
    resident = relationship("Resident", back_populates="payments")

class LedgerEntry(Base):
    __tablename__ = "ledger_entries"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    resident_id = Column(UUID(as_uuid=True), ForeignKey("residents.id"), nullable=False)
    entry_type = Column(Enum("debit", "credit", name="ledger_type"), nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    description = Column(String(255))
    reference_id = Column(UUID(as_uuid=True))
    running_balance = Column(Numeric(10, 2), nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    resident = relationship("Resident", back_populates="ledger_entries")

class Checkpoint(Base):
    __tablename__ = "checkpoints"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    checkpoint_id = Column(String(20), nullable=False, unique=True)
    workflow_id = Column(UUID(as_uuid=True))
    stage = Column(String(50), nullable=False)
    status = Column(Enum("pending", "decided", "escalated", "timeout", name="checkpoint_status"), nullable=False, default="pending")
    decision = Column(Enum("approve", "reject", "hold", name="checkpoint_decision"))
    decided_by = Column(UUID(as_uuid=True), ForeignKey("staff.id"))
    sla_deadline = Column(DateTime, nullable=False)
    context_package = Column(JSON)

class Staff(Base):
    __tablename__ = "staff"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    full_name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    role = Column(Enum("manager", "admin", "dm", name="staff_role"), nullable=False)
    phone = Column(String(20))
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    table_name = Column(String(50), nullable=False)
    record_id = Column(UUID(as_uuid=True), nullable=False)
    action = Column(Enum("create", "update", "delete", name="audit_action"), nullable=False)
    old_values = Column(JSON)
    new_values = Column(JSON)
    actor = Column(String(100))
    ip_address = Column(INET)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

class MoveOut(Base):
    __tablename__ = "move_outs"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    resident_id = Column(UUID(as_uuid=True), ForeignKey("residents.id"), nullable=False)
    requested_date = Column(Date, nullable=False)
    actual_date = Column(Date)
    reason = Column(Text)
    forwarding_contact = Column(String(255))
    status = Column(Enum("requested", "clearance", "final_billing", "refund_pending", "completed", name="moveout_status"), nullable=False, default="requested")
    final_billing_id = Column(UUID(as_uuid=True), ForeignKey("billings.id"))
    refund_amount = Column(Numeric(10, 2))
    accounting_submitted_at = Column(DateTime)
    accounting_resolved_at = Column(DateTime)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
