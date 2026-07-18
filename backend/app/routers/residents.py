from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from sqlalchemy.orm import selectinload
from datetime import datetime
from uuid import UUID
import uuid
from typing import Optional

from app.database import get_db
from app import models, schemas, auth

router = APIRouter()


@router.get("", response_model=list[schemas.ResidentListOut])
async def list_residents(
    search: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    branch: Optional[str] = Query(None),
    current_staff: models.Staff = Depends(auth.require_staff),
    property_code: Optional[str] = Depends(auth.get_current_property),
    db: AsyncSession = Depends(get_db),
):
    query = (
        select(models.Resident)
        .options(
            selectinload(models.Resident.bed).selectinload(models.Bed.room),
            selectinload(models.Resident.deposits),
        )
        .order_by(models.Resident.created_at.desc())
    )

    # Property filter via JWT
    if property_code:
        query = query.join(models.Bed, models.Resident.bed_id == models.Bed.id, isouter=True) \
                     .join(models.Room, models.Bed.room_id == models.Room.id, isouter=True) \
                     .where(models.Room.property_code == property_code)

    if status:
        query = query.where(models.Resident.status == status)

    result = await db.execute(query)
    residents = result.scalars().all()

    output = []
    for r in residents:
        if search:
            s = search.lower()
            if not (
                (r.full_name and s in r.full_name.lower()) or
                (r.email and s in r.email.lower()) or
                (r.phone and s in r.phone.lower()) or
                (r.bed and r.bed.bed_code and s in r.bed.bed_code.lower()) or
                (r.bed and r.bed.room and r.bed.room.room_number and s in r.bed.room.room_number.lower())
            ):
                continue

        output.append(schemas.ResidentListOut(
            id=r.id,
            full_name=r.full_name,
            email=r.email,
            phone=r.phone,
            monthly_rate=r.monthly_rate,
            status=r.status,
            bed_id=r.bed_id,
            id_type=r.id_type,
            id_number=r.id_number,
            address=r.address,
            school=r.school,
            course=r.course,
            review_center=r.review_center,
            exam_date=r.exam_date,
            is_first_time_dormer=r.is_first_time_dormer,
            source=r.source,
            location=r.location,
            dormer_type=r.dormer_type,
            board_exam_type=r.board_exam_type,
            lease_term_months=r.lease_term_months,
            move_in_date=r.move_in_date,
            move_out_date=r.move_out_date,
            contract_end_date=r.contract_end_date,
            deposit_paid=r.deposit_paid,
            created_at=r.created_at,
            notes=r.notes,
            created_by=r.created_by,
            updated_by=r.updated_by,
            bed_code=r.bed.bed_code if r.bed else None,
            bed_type=r.bed.bed_type if r.bed else None,
            room_number=r.bed.room.room_number if r.bed and r.bed.room else None,
            building=r.bed.room.building if r.bed and r.bed.room else None,
            room_type=r.bed.room.room_type if r.bed and r.bed.room else None,
            deposits=[
                {"deposit_type": d.deposit_type, "amount": d.amount, "receipt_number": d.receipt_number}
                for d in (r.deposits or [])
            ],
        ))
    return output


