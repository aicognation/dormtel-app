from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, extract, and_
from sqlalchemy.orm import selectinload
from datetime import datetime, timedelta
from decimal import Decimal
import calendar
from uuid import UUID
from typing import Optional

from app.database import get_db
from app import models, schemas
from app import auth

router = APIRouter()


def _is_end_of_month(d) -> bool:
    """Flag if date is within the last 3 days of its month."""
    if not d:
        return False
    days_in_month = calendar.monthrange(d.year, d.month)[1]
    return (days_in_month - d.day) <= 2


@router.post("/", response_model=schemas.MoveOutOut)
async def create_moveout(
    payload: schemas.MoveOutCreate,
    db: AsyncSession = Depends(get_db),
    current_staff: models.Staff = Depends(auth.require_staff),
):
    result = await db.execute(select(models.Resident).where(models.Resident.id == payload.resident_id))
    resident = result.scalar_one_or_none()
    if not resident:
        raise HTTPException(status_code=404, detail="Resident not found")

    moveout = models.MoveOut(
        resident_id=payload.resident_id,
        requested_date=payload.requested_date,
        actual_date=payload.actual_date,
        reason=payload.reason,
        forwarding_contact=payload.forwarding_contact,
        status="requested",
        is_end_of_month_flag=_is_end_of_month(payload.requested_date),
    )
    db.add(moveout)
    await db.flush()

    # Early termination without clause: less than ~6 months from move-in
    if resident.move_in_date:
        min_term_date = resident.move_in_date + timedelta(days=180)
        if payload.requested_date < min_term_date:
            checkpoint = models.Checkpoint(
                checkpoint_id=f"CP-11-{str(moveout.id)[:8]}",
                stage="move_out_review",
                status="pending",
                sla_deadline=datetime.utcnow() + timedelta(hours=48),
                context_package={
                    "move_out_id": str(moveout.id),
                    "resident_id": str(resident.id),
                    "reason": "early_termination_without_clause",
                },
            )
            db.add(checkpoint)

    await db.commit()
    await db.refresh(moveout)
    return moveout


@router.post("/{moveout_id}/clearance", response_model=schemas.MoveOutOut)
async def complete_clearance(
    moveout_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_staff: models.Staff = Depends(auth.require_staff),
):
    result = await db.execute(select(models.MoveOut).where(models.MoveOut.id == moveout_id))
    moveout = result.scalar_one_or_none()
    if not moveout:
        raise HTTPException(status_code=404, detail="Move-out not found")

    result = await db.execute(select(models.Resident).where(models.Resident.id == moveout.resident_id))
    resident = result.scalar_one_or_none()
    if not resident:
        raise HTTPException(status_code=404, detail="Resident not found")

    moveout_date = moveout.actual_date or moveout.extended_date or moveout.requested_date
    if not moveout_date:
        raise HTTPException(status_code=400, detail="No move-out date available")

    days_in_month = calendar.monthrange(moveout_date.year, moveout_date.month)[1]
    day_of_month = moveout_date.day

    prorated_rent = resident.monthly_rate * Decimal(day_of_month) / Decimal(days_in_month)
    prorated_rent = prorated_rent.quantize(Decimal("0.01"))

    billing_period = f"Final - {moveout_date.year}-{moveout_date.month:02d}"

    billing = models.Billing(
        resident_id=moveout.resident_id,
        billing_period=billing_period,
        rent_amount=prorated_rent,
        total_amount=prorated_rent,
        status="draft",
    )
    db.add(billing)
    await db.flush()

    moveout.status = "clearance"
    moveout.final_billing_id = billing.id

    await db.commit()
    await db.refresh(moveout)
    return moveout


@router.post("/{moveout_id}/finalize", response_model=schemas.MoveOutOut)
async def finalize_moveout(
    moveout_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_staff: models.Staff = Depends(auth.require_staff),
):
    result = await db.execute(select(models.MoveOut).where(models.MoveOut.id == moveout_id))
    moveout = result.scalar_one_or_none()
    if not moveout:
        raise HTTPException(status_code=404, detail="Move-out not found")

    if not moveout.final_billing_id:
        raise HTTPException(status_code=400, detail="Clearance billing not completed")

    result = await db.execute(select(models.Resident).where(models.Resident.id == moveout.resident_id))
    resident = result.scalar_one_or_none()
    if not resident:
        raise HTTPException(status_code=404, detail="Resident not found")

    result = await db.execute(select(models.Billing).where(models.Billing.id == moveout.final_billing_id))
    billing = result.scalar_one_or_none()
    if not billing:
        raise HTTPException(status_code=404, detail="Final billing not found")

    deposit = resident.deposit_paid or Decimal("0")
    penalties = Decimal("0")
    final_balance = (billing.total_amount or Decimal("0")) + penalties - deposit

    if final_balance < 0:
        refund_amount = abs(final_balance)

        result = await db.execute(
            select(models.LedgerEntry)
            .where(models.LedgerEntry.resident_id == resident.id)
            .order_by(models.LedgerEntry.created_at.desc())
            .limit(1)
        )
        last_entry = result.scalar_one_or_none()
        current_balance = last_entry.running_balance if last_entry else Decimal("0")
        new_balance = current_balance - refund_amount

        ledger = models.LedgerEntry(
            resident_id=resident.id,
            entry_type="credit",
            amount=refund_amount.quantize(Decimal("0.01")),
            description="Security deposit refund",
            reference_id=moveout.id,
            running_balance=new_balance.quantize(Decimal("0.01")),
        )
        db.add(ledger)
        moveout.refund_amount = refund_amount.quantize(Decimal("0.01"))

    moveout.status = "refund_pending"
    moveout.accounting_submitted_at = datetime.utcnow()

    await db.commit()
    await db.refresh(moveout)
    return moveout


