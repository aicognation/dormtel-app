from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID
from typing import Optional
import uuid

from pydantic import BaseModel, EmailStr

from app.database import get_db
from app import models, schemas

router = APIRouter()


class ReservationCreateRequest(BaseModel):
    full_name: str
    email: EmailStr
    phone: str
    monthly_rate: Decimal
    id_type: Optional[str] = None
    id_number: Optional[str] = None
    room_id: Optional[UUID] = None
    bed_number: Optional[int] = None
    move_in_date: Optional[date] = None


class RoomOut(BaseModel):
    id: UUID
    room_number: str
    building: Optional[str] = None
    capacity: int
    occupied_beds: int
    rate_per_bed: Decimal
    status: str

    class Config:
        from_attributes = True


@router.post("/reservations", response_model=schemas.ResidentOut, status_code=status.HTTP_201_CREATED)
async def create_reservation(payload: ReservationCreateRequest, db: AsyncSession = Depends(get_db)):
    room = None

    if payload.room_id:
        result = await db.execute(select(models.Room).where(models.Room.id == payload.room_id))
        room = result.scalar_one_or_none()
        if not room:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Room not found")
        if room.occupied_beds >= room.capacity:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Room is full")
    else:
        result = await db.execute(
            select(models.Room)
            .where(models.Room.status == "available")
            .order_by(models.Room.room_number)
        )
        room = result.scalar_one_or_none()
        if not room:
            result = await db.execute(
                select(models.Room)
                .where(models.Room.occupied_beds < models.Room.capacity)
                .order_by(models.Room.room_number)
            )
            room = result.scalar_one_or_none()
        if not room:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="No available rooms")

    assigned_bed = payload.bed_number
    if assigned_bed is None:
        assigned_bed = room.occupied_beds + 1

    room.occupied_beds += 1
    if room.occupied_beds >= room.capacity:
        room.status = "full"

    resident = models.Resident(
        id=uuid.uuid4(),
        full_name=payload.full_name,
        email=payload.email,
        phone=payload.phone,
        id_type=payload.id_type,
        id_number=payload.id_number,
        status="reserved",
        room_id=room.id,
        bed_number=assigned_bed,
        move_in_date=payload.move_in_date,
        monthly_rate=payload.monthly_rate,
        deposit_paid=Decimal("0"),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(resident)
    await db.commit()
    await db.refresh(resident)
    return resident


@router.post("/reservations/{resident_id}/payment-link", response_model=schemas.BillingOut)
async def generate_payment_link(resident_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(models.Resident).where(models.Resident.id == resident_id))
    resident = result.scalar_one_or_none()
    if not resident:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resident not found")
    if resident.status != "reserved":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Resident is not in reserved status")

    mock_link = f"https://pay.dormtel.ph/reservation/{resident_id}"
    billing = models.Billing(
        id=uuid.uuid4(),
        resident_id=resident_id,
        billing_period="reservation",
        rent_amount=resident.monthly_rate,
        electric_charge=Decimal("0"),
        water_charge=Decimal("0"),
        other_charges=Decimal("0"),
        previous_balance=Decimal("0"),
        total_amount=resident.monthly_rate,
        status="pending_review",
        payment_link=mock_link,
    )
    db.add(billing)
    await db.commit()
    await db.refresh(billing)
    return billing


@router.post("/moveins/{resident_id}/activate", response_model=schemas.ResidentOut)
async def activate_movein(resident_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(models.Resident).where(models.Resident.id == resident_id))
    resident = result.scalar_one_or_none()
    if not resident:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resident not found")
    if resident.status != "reserved":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Resident is not in reserved status")

    if not resident.id_type or not resident.id_number:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Documents incomplete")

    payment_result = await db.execute(
        select(models.Payment).where(
            models.Payment.resident_id == resident_id,
            models.Payment.status.in_(["verified", "matched"])
        )
    )
    payment_cleared = payment_result.scalar_one_or_none() is not None

    billing_result = await db.execute(
        select(models.Billing).where(
            models.Billing.resident_id == resident_id,
            models.Billing.status == "paid"
        )
    )
    billing_cleared = billing_result.scalar_one_or_none() is not None

    if not payment_cleared and not billing_cleared:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Payment not cleared")

    resident.status = "active"
    if not resident.move_in_date:
        resident.move_in_date = date.today()
    await db.commit()
    await db.refresh(resident)
    return resident


@router.get("/rooms", response_model=list[RoomOut])
async def list_available_rooms(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(models.Room).where(models.Room.occupied_beds < models.Room.capacity)
    )
    rooms = result.scalars().all()
    return rooms
