from pydantic import BaseModel, EmailStr, Field, field_validator
from datetime import date, datetime
from typing import Optional, List, Literal
from decimal import Decimal
from uuid import UUID
import re

from app.utils.validators import (
    parse_date_flexible,
    empty_string_to_none,
    normalize_enum_string,
    parse_decimal,
    parse_bool,
)

_EMAIL_RE = re.compile(r'^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$')

class ResidentBase(BaseModel):
    full_name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    monthly_rate: Decimal = Field(..., ge=0)

    @field_validator('email')
    @classmethod
    def validate_email(cls, v):
        if v is None or v == '':
            return None
        v = v.strip()
        if not _EMAIL_RE.match(v):
            raise ValueError(f'Invalid email format: {v}')
        return v

    @field_validator('monthly_rate', mode='before')
    @classmethod
    def parse_monthly_rate(cls, v):
        return parse_decimal(v)

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
    status: Optional[str] = "prospect"
    move_in_date: Optional[date] = None
    move_out_date: Optional[date] = None
    contract_end_date: Optional[date] = None
    notes: Optional[str] = None

    @field_validator('exam_date', 'move_in_date', 'move_out_date', 'contract_end_date', mode='before')
    @classmethod
    def parse_dates(cls, v):
        return parse_date_flexible(v)

    @field_validator('bed_id', mode='before')
    @classmethod
    def parse_bed_id(cls, v):
        return empty_string_to_none(v)

    @field_validator('is_first_time_dormer', mode='before')
    @classmethod
    def parse_bool(cls, v):
        return parse_bool(v)

    @field_validator('dormer_type', 'status', mode='before')
    @classmethod
    def normalize_enums(cls, v):
        return normalize_enum_string(v)

    @field_validator('lease_term_months', mode='before')
    @classmethod
    def parse_lease_term(cls, v):
        return empty_string_to_none(v)

    @field_validator('previous_stays', mode='before')
    @classmethod
    def parse_previous_stays(cls, v):
        return empty_string_to_none(v)

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
    company_name: Optional[str] = None
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
    warnings: Optional[List[str]] = None
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
    property_code: Optional[str] = None
    campaign_id: Optional[UUID] = None
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

    @field_validator('exam_date', 'desired_move_in_date', mode='before')
    @classmethod
    def parse_dates(cls, v):
        return parse_date_flexible(v)

    @field_validator('resident_id', 'campaign_id', mode='before')
    @classmethod
    def parse_optional_uuids(cls, v):
        return empty_string_to_none(v)

    @field_validator('first_time_dormer', mode='before')
    @classmethod
    def parse_bool(cls, v):
        return parse_bool(v)

    @field_validator('inquiry_form_data', mode='before')
    @classmethod
    def parse_form_data(cls, v):
        return empty_string_to_none(v)

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
    inquiry_form_data: Optional[dict] = None
    campaign_id: Optional[UUID] = None
    campaign_title: Optional[str] = None
    created_at: datetime
    class Config:
        from_attributes = True

class QrCampaignCreate(BaseModel):
    title: str = Field(..., min_length=2, max_length=255)
    property_code: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    notes: Optional[str] = None

    @field_validator('start_date', 'end_date', mode='before')
    @classmethod
    def parse_dates(cls, v):
        return parse_date_flexible(v)

class QrCampaignOut(BaseModel):
    id: UUID
    title: str
    property_code: str
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    notes: Optional[str] = None
    created_by: Optional[UUID] = None
    created_by_name: Optional[str] = None
    created_at: datetime
    leads_count: int = 0
    new_count: int = 0
    converted_count: int = 0
    last_lead_at: Optional[datetime] = None
    class Config:
        from_attributes = True

