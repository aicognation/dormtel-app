import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Date, DateTime, Numeric, Enum, ForeignKey, Text, JSON, Boolean
from sqlalchemy.dialects.postgresql import UUID, INET
from sqlalchemy.orm import relationship
from app.database import Base


class Property(Base):
    __tablename__ = "properties"
    code = Column(String(10), primary_key=True)
    name = Column(String(100), nullable=False)
    address = Column(String(255))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class Resident(Base):
    __tablename__ = "residents"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    full_name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False)
    phone = Column(String(20), nullable=False)
    id_type = Column(String(50))
    id_number = Column(String(100))
    status = Column(Enum("prospect", "reserved", "active", "inactive", "moved_out", name="resident_status"), nullable=False, default="prospect")
    bed_id = Column(UUID(as_uuid=True), ForeignKey("beds.id"))
    move_in_date = Column(Date)
    move_out_date = Column(Date)
    contract_end_date = Column(Date)
    monthly_rate = Column(Numeric(10, 2), nullable=False)
    deposit_paid = Column(Numeric(10, 2))
    address = Column(Text)
    school = Column(String(255))
    course = Column(String(255))
    review_center = Column(String(255))
    company_name = Column(String(255))
    exam_date = Column(Date)
    is_first_time_dormer = Column(Boolean, default=True)
    source = Column(String(50))
    location = Column(String(50))
    dormer_type = Column(Enum("student", "reviewee", "working_professional", "other", name="dormer_type"))
    board_exam_type = Column(String(100))
    lease_term_months = Column(Integer)
    previous_stays = Column(JSON)
    notes = Column(Text, nullable=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey("staff.id"), nullable=True)
    updated_by = Column(UUID(as_uuid=True), ForeignKey("staff.id"), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    bed = relationship("Bed", back_populates="resident")
    billings = relationship("Billing", back_populates="resident", cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="resident", cascade="all, delete-orphan")
    ledger_entries = relationship("LedgerEntry", back_populates="resident", cascade="all, delete-orphan")
    inquiries = relationship("Inquiry", back_populates="resident")
    service_requests = relationship("ServiceRequest", back_populates="resident", cascade="all, delete-orphan")
    miscellaneous_transactions = relationship("MiscellaneousTransaction", back_populates="resident")
    deposits = relationship("Deposit", back_populates="resident", cascade="all, delete-orphan")
    billing_statements = relationship("BillingStatement", back_populates="resident", cascade="all, delete-orphan")

class Room(Base):
    __tablename__ = "rooms"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    room_number = Column(String(20), nullable=False, unique=True)
    display_room_number = Column(String(20))
    property_code = Column(String(10), nullable=False, default="DT01")
    building = Column(String(50))
    room_type = Column(String(50))
    capacity = Column(Integer, nullable=False)
    status = Column(Enum("available", "full", "maintenance", name="room_status"), nullable=False, default="available")
    beds = relationship("Bed", back_populates="room", cascade="all, delete-orphan")

class Deposit(Base):
    __tablename__ = "deposits"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    resident_id = Column(UUID(as_uuid=True), ForeignKey("residents.id", ondelete="CASCADE"), nullable=False)
    deposit_type = Column(Enum("advance", "security", "utility", name="deposit_type"), nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    receipt_number = Column(String(100))
    payment_date = Column(Date, default=datetime.utcnow)
    status = Column(Enum("paid", "refunded", "forfeited", "pending", name="deposit_status"), nullable=False, default="paid")
    refunded_amount = Column(Numeric(10, 2))
    notes = Column(Text)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    resident = relationship("Resident", back_populates="deposits")


class Bed(Base):
    __tablename__ = "beds"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    bed_code = Column(String(20), nullable=False, unique=True)
    room_id = Column(UUID(as_uuid=True), ForeignKey("rooms.id"), nullable=False)
    bed_number = Column(Integer, nullable=False)
    bed_type = Column(Enum("lower_bunk", "upper_bunk", "loft_type", name="bed_type"))
    rate_per_bed = Column(Numeric(10, 2), nullable=False)
    status = Column(Enum("available", "reserved", "occupied", name="bed_status"), nullable=False, default="available")
    room = relationship("Room", back_populates="beds")
    resident = relationship("Resident", back_populates="bed", uselist=False)

class Inquiry(Base):
    __tablename__ = "inquiries"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source = Column(Enum("facebook", "instagram", "tiktok", "walkin", "phone", "referral", "website", "email", name="inquiry_source"), nullable=False)
    external_id = Column(String(255))
    content = Column(Text)
    inquiry_type = Column(String(50), nullable=True)
    sentiment_score = Column(Numeric(3, 2))
    lead_score = Column(Integer)
    status = Column(Enum("new", "responded", "escalated", "converted", "closed", name="inquiry_status"), nullable=False, default="new")
    assigned_to = Column(UUID(as_uuid=True), ForeignKey("staff.id"))
    resident_id = Column(UUID(as_uuid=True), ForeignKey("residents.id"))
    property_code = Column(String(10), default="DT01")
    prospect_name = Column(String(255))
    prospect_phone = Column(String(20))
    prospect_email = Column(String(255))
    school = Column(String(255))
    course = Column(String(255))
    review_center = Column(String(255))
    exam_date = Column(Date)
    first_time_dormer = Column(Boolean, default=True)
    previous_dorm = Column(String(255))
    desired_move_in_date = Column(Date)
    length_of_stay = Column(String(50))
    inquiry_form_data = Column(JSON)
    response = Column(Text, nullable=True)
    campaign_id = Column(UUID(as_uuid=True), ForeignKey("qr_campaigns.id"), nullable=True)
    campaign_title = Column(String(255), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    resident = relationship("Resident", back_populates="inquiries")
    campaign = relationship("QrCampaign", back_populates="inquiries")


class QrCampaign(Base):
    __tablename__ = "qr_campaigns"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(255), nullable=False)
    property_code = Column(String(10), nullable=False, default="DT01")
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    notes = Column(Text, nullable=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey("staff.id"), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    inquiries = relationship("Inquiry", back_populates="campaign")
    creator = relationship("Staff")

class MeterReading(Base):
    __tablename__ = "meter_readings"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    building = Column(String(50), nullable=False)
    room_id = Column(UUID(as_uuid=True), ForeignKey("rooms.id"), nullable=True)
    resident_id = Column(UUID(as_uuid=True), ForeignKey("residents.id"), nullable=True)
    reading_date = Column(Date, nullable=False)
    electric_reading = Column(Numeric(10, 2))
    water_reading = Column(Numeric(10, 2))
    submitted_by = Column(UUID(as_uuid=True), ForeignKey("staff.id"))
    photo_url = Column(String(500))
    variance_pct = Column(Numeric(5, 2))
    status = Column(Enum("pending", "approved", "rejected", "estimated", name="meter_status"), nullable=False, default="pending")
    approved_by = Column(UUID(as_uuid=True), ForeignKey("staff.id"))
    room = relationship("Room")
    resident = relationship("Resident")

class MeterReadingImport(Base):
    __tablename__ = "meter_reading_imports"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    resident_id = Column(UUID(as_uuid=True), ForeignKey("residents.id"), nullable=False)
    building = Column(String(50), nullable=False)
    year = Column(Integer, nullable=False)
    month = Column(Integer, nullable=False)
    total_electric_usage = Column(Numeric(10, 2))
    peso_kwh = Column(Numeric(10, 4))
    sub_total = Column(Numeric(10, 2))
    total_with_vat = Column(Numeric(10, 2))
    elec_bill = Column(Numeric(10, 2))
    water_bill = Column(Numeric(10, 2))
    water_days = Column(Integer)
    water_rate = Column(Numeric(10, 2))
    misc_charges = Column(JSON)
    source_filename = Column(String(255))
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    resident = relationship("Resident")

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
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    resident = relationship("Resident", back_populates="billings")

class Payment(Base):
    __tablename__ = "payments"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    resident_id = Column(UUID(as_uuid=True), ForeignKey("residents.id"), nullable=False)
    billing_id = Column(UUID(as_uuid=True), ForeignKey("billings.id"))
    amount = Column(Numeric(10, 2), nullable=False)
    method = Column(Enum("gcash", "maya", "bank_transfer", "cash", "salary_deduction", name="payment_method"), nullable=False)
    gateway_ref = Column(String(255))
    status = Column(Enum("pending", "verified", "matched", "unreconciled", "refunded", name="payment_status"), nullable=False, default="pending")
    matched_at = Column(DateTime)
    sales_invoice_no = Column(String(50))
    receipt_no = Column(String(500))
    webhook_payload = Column(JSON)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
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
    password_hash = Column(String(255), nullable=True)
    managed_branch = Column(String(50), nullable=True)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    email_verified_at = Column(DateTime, nullable=True)
    last_login_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    verification_codes = relationship("VerificationCode", back_populates="staff", cascade="all, delete-orphan")
    password_resets = relationship("PasswordReset", back_populates="staff", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="staff", cascade="all, delete-orphan")

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
    extended_date = Column(Date)
    extended_by = Column(UUID(as_uuid=True), ForeignKey("staff.id"))
    extension_reason = Column(Text)
    is_end_of_month_flag = Column(Boolean, default=False)
    reason = Column(Text)
    forwarding_contact = Column(String(255))
    status = Column(Enum("requested", "clearance", "final_billing", "refund_pending", "completed", name="moveout_status"), nullable=False, default="requested")
    final_billing_id = Column(UUID(as_uuid=True), ForeignKey("billings.id"))
    refund_amount = Column(Numeric(10, 2))
    accounting_submitted_at = Column(DateTime)
    accounting_resolved_at = Column(DateTime)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    resident = relationship("Resident")


class ServiceRequest(Base):
    __tablename__ = "service_requests"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    resident_id = Column(UUID(as_uuid=True), ForeignKey("residents.id"), nullable=False)
    category = Column(Enum("plumbing", "electrical", "aircon", "pest_control", "wifi", "water_supply", "lock_key", "cleaning", "appliance", "other", name="service_category"), nullable=False)
    subject = Column(String(255), nullable=False)
    description = Column(Text)
    location = Column(String(100))
    priority = Column(Enum("low", "medium", "high", "urgent", name="service_priority"), nullable=False, default="medium")
    status = Column(Enum("submitted", "acknowledged", "in_progress", "resolved", "closed", name="service_status"), nullable=False, default="submitted")
    resolution_notes = Column(Text)
    assigned_to = Column(UUID(as_uuid=True), ForeignKey("staff.id"), nullable=True)
    submitted_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    resolved_at = Column(DateTime)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    resident = relationship("Resident", back_populates="service_requests")


class Announcement(Base):
    __tablename__ = "announcements"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    category = Column(Enum("general", "maintenance", "billing", "event", "emergency", name="announcement_category"), nullable=False)
    priority = Column(Enum("normal", "important", "urgent", name="announcement_priority"), nullable=False, default="normal")
    target_property = Column(String(10))
    target_room_numbers = Column(JSON)
    target_bed_types = Column(JSON)
    is_active = Column(Boolean, nullable=False, default=True)
    published_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)


class Faq(Base):
    __tablename__ = "faqs"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    category = Column(String(50), default="general")
    order_index = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)


class VerificationCode(Base):
    __tablename__ = "verification_codes"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    staff_id = Column(UUID(as_uuid=True), ForeignKey("staff.id", ondelete="CASCADE"), nullable=False)
    code = Column(String(10), nullable=False)
    purpose = Column(String(20), nullable=False)
    expires_at = Column(DateTime, nullable=False)
    used_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    staff = relationship("Staff", back_populates="verification_codes")


class PasswordReset(Base):
    __tablename__ = "password_resets"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    staff_id = Column(UUID(as_uuid=True), ForeignKey("staff.id", ondelete="CASCADE"), nullable=False)
    token_hash = Column(String(255), nullable=False)
    expires_at = Column(DateTime, nullable=False)
    used_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    staff = relationship("Staff", back_populates="password_resets")


class Notification(Base):
    __tablename__ = "notifications"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    staff_id = Column(UUID(as_uuid=True), ForeignKey("staff.id", ondelete="CASCADE"), nullable=False)
    type = Column(String(50), nullable=False)
    message = Column(Text, nullable=False)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    staff = relationship("Staff", back_populates="notifications")


class BillingStatement(Base):
    __tablename__ = "billing_statements"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    resident_id = Column(UUID(as_uuid=True), ForeignKey("residents.id", ondelete="CASCADE"), nullable=False)
    billing_period = Column(String(20), nullable=False)
    scope_type = Column(String(20), nullable=False, default="resident")  # resident, room, floor, property
    scope_target = Column(String(100), nullable=True)
    file_path = Column(String(500), nullable=False)
    file_name = Column(String(255), nullable=False)
    file_size = Column(Integer)
    metadata_json = Column(JSON)
    status = Column(String(20), nullable=False, default="generated")  # generated, sent, failed
    sent_at = Column(DateTime)
    sent_to = Column(String(255))
    email_status = Column(String(50))
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    resident = relationship("Resident", back_populates="billing_statements")


class MiscellaneousTransaction(Base):
    __tablename__ = "miscellaneous_transactions"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    resident_id = Column(UUID(as_uuid=True), ForeignKey("residents.id", ondelete="SET NULL"), nullable=True)
    branch = Column(String(50), nullable=True)
    room_id = Column(UUID(as_uuid=True), ForeignKey("rooms.id", ondelete="SET NULL"), nullable=True)
    description = Column(Text, nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    category = Column(String(50), default="other", nullable=False)
    transaction_date = Column(Date, nullable=False)
    status = Column(String(20), default="pending", nullable=False)
    recorded_by = Column(UUID(as_uuid=True), ForeignKey("staff.id"), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    resident = relationship("Resident", back_populates="miscellaneous_transactions")
    room = relationship("Room")
