from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timedelta
from decimal import Decimal
import calendar
from uuid import UUID

from app.database import get_db
from app import models, schemas

router = APIRouter()


@router.post("/", response_model=schemas.MoveOutOut)
async def create_moveout(payload: schemas.MoveOutCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(models.Resident).where(models.Resident.id == payload.resident_id))
    resident = result.scalar_one_or_none()
    if not resident:
        raise HTTPException(status_code=404, detail="Resident not found")

    moveout = models.MoveOut(
        resident_id=payload.resident_id,
        requested_date=payload.requested_date,
        reason=payload.reason,
        forwarding_contact=payload.forwarding_contact,
        status="requested",
    )
    db.add(moveout)
    await db.flush()

    # Early termination without clause: less than ~6 months from move-in
    if resident.move_in_date:
        min_term_date = resident.move_in_date + timedelta(days=180)
        if payload.requested_date < min_term_date:
            checkpoint = models.Checkpoint(
                checkpoint_id="CP-11",
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
async def complete_clearance(moveout_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(models.MoveOut).where(models.MoveOut.id == moveout_id))
    moveout = result.scalar_one_or_none()
    if not moveout:
        raise HTTPException(status_code=404, detail="Move-out not found")

    result = await db.execute(select(models.Resident).where(models.Resident.id == moveout.resident_id))
    resident = result.scalar_one_or_none()
    if not resident:
        raise HTTPException(status_code=404, detail="Resident not found")

    moveout_date = moveout.actual_date or moveout.requested_date
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
async def finalize_moveout(moveout_id: UUID, db: AsyncSession = Depends(get_db)):
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
async def complete_moveout(moveout_id: UUID, db: AsyncSession = Depends(get_db)):
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

    await db.commit()
    await db.refresh(moveout)
    return moveout


@router.get("/", response_model=list[schemas.MoveOutOut])
async def list_moveouts(
    status: str = Query(None),
    resident_id: UUID = Query(None),
    db: AsyncSession = Depends(get_db),
):
    query = select(models.MoveOut)
    if status:
        query = query.where(models.MoveOut.status == status)
    if resident_id:
        query = query.where(models.MoveOut.resident_id == resident_id)
    result = await db.execute(query)
    return result.scalars().all()
