from pydantic import BaseModel, EmailStr, Field
from datetime import date, datetime
from typing import Optional, List
from decimal import Decimal
from uuid import UUID

class ResidentBase(BaseModel):
    full_name: str
    email: EmailStr
    phone: str
    monthly_rate: Decimal = Field(..., ge=0)

class ResidentCreate(ResidentBase):
    id_type: Optional[str] = None
    id_number: Optional[str] = None
    bed_id: Optional[UUID] = None
    address: Optional[str] = None
    school: Optional[str] = None
    course: Optional[str] = None
    review_center: Optional[str] = None
    exam_date: Optional[date] = None
    is_first_time_dormer: Optional[bool] = True
    source: Optional[str] = None
    location: Optional[str] = None
    dormer_type: Optional[str] = None
    board_exam_type: Optional[str] = None
    lease_term_months: Optional[int] = None
    previous_stays: Optional[list] = None

class ResidentOut(ResidentBase):
    id: UUID
    status: str
    bed_id: Optional[UUID] = None
    id_type: Optional[str] = None
    id_number: Optional[str] = None
    address: Optional[str] = None
    school: Optional[str] = None
    course: Optional[str] = None
    review_center: Optional[str] = None
    exam_date: Optional[date] = None
    is_first_time_dormer: Optional[bool] = True
    source: Optional[str] = None
    location: Optional[str] = None
    dormer_type: Optional[str] = None
    board_exam_type: Optional[str] = None
    lease_term_months: Optional[int] = None
    previous_stays: Optional[list] = None
    move_in_date: Optional[date] = None
    move_out_date: Optional[date] = None
    contract_end_date: Optional[date] = None
    deposit_paid: Optional[Decimal] = None
    created_at: datetime
    class Config:
        from_attributes = True

class ResidentMiniOut(BaseModel):
    id: UUID
    full_name: str
    status: str
    class Config:
        from_attributes = True

class InquiryBase(BaseModel):
    source: str
    content: Optional[str] = None

class InquiryAdminResponse(BaseModel):
    response: str

class InquiryCreate(InquiryBase):
    resident_id: Optional[UUID] = None
    inquiry_type: Optional[str] = None
    external_id: Optional[str] = None
    property_code: Optional[str] = "DT01"
    prospect_name: Optional[str] = None
    prospect_phone: Optional[str] = None
    prospect_email: Optional[str] = None
    school: Optional[str] = None
    course: Optional[str] = None
    review_center: Optional[str] = None
    exam_date: Optional[date] = None
    first_time_dormer: Optional[bool] = True
    previous_dorm: Optional[str] = None
    desired_move_in_date: Optional[date] = None
    length_of_stay: Optional[str] = None
    inquiry_form_data: Optional[dict] = None

class InquiryOut(InquiryBase):
    id: UUID
    status: str
    inquiry_type: Optional[str] = None
    property_code: Optional[str] = None
    prospect_name: Optional[str] = None
    prospect_phone: Optional[str] = None
    prospect_email: Optional[str] = None
    school: Optional[str] = None
    course: Optional[str] = None
    review_center: Optional[str] = None
    exam_date: Optional[date] = None
    first_time_dormer: Optional[bool] = True
    previous_dorm: Optional[str] = None
    desired_move_in_date: Optional[date] = None
    length_of_stay: Optional[str] = None
    sentiment_score: Optional[Decimal] = None
    lead_score: Optional[int] = None
    response: Optional[str] = None
    created_at: datetime
    class Config:
        from_attributes = True

class BillingBase(BaseModel):
    billing_period: str
    rent_amount: Decimal = Field(..., ge=0)
    electric_charge: Optional[Decimal] = Field(default=Decimal("0"), ge=0)
    water_charge: Optional[Decimal] = Field(default=Decimal("0"), ge=0)
    other_charges: Optional[Decimal] = Field(default=Decimal("0"), ge=0)

class BillingCreate(BillingBase):
    resident_id: UUID

class BillingOut(BillingBase):
    id: UUID
    resident_id: UUID
    total_amount: Decimal
    status: str
    created_at: datetime
    class Config:
        from_attributes = True

class BillingWithResidentOut(BillingOut):
    resident_name: Optional[str] = None
    bed_code: Optional[str] = None
    room_number: Optional[str] = None
    class Config:
        from_attributes = True

class PaymentBase(BaseModel):
    amount: Decimal = Field(..., ge=0)
    method: str

class PaymentCreate(PaymentBase):
    resident_id: UUID
    billing_id: Optional[UUID] = None

