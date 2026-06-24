from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID
from typing import Optional
import uuid
import logging

from pydantic import BaseModel, EmailStr

from app.database import get_db
from app import models, schemas, auth

router = APIRouter()
logger = logging.getLogger(__name__)


class DepositInput(BaseModel):
    deposit_type: str
    amount: Decimal
    receipt_number: Optional[str] = None
    payment_date: Optional[date] = None
    notes: Optional[str] = None


class ReservationCreateRequest(BaseModel):
    full_name: str
    email: EmailStr
    phone: str
    monthly_rate: Decimal
    id_type: Optional[str] = None
    id_number: Optional[str] = None
    bed_id: Optional[UUID] = None
    move_in_date: date
    move_out_date: date
    inquiry_id: Optional[UUID] = None
    school: Optional[str] = None
    course: Optional[str] = None
    review_center: Optional[str] = None
    exam_date: Optional[date] = None
    is_first_time_dormer: Optional[bool] = True
    address: Optional[str] = None
    deposit_paid: Optional[Decimal] = Decimal("0")
    source: Optional[str] = None
    location: Optional[str] = None
    dormer_type: Optional[str] = None
    board_exam_type: Optional[str] = None
    lease_term_months: Optional[int] = None
    deposits: Optional[list] = None


@router.post("/reservations", response_model=schemas.ResidentOut, status_code=status.HTTP_201_CREATED)
async def create_reservation(
    payload: ReservationCreateRequest,
    current_staff: models.Staff = Depends(auth.require_staff),
    db: AsyncSession = Depends(get_db),
):
    inquiry = None
    if payload.inquiry_id:
        result = await db.execute(
            select(models.Inquiry).where(models.Inquiry.id == payload.inquiry_id)
        )
        inquiry = result.scalar_one_or_none()
        if not inquiry:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Inquiry not found")
        if inquiry.status == "converted":
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Inquiry already converted")

    bed = None

    if payload.bed_id:
        result = await db.execute(
            select(models.Bed)
            .where(models.Bed.id == payload.bed_id)
            .options(selectinload(models.Bed.room))
        )
        bed = result.scalar_one_or_none()
        if not bed:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bed not found")
        if bed.status != "available":
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Bed is not available")
    else:
        result = await db.execute(
            select(models.Bed)
            .where(models.Bed.status == "available")
            .order_by(models.Bed.bed_code)
        )
        bed = result.scalars().first()
        if not bed:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="No available beds")

    # Update bed status
    bed.status = "reserved"

    # Update room status if all beds are now taken
    room = bed.room
    if room:
        beds_result = await db.execute(
            select(func.count(models.Bed.id))
            .where(
                models.Bed.room_id == room.id,
                models.Bed.status == "available"
            )
        )
        available_beds = beds_result.scalar() or 0
        if available_beds == 0:
            room.status = "full"

    if payload.move_out_date <= payload.move_in_date:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Move-out date must be after move-in date")

    # Check for duplicate email or phone — warn but allow
    warnings = []
    existing_result = await db.execute(
        select(models.Resident).where(
            (models.Resident.email == payload.email) | (models.Resident.phone == payload.phone)
        )
    )
    existing_residents = existing_result.scalars().all()
    if existing_residents:
        dup_emails = [r for r in existing_residents if r.email == payload.email]
        dup_phones = [r for r in existing_residents if r.phone == payload.phone]
        if dup_emails:
            names = ", ".join(r.full_name for r in dup_emails[:3])
            warnings.append(f"Email already used by: {names}")
        if dup_phones:
            names = ", ".join(r.full_name for r in dup_phones[:3])
            warnings.append(f"Phone already used by: {names}")
        logger.warning(
            "[AUDIT] Reservation created with duplicate contact info — "
            "email=%s phone=%s full_name=%s duplicates=%s",
            payload.email, payload.phone, payload.full_name,
            [{"id": str(r.id), "name": r.full_name, "status": r.status} for r in existing_residents],
        )

    # Pre-fill from inquiry if available
    full_name = payload.full_name
    email = payload.email
    phone = payload.phone
    school = payload.school
    course = payload.course
    review_center = payload.review_center
    exam_date = payload.exam_date
    is_first_time_dormer = payload.is_first_time_dormer
    address = payload.address
    source = payload.source
    location = payload.location
    dormer_type = payload.dormer_type
    board_exam_type = payload.board_exam_type
    lease_term_months = payload.lease_term_months

    if inquiry:
        full_name = full_name or inquiry.prospect_name or ""
        email = email or inquiry.prospect_email or ""
        phone = phone or inquiry.prospect_phone or ""
        school = school or inquiry.school
        course = course or inquiry.course
        review_center = review_center or inquiry.review_center
        exam_date = exam_date or inquiry.exam_date
        source = source or inquiry.source
        if inquiry.first_time_dormer is not None:
            is_first_time_dormer = inquiry.first_time_dormer

    resident = models.Resident(
        id=uuid.uuid4(),
        full_name=full_name,
        email=email,
        phone=phone,
        id_type=payload.id_type,
        id_number=payload.id_number,
        status="reserved",
        bed_id=bed.id,
        move_in_date=payload.move_in_date,
        move_out_date=payload.move_out_date,
        contract_end_date=payload.move_out_date,
        monthly_rate=payload.monthly_rate,
        deposit_paid=payload.deposit_paid or Decimal("0"),
        school=school,
        course=course,
        review_center=review_center,
        exam_date=exam_date,
        is_first_time_dormer=is_first_time_dormer,
        address=address,
        source=source,
        location=location,
        dormer_type=dormer_type,
        board_exam_type=board_exam_type,
        lease_term_months=lease_term_months,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(resident)
    await db.commit()
    await db.refresh(resident)

    # Create deposit records if provided
    if payload.deposits:
        for dep in payload.deposits:
            deposit = models.Deposit(
                id=uuid.uuid4(),
                resident_id=resident.id,
                deposit_type=dep.get("deposit_type"),
                amount=Decimal(str(dep.get("amount", 0))),
                receipt_number=dep.get("receipt_number"),
                payment_date=dep.get("payment_date") or date.today(),
                notes=dep.get("notes"),
                created_at=datetime.utcnow(),
            )
            db.add(deposit)
        await db.commit()

    # Link inquiry to resident and mark as converted
    if inquiry:
        inquiry.resident_id = resident.id
        inquiry.status = "converted"
        await db.commit()

    # Build response with optional duplicate warnings
    response_data = schemas.ResidentOut.model_validate(resident).model_dump()
    if warnings:
        response_data["warnings"] = warnings
    return response_data


@router.post("/reservations/{resident_id}/payment-link", response_model=schemas.BillingOut)
async def generate_payment_link(
    resident_id: UUID,
    current_staff: models.Staff = Depends(auth.require_staff),
    db: AsyncSession = Depends(get_db),
):
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
async def activate_movein(
    resident_id: UUID,
    current_staff: models.Staff = Depends(auth.require_staff),
    db: AsyncSession = Depends(get_db),
):
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

    # Update bed status to occupied
    if resident.bed_id:
        bed_result = await db.execute(select(models.Bed).where(models.Bed.id == resident.bed_id))
        bed = bed_result.scalar_one_or_none()
        if bed:
            bed.status = "occupied"

    await db.commit()
    await db.refresh(resident)
    return resident


@router.get("/rooms", response_model=list[schemas.RoomWithBedsOut])
async def list_rooms_with_beds(
    current_staff: models.Staff = Depends(auth.require_staff),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(models.Room)
        .options(selectinload(models.Room.beds).selectinload(models.Bed.resident))
        .order_by(models.Room.room_number)
    )
    rooms = result.scalars().all()

    output = []
    for room in rooms:
        occupied_count = sum(1 for b in room.beds if b.resident and b.resident.status == "active")
        reserved_count = sum(1 for b in room.beds if b.resident and b.resident.status == "reserved")
        available_count = len(room.beds) - occupied_count - reserved_count

        rates = [b.rate_per_bed for b in room.beds if b.rate_per_bed is not None]
        min_rate = min(rates) if rates else None
        max_rate = max(rates) if rates else None

        room_data = schemas.RoomWithBedsOut(
            id=room.id,
            room_number=room.room_number,
            display_room_number=room.display_room_number,
            property_code=room.property_code,
            building=room.building,
            room_type=room.room_type,
            capacity=room.capacity,
            status=room.status,
            beds=[
                schemas.BedOut(
                    id=bed.id,
                    bed_code=bed.bed_code,
                    bed_number=bed.bed_number,
                    bed_type=bed.bed_type,
                    rate_per_bed=bed.rate_per_bed,
                    status=bed.status,
                    resident=schemas.ResidentMiniOut(
                        id=bed.resident.id,
                        full_name=bed.resident.full_name,
                        status=bed.resident.status
                    ) if bed.resident else None
                )
                for bed in room.beds
            ],
            occupied_count=occupied_count,
            reserved_count=reserved_count,
            available_count=available_count,
            min_rate=min_rate,
            max_rate=max_rate,
        )
        output.append(room_data)

    return output


@router.get("/rooms/{room_id}/tenants", response_model=list[schemas.BedOut])
async def get_room_tenants(
    room_id: UUID,
    current_staff: models.Staff = Depends(auth.require_staff),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(models.Bed)
        .where(models.Bed.room_id == room_id)
        .options(selectinload(models.Bed.resident))
        .order_by(models.Bed.bed_number)
    )
    beds = result.scalars().all()
    if not beds:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Room not found")
    return [
        schemas.BedOut(
            id=bed.id,
            bed_code=bed.bed_code,
            bed_number=bed.bed_number,
            bed_type=bed.bed_type,
            rate_per_bed=bed.rate_per_bed,
            status=bed.status,
            resident=schemas.ResidentMiniOut(
                id=bed.resident.id,
                full_name=bed.resident.full_name,
                status=bed.resident.status
            ) if bed.resident else None
        )
        for bed in beds
    ]