@router.post("", response_model=schemas.ResidentOut, status_code=status.HTTP_201_CREATED)
async def create_resident(
    payload: schemas.ResidentCreate,
    current_staff: models.Staff = Depends(auth.require_admin),
    db: AsyncSession = Depends(get_db),
):
    existing = await db.execute(
        select(models.Resident).where(
            or_(models.Resident.email == payload.email, models.Resident.phone == payload.phone)
        )
    )
    if existing.first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email or phone already exists")

    if payload.bed_id:
        bed_result = await db.execute(select(models.Bed).where(models.Bed.id == payload.bed_id))
        bed = bed_result.scalar_one_or_none()
        if not bed:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Bed not found")

    resident = models.Resident(
        id=uuid.uuid4(),
        full_name=payload.full_name,
        email=payload.email,
        phone=payload.phone,
        id_type=payload.id_type,
        id_number=payload.id_number,
        status=payload.status or "prospect",
        bed_id=payload.bed_id,
        address=payload.address,
        school=payload.school,
        course=payload.course,
        review_center=payload.review_center,
        exam_date=payload.exam_date,
        is_first_time_dormer=payload.is_first_time_dormer,
        source=payload.source,
        location=payload.location,
        dormer_type=payload.dormer_type,
        board_exam_type=payload.board_exam_type,
        lease_term_months=payload.lease_term_months,
        monthly_rate=payload.monthly_rate or 0,
        move_in_date=payload.move_in_date,
        move_out_date=payload.move_out_date,
        contract_end_date=payload.contract_end_date,
        notes=payload.notes,
        deposit_paid=0,
        created_by=current_staff.id,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(resident)
    await db.commit()
    await db.refresh(resident)
    return resident


@router.get("/{resident_id}", response_model=schemas.ResidentListOut)
async def get_resident(
    resident_id: UUID,
    current_staff: models.Staff = Depends(auth.require_staff),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(models.Resident)
        .where(models.Resident.id == resident_id)
        .options(selectinload(models.Resident.bed).selectinload(models.Bed.room))
    )
    r = result.scalar_one_or_none()
    if not r:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resident not found")

    return schemas.ResidentListOut(
        id=r.id,
        full_name=r.full_name,
        email=r.email,
        phone=r.phone,
        monthly_rate=r.monthly_rate,
        status=r.status,
        bed_id=r.bed_id,
        id_type=r.id_type,
        id_number=r.id_number,
        address=r.address,
        school=r.school,
        course=r.course,
        review_center=r.review_center,
        exam_date=r.exam_date,
        is_first_time_dormer=r.is_first_time_dormer,
        source=r.source,
        location=r.location,
        dormer_type=r.dormer_type,
        board_exam_type=r.board_exam_type,
        lease_term_months=r.lease_term_months,
        move_in_date=r.move_in_date,
        move_out_date=r.move_out_date,
        contract_end_date=r.contract_end_date,
        deposit_paid=r.deposit_paid,
        created_at=r.created_at,
        notes=r.notes,
        created_by=r.created_by,
        updated_by=r.updated_by,
        bed_code=r.bed.bed_code if r.bed else None,
        bed_type=r.bed.bed_type if r.bed else None,
        room_number=r.bed.room.room_number if r.bed and r.bed.room else None,
        building=r.bed.room.building if r.bed and r.bed.room else None,
        room_type=r.bed.room.room_type if r.bed and r.bed.room else None,
    )


@router.patch("/{resident_id}", response_model=schemas.ResidentOut)
async def update_resident(
    resident_id: UUID,
    payload: schemas.ResidentUpdate,
    current_staff: models.Staff = Depends(auth.require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(models.Resident).where(models.Resident.id == resident_id))
    resident = result.scalar_one_or_none()
    if not resident:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resident not found")

    if payload.full_name is not None:
        resident.full_name = payload.full_name
    if payload.email is not None:
        resident.email = payload.email
    if payload.phone is not None:
        resident.phone = payload.phone
    if payload.id_type is not None:
        resident.id_type = payload.id_type
    if payload.id_number is not None:
        resident.id_number = payload.id_number
    if payload.status is not None:
        resident.status = payload.status
    if payload.bed_id is not None:
        resident.bed_id = payload.bed_id
    if payload.address is not None:
        resident.address = payload.address
    if payload.school is not None:
        resident.school = payload.school
    if payload.course is not None:
        resident.course = payload.course
    if payload.review_center is not None:
        resident.review_center = payload.review_center
    if payload.exam_date is not None:
        resident.exam_date = payload.exam_date
    if payload.is_first_time_dormer is not None:
        resident.is_first_time_dormer = payload.is_first_time_dormer
    if payload.source is not None:
        resident.source = payload.source
    if payload.location is not None:
        resident.location = payload.location
    if payload.dormer_type is not None:
        resident.dormer_type = payload.dormer_type
    if payload.board_exam_type is not None:
        resident.board_exam_type = payload.board_exam_type
    if payload.lease_term_months is not None:
        resident.lease_term_months = payload.lease_term_months
    if payload.notes is not None:
        resident.notes = payload.notes
    if payload.move_in_date is not None:
        resident.move_in_date = payload.move_in_date
    if payload.move_out_date is not None:
        resident.move_out_date = payload.move_out_date
    if payload.contract_end_date is not None:
        resident.contract_end_date = payload.contract_end_date
    if payload.monthly_rate is not None:
        resident.monthly_rate = payload.monthly_rate

    resident.updated_by = current_staff.id
    resident.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(resident)
    return resident


@router.delete("/{resident_id}")
async def deactivate_resident(
    resident_id: UUID,
    current_staff: models.Staff = Depends(auth.require_manager),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(models.Resident).where(models.Resident.id == resident_id))
    resident = result.scalar_one_or_none()
    if not resident:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resident not found")

    resident.status = "inactive"
    resident.updated_by = current_staff.id
    resident.updated_at = datetime.utcnow()
    await db.commit()
    return {"message": "Resident deactivated"}
