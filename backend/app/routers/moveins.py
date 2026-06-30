from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, and_
from sqlalchemy.orm import selectinload
from datetime import date
from typing import Optional, Literal

from app.database import get_db
from app import models, schemas, auth

router = APIRouter()


@router.get("", response_model=list[schemas.ResidentListOut])
async def list_moveins(
    period: Literal["past", "current", "future"] = Query("current"),
    current_staff: models.Staff = Depends(auth.require_staff),
    property_code: Optional[str] = Depends(auth.get_current_property),
    db: AsyncSession = Depends(get_db),
):
    today = date.today()

    query = (
        select(models.Resident)
        .options(selectinload(models.Resident.bed).selectinload(models.Bed.room))
        .where(models.Resident.move_in_date.isnot(None))
        .order_by(models.Resident.move_in_date.desc())
    )

    if period == "past":
        query = query.where(models.Resident.move_in_date < today)
    elif period == "current":
        query = query.where(
            and_(
                models.Resident.move_in_date <= today,
                or_(
                    models.Resident.move_out_date.is_(None),
                    models.Resident.move_out_date >= today,
                ),
            )
        )
    elif period == "future":
        query = query.where(models.Resident.move_in_date > today)

    # Property filter via JWT
    if property_code:
        query = query.join(models.Bed, models.Resident.bed_id == models.Bed.id, isouter=True) \
                     .join(models.Room, models.Bed.room_id == models.Room.id, isouter=True) \
                     .where(models.Room.property_code == property_code)

    result = await db.execute(query)
    residents = result.scalars().all()

    output = []
    for r in residents:
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
        ))
    return output