class PaymentOut(PaymentBase):
    id: UUID
    resident_id: UUID
    status: str
    gateway_ref: Optional[str] = None
    receipt_no: Optional[str] = None
    sales_invoice_no: Optional[str] = None
    billing_id: Optional[UUID] = None
    created_at: datetime
    class Config:
        from_attributes = True

class LedgerBillingRow(BaseModel):
    id: UUID
    billing_period: str
    rent_amount: Decimal
    electric_charge: Optional[Decimal] = None
    water_charge: Optional[Decimal] = None
    other_charges: Optional[Decimal] = None
    total_amount: Decimal
    status: str
    payments_total: Decimal = Decimal("0")
    balance_due: Decimal = Decimal("0")
    created_at: datetime
    class Config:
        from_attributes = True

class LedgerPaymentRow(BaseModel):
    id: UUID
    amount: Decimal
    method: str
    gateway_ref: Optional[str] = None
    receipt_no: Optional[str] = None
    sales_invoice_no: Optional[str] = None
    status: str
    created_at: datetime
    class Config:
        from_attributes = True

class DormerLedgerOut(BaseModel):
    resident_id: UUID
    resident_name: str
    room_number: Optional[str] = None
    bed_code: Optional[str] = None
    bed_letter: Optional[str] = None
    room_type: Optional[str] = None
    bed_type: Optional[str] = None
    monthly_rate: Decimal
    move_in_date: Optional[date] = None
    move_out_date: Optional[date] = None
    contract_end_date: Optional[date] = None
    deposit_paid: Optional[Decimal] = None
    total_billed: Decimal = Decimal("0")
    total_paid: Decimal = Decimal("0")
    balance_due: Decimal = Decimal("0")
    billings: list[LedgerBillingRow] = []
    payments: list[LedgerPaymentRow] = []
    class Config:
        from_attributes = True

class DormerLedgerSummaryOut(BaseModel):
    resident_id: UUID
    resident_name: str
    room_number: Optional[str] = None
    bed_code: Optional[str] = None
    monthly_rate: Decimal
    total_billed: Decimal = Decimal("0")
    total_paid: Decimal = Decimal("0")
    balance_due: Decimal = Decimal("0")
    status: str = "current"
    class Config:
        from_attributes = True

class MeterReadingBase(BaseModel):
    building: str
    room_id: Optional[UUID] = None
    resident_id: Optional[UUID] = None
    reading_date: date
    electric_reading: Optional[Decimal] = None
    water_reading: Optional[Decimal] = None

class MeterReadingCreate(MeterReadingBase):
    pass

class MeterReadingOut(MeterReadingBase):
    id: UUID
    status: str
    variance_pct: Optional[Decimal] = None
    room_number: Optional[str] = None
    resident_name: Optional[str] = None
    bed_code: Optional[str] = None
    class Config:
        from_attributes = True

class MeterReadingDailyCell(BaseModel):
    reading_id: Optional[UUID] = None
    electric_reading: Optional[Decimal] = None
    water_reading: Optional[Decimal] = None
    status: Optional[str] = None

class MeterReadingDailyRow(BaseModel):
    resident_id: UUID
    resident_name: str
    room_number: Optional[str] = None
    bed_code: Optional[str] = None
    bed_letter: Optional[str] = None
    monthly_rate: Optional[Decimal] = None
    move_in_date: Optional[date] = None
    move_out_date: Optional[date] = None
    days_in_month: int = 0
    readings: dict[str, MeterReadingDailyCell] = {}

class MeterReadingDailyGridOut(BaseModel):
    year: int
    month: int
    days_in_month: int
    residents: list[MeterReadingDailyRow]
    water_config: dict

class CheckpointOut(BaseModel):
    id: UUID
    checkpoint_id: str
    stage: str
    status: str
    sla_deadline: datetime
    class Config:
        from_attributes = True

class MoveOutBase(BaseModel):
    requested_date: date
    actual_date: Optional[date] = None
    extended_date: Optional[date] = None
    extension_reason: Optional[str] = None
    reason: Optional[str] = None
    forwarding_contact: Optional[str] = None

class MoveOutCreate(MoveOutBase):
    resident_id: UUID

class MoveOutOut(MoveOutBase):
    id: UUID
    resident_id: UUID
    resident_name: Optional[str] = None
    room_number: Optional[str] = None
    bed_code: Optional[str] = None
    status: str
    is_end_of_month_flag: Optional[bool] = False
    refund_amount: Optional[Decimal] = None
    final_billing_id: Optional[UUID] = None
    created_at: datetime
    class Config:
        from_attributes = True

class MoveOutExtendRequest(BaseModel):
    extended_date: date
    extension_reason: Optional[str] = None


