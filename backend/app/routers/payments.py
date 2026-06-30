from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from sqlalchemy.orm import selectinload
from datetime import datetime, date, time
from decimal import Decimal
from uuid import UUID
import re
from typing import Optional, List

from app.database import get_db
from app import models, auth
from app.models import Payment, Resident, LedgerEntry, Billing, Bed, Room
from app.schemas import (
    PaymentOut, DormerLedgerOut, DormerLedgerSummaryOut,
    LedgerBillingRow, LedgerPaymentRow,
)
from pydantic import BaseModel, Field

router = APIRouter()


class WebhookPayload(BaseModel):
    reference_id: str
    amount: Decimal = Field(..., ge=0)
    method: str
    gateway_ref: Optional[str] = None
    signature: Optional[str] = None


class MatchRequest(BaseModel):
    resident_id: UUID
    billing_id: Optional[UUID] = None


class ReconcileRequest(BaseModel):
    payment_ids: Optional[List[UUID]] = None


class DSRReport(BaseModel):
    date: str
    total_amount: Decimal
    total_transactions: int


def mock_verify_signature(payload: dict, signature: Optional[str]) -> bool:
    # Mock signature verification — always accept for this demo
    return True


def parse_reference_id(reference_id: str):
    pattern = r"^RES-([0-9a-fA-F-]{36})-(.+)$"
    match = re.match(pattern, reference_id)
    if not match:
        return None, None
    return UUID(match.group(1)), match.group(2)


@router.post("/webhook", response_model=PaymentOut)
async def payment_webhook(payload: WebhookPayload, db: AsyncSession = Depends(get_db)):
    if not mock_verify_signature(payload.model_dump(mode="json"), payload.signature):
        raise HTTPException(status_code=400, detail="Invalid signature")

    resident_id, period = parse_reference_id(payload.reference_id)
    if not resident_id:
        raise HTTPException(status_code=400, detail="Invalid reference_id format")

    result = await db.execute(select(Resident).where(Resident.id == resident_id))
    resident = result.scalar_one_or_none()
    if not resident:
        raise HTTPException(status_code=404, detail="Resident not found")

    # Find most recent open billing for this resident
    result = await db.execute(
        select(Billing)
        .where(
            and_(
                Billing.resident_id == resident_id,
                Billing.status.in_(["pending_review", "approved", "distributed", "overdue"]),
            )
        )
        .order_by(Billing.created_at.desc())
    )
    billing = result.scalar_one_or_none()

    payment = Payment(
        resident_id=resident_id,
        billing_id=billing.id if billing else None,
        amount=payload.amount,
        method=payload.method,
        gateway_ref=payload.gateway_ref or payload.reference_id,
        status="matched",
        matched_at=datetime.utcnow(),
        webhook_payload=payload.model_dump(mode="json"),
    )
    db.add(payment)
    await db.flush()

    # Update resident ledger — credit entry
    result = await db.execute(
        select(LedgerEntry)
        .where(LedgerEntry.resident_id == resident_id)
        .order_by(LedgerEntry.created_at.desc())
    )
    last_entry = result.scalar_one_or_none()
    running_balance = last_entry.running_balance if last_entry else Decimal("0.00")
    new_balance = running_balance + payload.amount

    ledger = LedgerEntry(
        resident_id=resident_id,
        entry_type="credit",
        amount=payload.amount,
        description=f"Webhook payment via {payload.method} ({payload.gateway_ref or payload.reference_id})",
        reference_id=payment.id,
        running_balance=new_balance,
    )
    db.add(ledger)
    await db.commit()
    await db.refresh(payment)
    return payment


@router.post("/reconcile")
async def manual_reconcile(
    body: ReconcileRequest,
    db: AsyncSession = Depends(get_db),
    current_staff: models.Staff = Depends(auth.require_staff),
):
    if body.payment_ids:
        result = await db.execute(select(Payment).where(Payment.id.in_(body.payment_ids)))
        payments = result.scalars().all()
    else:
        result = await db.execute(select(Payment).where(Payment.status == "unreconciled"))
        payments = result.scalars().all()

    count = 0
    for payment in payments:
        payment.status = "matched"
        payment.matched_at = datetime.utcnow()

        result = await db.execute(
            select(LedgerEntry)
            .where(LedgerEntry.resident_id == payment.resident_id)
            .order_by(LedgerEntry.created_at.desc())
        )
        last_entry = result.scalar_one_or_none()
        running_balance = last_entry.running_balance if last_entry else Decimal("0.00")
        new_balance = running_balance + payment.amount

        ledger = LedgerEntry(
            resident_id=payment.resident_id,
            entry_type="credit",
            amount=payment.amount,
            description=f"Manual reconcile payment {payment.id}",
            reference_id=payment.id,
            running_balance=new_balance,
        )
        db.add(ledger)
        count += 1

    await db.commit()
    return {"reconciled_count": count}