class QrCampaignPublic(BaseModel):
    id: UUID
    title: str
    property_code: str
    start_date: Optional[date] = None
    end_date: Optional[date] = None
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
    previous_balance: Optional[Decimal] = Field(default=Decimal("0"), ge=0)
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
    method: Literal["gcash", "maya", "bank_transfer", "cash", "salary_deduction"]

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

    @field_validator('reading_date', mode='before')
    @classmethod
    def parse_reading_date(cls, v):
        return parse_date_flexible(v)

    @field_validator('room_id', 'resident_id', mode='before')
    @classmethod
    def parse_optional_uuids(cls, v):
        return empty_string_to_none(v)

    @field_validator('electric_reading', 'water_reading', mode='before')
    @classmethod
    def parse_optional_decimals(cls, v):
        return empty_string_to_none(v)

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
    # Import summary data (from MeterReadingImport)
    total_electric_usage: Optional[Decimal] = None
    peso_kwh: Optional[Decimal] = None
    sub_total: Optional[Decimal] = None
    total_with_vat: Optional[Decimal] = None
    elec_bill: Optional[Decimal] = None
    water_bill: Optional[Decimal] = None
    water_days: Optional[int] = None
    water_rate: Optional[Decimal] = None
    misc_charges: Optional[dict] = None
    source_filename: Optional[str] = None


class VacantBedRow(BaseModel):
    room_number: str
    bed_code: str
    bed_letter: Optional[str] = None
    bed_number: int = 0


class ImportInfo(BaseModel):
    source_filename: Optional[str] = None
    imported_at: Optional[datetime] = None
    resident_count: int = 0


class MeterReadingDailyGridOut(BaseModel):
    year: int
    month: int
    days_in_month: int
    residents: list[MeterReadingDailyRow]
    vacant_beds: list[VacantBedRow] = []
    import_info: Optional[ImportInfo] = None
    water_config: dict

class MeterReadingUploadResult(BaseModel):
    imported: int
    skipped: int
    errors: list[str]
    message: str

class MeterReadingDailySheetResult(BaseModel):
    building: str
    year: int
    month: int
    residents_imported: int
    daily_readings_imported: int
    errors: list[str]
    message: str

class BillingImportStatusOut(BaseModel):
    billing_period: str
    building: Optional[str] = None
    has_imports: bool
    import_count: int
    total_imported_water: Optional[Decimal] = None
    total_imported_misc: Optional[Decimal] = None
    total_imported_electric: Optional[Decimal] = None
    source_filename: Optional[str] = None

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

    @field_validator('requested_date', 'actual_date', 'extended_date', mode='before')
    @classmethod
    def parse_dates(cls, v):
        return parse_date_flexible(v)
    forwarding_contact: Optional[str] = None

class MoveOutCreate(MoveOutBase):
    resident_id: UUID

class MoveOutOut(MoveOutBase):
    id: UUID
    resident_id: UUID
    resident_name: Optional[str] = None
    resident_email: Optional[str] = None
    resident_phone: Optional[str] = None
    id_type: Optional[str] = None
    id_number: Optional[str] = None
    address: Optional[str] = None
    school: Optional[str] = None
    course: Optional[str] = None
    review_center: Optional[str] = None
    company_name: Optional[str] = None
    exam_date: Optional[date] = None
    source: Optional[str] = None
    location: Optional[str] = None
    dormer_type: Optional[str] = None
    board_exam_type: Optional[str] = None
    lease_term_months: Optional[int] = None
    monthly_rate: Optional[Decimal] = None
    deposit_paid: Optional[Decimal] = None
    contract_end_date: Optional[date] = None
    is_first_time_dormer: Optional[bool] = None
    notes: Optional[str] = None
    room_number: Optional[str] = None
    bed_code: Optional[str] = None
    bed_type: Optional[str] = None
    building: Optional[str] = None
    room_type: Optional[str] = None
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

    @field_validator('extended_date', mode='before')
    @classmethod
    def parse_extended_date(cls, v):
        return parse_date_flexible(v)


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
    total_listed_residents: int = 0
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
    category: Literal["plumbing", "electrical", "aircon", "pest_control", "wifi", "water_supply", "lock_key", "cleaning", "appliance", "other"]
    subject: str
    description: Optional[str] = None
    location: Optional[str] = None
    priority: Literal["low", "medium", "high", "urgent"] = "medium"

