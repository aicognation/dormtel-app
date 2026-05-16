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
    room_id: Optional[UUID] = None
    bed_number: Optional[int] = None

class ResidentOut(ResidentBase):
    id: UUID
    status: str
    created_at: datetime
    class Config:
        from_attributes = True

class InquiryBase(BaseModel):
    source: str
    content: Optional[str] = None

class InquiryCreate(InquiryBase):
    external_id: Optional[str] = None

class InquiryOut(InquiryBase):
    id: UUID
    status: str
    sentiment_score: Optional[Decimal] = None
    lead_score: Optional[int] = None
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
    created_at: datetime
    class Config:
        from_attributes = True

class MeterReadingBase(BaseModel):
    building: str
    reading_date: date
    electric_reading: Optional[Decimal] = None
    water_reading: Optional[Decimal] = None

class MeterReadingCreate(MeterReadingBase):
    pass

class MeterReadingOut(MeterReadingBase):
    id: UUID
    status: str
    variance_pct: Optional[Decimal] = None
    class Config:
        from_attributes = True

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
    reason: Optional[str] = None
    forwarding_contact: Optional[str] = None

class MoveOutCreate(MoveOutBase):
    resident_id: UUID

class MoveOutOut(MoveOutBase):
    id: UUID
    resident_id: UUID
    status: str
    created_at: datetime
    class Config:
        from_attributes = True