# --- Bed & Room Schemas ---

class BedOut(BaseModel):
    id: UUID
    bed_code: str
    bed_number: int
    bed_type: Optional[str] = None
    rate_per_bed: Decimal
    status: str
    resident: Optional[ResidentMiniOut] = None
    class Config:
        from_attributes = True

class RoomOut(BaseModel):
    id: UUID
    room_number: str
    display_room_number: Optional[str] = None
    property_code: str
    building: Optional[str] = None
    room_type: Optional[str] = None
    capacity: int
    status: str
    class Config:
        from_attributes = True

class RoomWithBedsOut(RoomOut):
    beds: List[BedOut] = []
    occupied_count: int = 0
    reserved_count: int = 0
    available_count: int = 0
    min_rate: Optional[Decimal] = None
    max_rate: Optional[Decimal] = None
    class Config:
        from_attributes = True


# --- Dashboard Schemas ---

class DashboardStatsOut(BaseModel):
    revenue: Decimal
    dormers: int
    inquiries: int
    reservations: int
    pending_bills: Decimal
    pending_bills_count: int
    scheduled_moveins: int
    scheduled_moveouts: int

class DashboardEventResident(BaseModel):
    id: UUID
    full_name: str
    bed_code: str

class DashboardEventOut(BaseModel):
    date: date
    count: int
    residents: List[DashboardEventResident]


# --- Tenant Portal Schemas ---

class TenantLoginRequest(BaseModel):
    email: Optional[str] = None
    phone: Optional[str] = None
    bed_code: Optional[str] = None

class TenantLoginResponse(BaseModel):
    id: UUID
    full_name: str
    email: str
    phone: str
    status: str
    room_number: Optional[str] = None
    building: Optional[str] = None
    bed_code: Optional[str] = None
    monthly_rate: Decimal
    move_in_date: Optional[date] = None
    contract_end_date: Optional[date] = None
    deposit_paid: Optional[Decimal] = None

class TenantDashboardResponse(BaseModel):
    resident_name: str
    room_number: Optional[str] = None
    building: Optional[str] = None
    bed_code: Optional[str] = None
    outstanding_balance: Decimal
    open_requests: int
    pending_billings_count: int = 0
    paid_billings_count: int = 0
    total_requests_submitted: int = 0
    total_responses_received: int = 0
    months_to_end_contract: Optional[int] = None
    current_billing_period: Optional[str] = None
    current_billing_total: Optional[Decimal] = None
    current_billing_status: Optional[str] = None
    last_payment_date: Optional[datetime] = None
    last_payment_amount: Optional[Decimal] = None
    announcements: list = []

class ServiceRequestBase(BaseModel):
    category: str
    subject: str
    description: Optional[str] = None
    location: Optional[str] = None
    priority: str = "medium"

class ServiceRequestCreate(ServiceRequestBase):
    pass

class ServiceRequestOut(ServiceRequestBase):
    id: UUID
    resident_id: UUID
    status: str
    resolution_notes: Optional[str] = None
    assigned_to: Optional[UUID] = None
    submitted_at: datetime
    resolved_at: Optional[datetime] = None
    created_at: datetime
    class Config:
        from_attributes = True

class ServiceRequestWithResidentOut(ServiceRequestOut):
    resident_name: Optional[str] = None
    class Config:
        from_attributes = True

class ServiceRequestStatusUpdate(BaseModel):
    status: str
    resolution_notes: Optional[str] = None

class ServiceRequestAssign(BaseModel):
    assigned_to: UUID

class AnnouncementOut(BaseModel):
    id: UUID
    title: str
    content: str
    category: str
    priority: str
    target_property: Optional[str] = None
    target_room_numbers: Optional[list] = None
    target_bed_types: Optional[list] = None
    published_at: datetime
    class Config:
        from_attributes = True


# --- FAQ Schemas ---

class FaqBase(BaseModel):
    question: str
    answer: str
    category: Optional[str] = "general"
    order_index: Optional[int] = 0

class FaqCreate(FaqBase):
    pass

class FaqOut(FaqBase):
    id: UUID
    is_active: bool
    created_at: datetime
    class Config:
        from_attributes = True


# --- Monitoring Report Schemas ---

class DailyMonitoringRow(BaseModel):
    date: date
    nob: int
    nod: int
    target_occupancy: int
    actual_occupancy: int
    variance: int
    occupancy_rate: Decimal
    room_sales_target: Decimal
    room_sales_actual: Decimal
    misc_sales_actual: Decimal
    total_sales_actual: Decimal