@router.post("/{moveout_id}/complete", response_model=schemas.MoveOutOut)
async def complete_moveout(
    moveout_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_staff: models.Staff = Depends(auth.require_staff),
):
    result = await db.execute(select(models.MoveOut).where(models.MoveOut.id == moveout_id))
    moveout = result.scalar_one_or_none()
    if not moveout:
        raise HTTPException(status_code=404, detail="Move-out not found")

    result = await db.execute(select(models.Resident).where(models.Resident.id == moveout.resident_id))
    resident = result.scalar_one_or_none()
    if not resident:
        raise HTTPException(status_code=404, detail="Resident not found")

    moveout.status = "completed"
    moveout.accounting_resolved_at = datetime.utcnow()
    resident.status = "moved_out"

    # Sync move-out date to resident record
    resident.move_out_date = (
        moveout.actual_date or moveout.extended_date or moveout.requested_date or date.today()
    )

    # Free the bed and update room status
    if resident.bed_id:
        bed_result = await db.execute(
            select(models.Bed)
            .where(models.Bed.id == resident.bed_id)
            .options(selectinload(models.Bed.room))
        )
        bed = bed_result.scalar_one_or_none()
        if bed:
            bed.status = "available"
            room = bed.room
            if room and room.status == "full":
                room.status = "available"
        resident.bed_id = None

    await db.commit()
    await db.refresh(moveout)
    return moveout


@router.post("/{moveout_id}/extend", response_model=schemas.MoveOutOut)
async def extend_moveout(
    moveout_id: UUID,
    payload: schemas.MoveOutExtendRequest,
    db: AsyncSession = Depends(get_db),
    current_staff: models.Staff = Depends(auth.require_staff),
):
    result = await db.execute(select(models.MoveOut).where(models.MoveOut.id == moveout_id))
    moveout = result.scalar_one_or_none()
    if not moveout:
        raise HTTPException(status_code=404, detail="Move-out not found")

    if moveout.status not in ("requested", "clearance"):
        raise HTTPException(status_code=400, detail="Can only extend move-outs in requested or clearance status")

    moveout.extended_date = payload.extended_date
    moveout.extension_reason = payload.extension_reason
    moveout.extended_by = current_staff.id
    moveout.is_end_of_month_flag = _is_end_of_month(payload.extended_date)

    await db.commit()
    await db.refresh(moveout)
    return moveout


@router.get("/", response_model=list[schemas.MoveOutOut])
async def list_moveouts(
    status: str = Query(None),
    resident_id: UUID = Query(None),
    year: int = Query(None),
    month: int = Query(None),
    db: AsyncSession = Depends(get_db),
    current_staff: models.Staff = Depends(auth.require_staff),
    property_code: Optional[str] = Depends(auth.get_current_property),
):
    query = (
        select(models.MoveOut, models.Resident, models.Bed, models.Room)
        .join(models.Resident, models.MoveOut.resident_id == models.Resident.id)
        .join(models.Bed, models.Resident.bed_id == models.Bed.id, isouter=True)
        .join(models.Room, models.Bed.room_id == models.Room.id, isouter=True)
        .order_by(models.MoveOut.requested_date.desc())
    )

    if status:
        query = query.where(models.MoveOut.status == status)
    if resident_id:
        query = query.where(models.MoveOut.resident_id == resident_id)
    if year and month:
        query = query.where(
            and_(
                extract("year", models.MoveOut.requested_date) == year,
                extract("month", models.MoveOut.requested_date) == month,
            )
        )
    elif year:
        query = query.where(extract("year", models.MoveOut.requested_date) == year)

    # Property filter via JWT
    if property_code:
        query = query.where(models.Room.property_code == property_code)

    result = await db.execute(query)
    rows = result.all()

    out = []
    for moveout, resident, bed, room in rows:
        out.append(schemas.MoveOutOut(
            id=moveout.id,
            resident_id=moveout.resident_id,
            resident_name=resident.full_name if resident else None,
            resident_email=resident.email if resident else None,
            resident_phone=resident.phone if resident else None,
            id_type=resident.id_type if resident else None,
            id_number=resident.id_number if resident else None,
            address=resident.address if resident else None,
            school=resident.school if resident else None,
            course=resident.course if resident else None,
            review_center=resident.review_center if resident else None,
            company_name=resident.company_name if resident else None,
            exam_date=resident.exam_date if resident else None,
            source=resident.source if resident else None,
            location=resident.location if resident else None,
            dormer_type=resident.dormer_type if resident else None,
            board_exam_type=resident.board_exam_type if resident else None,
            lease_term_months=resident.lease_term_months if resident else None,
            monthly_rate=resident.monthly_rate if resident else None,
            deposit_paid=resident.deposit_paid if resident else None,
            contract_end_date=resident.contract_end_date if resident else None,
            is_first_time_dormer=resident.is_first_time_dormer if resident else None,
            notes=resident.notes if resident else None,
            room_number=room.room_number if room else None,
            bed_code=bed.bed_code if bed else None,
            bed_type=bed.bed_type if bed else None,
            building=room.building if room else None,
            room_type=room.room_type if room else None,
            requested_date=moveout.requested_date,
            actual_date=moveout.actual_date,
            extended_date=moveout.extended_date,
            extension_reason=moveout.extension_reason,
            reason=moveout.reason,
            forwarding_contact=moveout.forwarding_contact,
            status=moveout.status,
            is_end_of_month_flag=moveout.is_end_of_month_flag,
            refund_amount=moveout.refund_amount,
            final_billing_id=moveout.final_billing_id,
            created_at=moveout.created_at,
        ))
    return out