@router.get("/unmatched", response_model=List[PaymentOut])
async def list_unmatched(
    db: AsyncSession = Depends(get_db),
    current_staff: models.Staff = Depends(auth.require_staff),
    property_code: Optional[str] = Depends(auth.get_current_property),
):
    query = select(Payment).where(Payment.status == "unreconciled")
    if property_code:
        query = (
            query
            .join(Resident, Payment.resident_id == Resident.id)
            .join(Bed, Resident.bed_id == Bed.id, isouter=True)
            .join(Room, Bed.room_id == Room.id, isouter=True)
            .where(Room.property_code == property_code)
        )
    result = await db.execute(query)
    payments = result.scalars().all()
    return payments


@router.get("/list", response_model=List[PaymentOut])
async def list_payments(
    resident_id: Optional[UUID] = Query(None),
    status: Optional[str] = Query(None),
    limit: int = Query(500, ge=1, le=2000),
    db: AsyncSession = Depends(get_db),
    current_staff: models.Staff = Depends(auth.require_staff),
    property_code: Optional[str] = Depends(auth.get_current_property),
):
    query = select(Payment).order_by(Payment.created_at.desc())
    if resident_id:
        query = query.where(Payment.resident_id == resident_id)
    if status:
        query = query.where(Payment.status == status)
    if property_code:
        query = (
            query
            .join(Resident, Payment.resident_id == Resident.id)
            .join(Bed, Resident.bed_id == Bed.id, isouter=True)
            .join(Room, Bed.room_id == Room.id, isouter=True)
            .where(Room.property_code == property_code)
        )
    query = query.limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.post("/{id}/match", response_model=PaymentOut)
async def match_payment(
    id: UUID,
    body: MatchRequest,
    db: AsyncSession = Depends(get_db),
    current_staff: models.Staff = Depends(auth.require_staff),
):
    result = await db.execute(select(Payment).where(Payment.id == id))
    payment = result.scalar_one_or_none()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")

    payment.resident_id = body.resident_id
    payment.billing_id = body.billing_id
    payment.status = "matched"
    payment.matched_at = datetime.utcnow()

    result = await db.execute(
        select(LedgerEntry)
        .where(LedgerEntry.resident_id == body.resident_id)
        .order_by(LedgerEntry.created_at.desc())
    )
    last_entry = result.scalar_one_or_none()
    running_balance = last_entry.running_balance if last_entry else Decimal("0.00")
    new_balance = running_balance + payment.amount

    ledger = LedgerEntry(
        resident_id=body.resident_id,
        entry_type="credit",
        amount=payment.amount,
        description=f"Manual match payment {payment.id}",
        reference_id=payment.id,
        running_balance=new_balance,
    )
    db.add(ledger)
    await db.commit()
    await db.refresh(payment)
    return payment


@router.get("/dsr", response_model=DSRReport)
async def daily_sales_report(
    db: AsyncSession = Depends(get_db),
    current_staff: models.Staff = Depends(auth.require_staff),
    property_code: Optional[str] = Depends(auth.get_current_property),
):
    today = date.today()
    start = datetime.combine(today, time.min)
    end = datetime.combine(today, time.max)

    query = (
        select(func.sum(Payment.amount), func.count(Payment.id))
        .where(Payment.matched_at >= start, Payment.matched_at <= end)
    )
    if property_code:
        query = (
            query
            .join(Resident, Payment.resident_id == Resident.id)
            .join(Bed, Resident.bed_id == Bed.id, isouter=True)
            .join(Room, Bed.room_id == Room.id, isouter=True)
            .where(Room.property_code == property_code)
        )
    result = await db.execute(query)
    row = result.one()
    total_amount = row[0] or Decimal("0.00")
    total_transactions = row[1] or 0

    return DSRReport(
        date=today.isoformat(),
        total_amount=total_amount,
        total_transactions=total_transactions,
    )