class ServiceRequestCreate(ServiceRequestBase):
    pass

class ServiceRequestAdminCreate(ServiceRequestBase):
    resident_id: UUID

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
    method: Literal["gcash", "maya", "bank_transfer", "cash", "salary_deduction"]
    gateway_ref: Optional[str] = None
    proof_of_payment: Optional[str] = None

    @field_validator('billing_id', mode='before')
    @classmethod
    def parse_billing_id(cls, v):
        return empty_string_to_none(v)

    @field_validator('amount', mode='before')
    @classmethod
    def parse_amount(cls, v):
        return parse_decimal(v)

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
    db_schema: Optional[str] = "demo"

class StaffLoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    staff: "StaffOut"
    requires_property_selection: bool = True


class PropertyOut(BaseModel):
    code: str
    name: str
    address: Optional[str] = None
    is_active: bool

    class Config:
        from_attributes = True


class PropertySelectRequest(BaseModel):
    property_code: str


class PropertyLoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    property_code: str
    property_name: str

class StaffCreate(BaseModel):
    full_name: str
    email: EmailStr
    phone: Optional[str] = None
    role: str = "admin"
    managed_branch: Optional[str] = None
    password: Optional[str] = None

    @field_validator('role', mode='before')
    @classmethod
    def normalize_role(cls, v):
        return normalize_enum_string(v)

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

    @field_validator('role', mode='before')
    @classmethod
    def normalize_role(cls, v):
        return normalize_enum_string(v)

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
    email: Optional[str] = None
    phone: Optional[str] = None
    id_type: Optional[str] = None
    id_number: Optional[str] = None
    status: Optional[str] = None
    bed_id: Optional[UUID] = None
    address: Optional[str] = None
    school: Optional[str] = None
    course: Optional[str] = None
    review_center: Optional[str] = None
    company_name: Optional[str] = None
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

    @field_validator('exam_date', 'move_in_date', 'move_out_date', 'contract_end_date', mode='before')
    @classmethod
    def parse_dates(cls, v):
        return parse_date_flexible(v)

    @field_validator('bed_id', mode='before')
    @classmethod
    def parse_bed_id(cls, v):
        return empty_string_to_none(v)

    @field_validator('is_first_time_dormer', mode='before')
    @classmethod
    def parse_bool(cls, v):
        return parse_bool(v)

    @field_validator('dormer_type', 'status', mode='before')
    @classmethod
    def normalize_enums(cls, v):
        return normalize_enum_string(v)

    @field_validator('monthly_rate', mode='before')
    @classmethod
    def parse_monthly_rate(cls, v):
        return empty_string_to_none(v)

    @field_validator('lease_term_months', mode='before')
    @classmethod
    def parse_lease_term(cls, v):
        return empty_string_to_none(v)


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


# --- Billing Statement Schemas ---

class BillingStatementGenerateRequest(BaseModel):
    billing_period: str
    scope_type: str = "resident"  # resident, room, floor, property
    scope_target: Optional[str] = None  # resident_id, room_id, floor prefix, building/property_code
    total_water_bill: Optional[Decimal] = Field(default=Decimal("0"), ge=0)
    other_charges: Optional[Decimal] = Field(default=Decimal("0"), ge=0)
    regenerate: bool = False
    auto_send_email: bool = False
    email_subject: Optional[str] = None
    email_body: Optional[str] = None

    @field_validator('total_water_bill', 'other_charges', mode='before')
    @classmethod
    def parse_decimals(cls, v):
        if v is None or v == "":
            return Decimal("0")
        return parse_decimal(v)