class MonitoringReportResponse(BaseModel):
    property_code: str
    month: str
    daily_rows: List[DailyMonitoringRow]
    summary: dict

class TenantPayRequest(BaseModel):
    billing_id: Optional[UUID] = None
    amount: Decimal = Field(..., ge=0)
    method: str

class TenantProfileResponse(BaseModel):
    id: UUID
    full_name: str
    email: str
    phone: str
    id_type: Optional[str] = None
    id_number: Optional[str] = None
    status: str
    room_number: Optional[str] = None
    building: Optional[str] = None
    bed_code: Optional[str] = None
    monthly_rate: Decimal
    deposit_paid: Optional[Decimal] = None
    move_in_date: Optional[date] = None
    contract_end_date: Optional[date] = None
    ledger_balance: Decimal = Decimal("0")


# --- Auth Schemas ---

class StaffLoginRequest(BaseModel):
    email: EmailStr
    password: str

class StaffLoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    staff: "StaffOut"

class StaffCreate(BaseModel):
    full_name: str
    email: EmailStr
    phone: Optional[str] = None
    role: str = "admin"
    managed_branch: Optional[str] = None
    password: Optional[str] = None

class StaffOut(BaseModel):
    id: UUID
    full_name: str
    email: str
    role: str
    phone: Optional[str] = None
    managed_branch: Optional[str] = None
    is_active: bool
    is_verified: bool
    last_login_at: Optional[datetime] = None
    created_at: datetime
    class Config:
        from_attributes = True

class StaffUpdate(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    role: Optional[str] = None
    managed_branch: Optional[str] = None
    is_active: Optional[bool] = None

class PasswordResetRequest(BaseModel):
    email: EmailStr

class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str = Field(..., min_length=8)

class VerificationCodeRequest(BaseModel):
    staff_id: UUID

class VerificationCodeVerify(BaseModel):
    staff_id: UUID
    code: str

class NotificationOut(BaseModel):
    id: UUID
    type: str
    message: str
    is_read: bool
    created_at: datetime
    class Config:
        from_attributes = True


# --- Residents List Schemas ---

class ResidentListOut(ResidentOut):
    notes: Optional[str] = None
    created_by: Optional[UUID] = None
    updated_by: Optional[UUID] = None
    bed_code: Optional[str] = None
    bed_type: Optional[str] = None
    room_number: Optional[str] = None
    building: Optional[str] = None
    room_type: Optional[str] = None
    deposits: Optional[list] = None
    class Config:
        from_attributes = True

class ResidentUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    id_type: Optional[str] = None
    id_number: Optional[str] = None
    status: Optional[str] = None
    bed_id: Optional[UUID] = None
    address: Optional[str] = None
    school: Optional[str] = None
    course: Optional[str] = None
    review_center: Optional[str] = None
    exam_date: Optional[date] = None
    is_first_time_dormer: Optional[bool] = None
    source: Optional[str] = None
    location: Optional[str] = None
    dormer_type: Optional[str] = None
    board_exam_type: Optional[str] = None
    lease_term_months: Optional[int] = None
    notes: Optional[str] = None
    move_in_date: Optional[date] = None
    move_out_date: Optional[date] = None
    contract_end_date: Optional[date] = None
    monthly_rate: Optional[Decimal] = None


# --- Deposit Schemas ---

class DepositBase(BaseModel):
    deposit_type: str
    amount: Decimal = Field(..., ge=0)
    receipt_number: Optional[str] = None
    payment_date: Optional[date] = None
    status: Optional[str] = "paid"
    notes: Optional[str] = None

class DepositCreate(DepositBase):
    resident_id: UUID

class DepositOut(DepositBase):
    id: UUID
    resident_id: UUID
    refunded_amount: Optional[Decimal] = None
    created_at: datetime
    class Config:
        from_attributes = True


# --- Miscellaneous Transaction Schemas ---

class MiscellaneousTransactionBase(BaseModel):
    description: str
    amount: Decimal = Field(..., ge=0)
    category: str = "other"
    transaction_date: date
    status: str = "pending"

class MiscellaneousTransactionCreate(MiscellaneousTransactionBase):
    resident_id: Optional[UUID] = None
    branch: Optional[str] = None
    room_id: Optional[UUID] = None

class MiscellaneousTransactionOut(MiscellaneousTransactionBase):
    id: UUID
    resident_id: Optional[UUID] = None
    branch: Optional[str] = None
    room_id: Optional[UUID] = None
    recorded_by: Optional[UUID] = None
    created_at: datetime
    class Config:
        from_attributes = True


# Resolve forward reference for StaffLoginResponse
StaffLoginResponse.model_rebuild()