@router.get("/ledger/{resident_id}", response_model=DormerLedgerOut)
async def get_dormer_ledger(
    resident_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_staff: models.Staff = Depends(auth.require_staff),
):
    # Fetch resident with bed/room
    result = await db.execute(
        select(Resident, Bed, Room)
        .join(Bed, Resident.bed_id == Bed.id, isouter=True)
        .join(Room, Bed.room_id == Room.id, isouter=True)
        .where(Resident.id == resident_id)
    )
    row = result.first()
    if not row:
        raise HTTPException(status_code=404, detail="Resident not found")
    resident, bed, room = row

    # Fetch billings
    billing_result = await db.execute(
        select(Billing)
        .where(Billing.resident_id == resident_id)
        .order_by(Billing.billing_period.asc())
    )
    billings = billing_result.scalars().all()

    # Fetch payments
    payment_result = await db.execute(
        select(Payment)
        .where(Payment.resident_id == resident_id)
        .order_by(Payment.created_at.asc())
    )
    payments = payment_result.scalars().all()

    # Index payments by billing_id
    payments_by_billing = {}
    payments_total_all = Decimal("0")
    for p in payments:
        payments_total_all += p.amount or Decimal("0")
        if p.billing_id:
            bid = str(p.billing_id)
            if bid not in payments_by_billing:
                payments_by_billing[bid] = Decimal("0")
            payments_by_billing[bid] += p.amount or Decimal("0")

    # Build billing rows with balance
    billing_rows = []
    total_billed = Decimal("0")
    for b in billings:
        total_billed += b.total_amount or Decimal("0")
        payments_for_billing = payments_by_billing.get(str(b.id), Decimal("0"))
        balance = (b.total_amount or Decimal("0")) - payments_for_billing
        billing_rows.append(LedgerBillingRow(
            id=b.id,
            billing_period=b.billing_period,
            rent_amount=b.rent_amount or Decimal("0"),
            electric_charge=b.electric_charge,
            water_charge=b.water_charge,
            other_charges=b.other_charges,
            total_amount=b.total_amount or Decimal("0"),
            status=b.status,
            payments_total=payments_for_billing,
            balance_due=balance if balance > 0 else Decimal("0"),
            created_at=b.created_at,
        ))

    # Build payment rows
    payment_rows = []
    for p in payments:
        payment_rows.append(LedgerPaymentRow(
            id=p.id,
            amount=p.amount or Decimal("0"),
            method=p.method,
            gateway_ref=p.gateway_ref,
            receipt_no=p.receipt_no,
            sales_invoice_no=p.sales_invoice_no,
            status=p.status,
            created_at=p.created_at,
        ))

    bed_letter = None
    if bed and bed.bed_code:
        bed_letter = bed.bed_code[-1] if len(bed.bed_code) > 0 else None

    room_type = None
    if room:
        room_type = f"Room for {room.capacity} persons" if room.capacity else None

    balance_due = total_billed - payments_total_all
    if balance_due < 0:
        balance_due = Decimal("0")

    return DormerLedgerOut(
        resident_id=resident.id,
        resident_name=resident.full_name,
        room_number=room.room_number if room else None,
        bed_code=bed.bed_code if bed else None,
        bed_letter=bed_letter,
        room_type=room_type,
        bed_type=bed.bed_type if bed else None,
        monthly_rate=resident.monthly_rate or Decimal("0"),
        move_in_date=resident.move_in_date,
        move_out_date=resident.move_out_date,
        contract_end_date=resident.contract_end_date,
        deposit_paid=resident.deposit_paid,
        total_billed=total_billed,
        total_paid=payments_total_all,
        balance_due=balance_due,
        billings=billing_rows,
        payments=payment_rows,
    )


@router.get("/ledgers", response_model=List[DormerLedgerSummaryOut])
async def list_all_ledgers(
    search: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_staff: models.Staff = Depends(auth.require_staff),
    property_code: Optional[str] = Depends(auth.get_current_property),
):
    # Fetch all active residents with bed/room
    query = (
        select(Resident, Bed, Room)
        .join(Bed, Resident.bed_id == Bed.id, isouter=True)
        .join(Room, Bed.room_id == Room.id, isouter=True)
        .where(Resident.status.in_(["active", "reserved", "moved_out"]))
        .order_by(Room.room_number.asc().nullslast(), Bed.bed_number.asc().nullslast())
    )
    if property_code:
        query = query.where(Room.property_code == property_code)
    result = await db.execute(query)
    rows = result.all()

    # Fetch all billings and payments in bulk
    billing_result = await db.execute(
        select(Billing.resident_id, func.sum(Billing.total_amount))
        .group_by(Billing.resident_id)
    )
    billed_map = {str(r[0]): r[1] or Decimal("0") for r in billing_result.all()}

    payment_result = await db.execute(
        select(Payment.resident_id, func.sum(Payment.amount))
        .where(Payment.status.in_(["matched", "verified"]))
        .group_by(Payment.resident_id)
    )
    paid_map = {str(r[0]): r[1] or Decimal("0") for r in payment_result.all()}

    out = []
    for resident, bed, room in rows:
        rid = str(resident.id)
        total_billed = billed_map.get(rid, Decimal("0"))
        total_paid = paid_map.get(rid, Decimal("0"))
        balance_due = total_billed - total_paid
        if balance_due < 0:
            balance_due = Decimal("0")

        ledger_status = "paid" if balance_due <= 0 and total_billed > 0 else ("unpaid" if total_billed > 0 and total_paid <= 0 else "partial")
        if total_billed <= 0:
            ledger_status = "no_bills"

        if status and ledger_status != status:
            continue

        if search:
            s = search.lower()
            if not (
                (resident.full_name and s in resident.full_name.lower()) or
                (room and room.room_number and s in room.room_number.lower()) or
                (bed and bed.bed_code and s in bed.bed_code.lower())
            ):
                continue

        out.append(DormerLedgerSummaryOut(
            resident_id=resident.id,
            resident_name=resident.full_name,
            room_number=room.room_number if room else None,
            bed_code=bed.bed_code if bed else None,
            monthly_rate=resident.monthly_rate or Decimal("0"),
            total_billed=total_billed,
            total_paid=total_paid,
            balance_due=balance_due,
            status=ledger_status,
        ))

    return out