class BillingStatementRow(BaseModel):
    statement_id: UUID
    resident_id: UUID
    resident_name: Optional[str] = None
    billing_period: str
    scope_type: str
    scope_target: Optional[str] = None
    file_name: str
    file_path: str
    file_size: Optional[int] = None
    status: str
    sent_to: Optional[str] = None
    sent_at: Optional[datetime] = None
    email_status: Optional[str] = None
    created_at: datetime
    total_amount: Optional[Decimal] = None


class BillingStatementGenerateResponse(BaseModel):
    generated: int
    skipped: int
    errors: List[str]
    statements: List[BillingStatementRow]


# --- Miscellaneous Transaction Schemas ---

class MiscellaneousTransactionBase(BaseModel):
    description: str
    amount: Decimal = Field(..., ge=0)
    category: str = "other"
    transaction_date: date
    status: str = "pending"

    @field_validator('transaction_date', mode='before')
    @classmethod
    def parse_transaction_date(cls, v):
        return parse_date_flexible(v)

    @field_validator('amount', mode='before')
    @classmethod
    def parse_amount(cls, v):
        return parse_decimal(v)

class MiscellaneousTransactionCreate(MiscellaneousTransactionBase):
    resident_id: Optional[UUID] = None
    branch: Optional[str] = None
    room_id: Optional[UUID] = None

    @field_validator('resident_id', 'room_id', mode='before')
    @classmethod
    def parse_optional_uuids(cls, v):
        return empty_string_to_none(v)

class MiscellaneousTransactionUpdate(BaseModel):
    description: Optional[str] = None
    amount: Optional[Decimal] = Field(default=None, ge=0)
    category: Optional[str] = None
    transaction_date: Optional[date] = None
    status: Optional[str] = None
    resident_id: Optional[UUID] = None
    branch: Optional[str] = None
    room_id: Optional[UUID] = None

    @field_validator('transaction_date', mode='before')
    @classmethod
    def parse_transaction_date(cls, v):
        return parse_date_flexible(v)

    @field_validator('amount', mode='before')
    @classmethod
    def parse_amount(cls, v):
        return empty_string_to_none(v)

    @field_validator('resident_id', 'room_id', mode='before')
    @classmethod
    def parse_optional_uuids(cls, v):
        return empty_string_to_none(v)

class MiscellaneousTransactionOut(MiscellaneousTransactionBase):
    id: UUID
    resident_id: Optional[UUID] = None
    branch: Optional[str] = None
    room_id: Optional[UUID] = None
    recorded_by: Optional[UUID] = None
    created_at: datetime
    class Config:
        from_attributes = True


# --- Template Validation Schemas ---

class TemplateValidationIssue(BaseModel):
    severity: str          # "error" | "warning" | "info"
    code: str              # machine-readable e.g. "MISSING_REQUIRED_COLUMN"
    message: str           # human-readable, actionable
    sheet: Optional[str] = None
    column: Optional[str] = None

class SheetPreview(BaseModel):
    name: str
    header_row_index: Optional[int] = None
    detected_headers: List[str] = []
    missing_headers: List[str] = []
    extra_headers: List[str] = []
    data_row_count: int = 0
    sample_rows: List[list] = []
    date_column_count: Optional[int] = None
    date_range_start: Optional[str] = None
    date_range_end: Optional[str] = None
    detected_month: Optional[str] = None
    detected_year: Optional[int] = None
    has_bed_column: Optional[bool] = None
    format_variant: Optional[str] = None
    misc_columns: List[str] = []
    has_total_usage: Optional[bool] = None
    has_water_bill: Optional[bool] = None

class TemplateValidationResponse(BaseModel):
    upload_type: str                       # "standard" | "daily_sheet"
    file_name: str
    file_size_bytes: int
    overall_status: str                    # "valid" | "warnings" | "invalid"
    issues: List[TemplateValidationIssue] = []
    sheets: List[SheetPreview] = []
    summary: dict = {}


# Resolve forward reference for StaffLoginResponse
StaffLoginResponse.model_rebuild()
