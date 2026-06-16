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
            address=r.address,
            school=r.school,
            course=r.course,
            review_center=r.review_center,
            exam_date=r.exam_date,
            is_first_time_dormer=r.is_first_time_dormer,
            created_at=r.created_at,
            notes=r.notes,
            created_by=r.created_by,
            updated_by=r.updated_by,
            bed_code=r.bed.bed_code if r.bed else None,
            room_number=r.bed.room.room_number if r.bed and r.bed.room else None,
            building=r.bed.room.building if r.bed and r.bed.room else None,
        ))
    return output
