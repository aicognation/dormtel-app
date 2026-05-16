from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from datetime import datetime, date, time
from decimal import Decimal
from uuid import UUID
import re
from typing import Optional, List

from app.database import get_db
from app.models import Payment, Resident, LedgerEntry, Billing
from app.schemas import PaymentOut
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


def _serialize_payment(payment: Payment) -> PaymentOut:
    # Payment model lacks created_at, so we synthesize it from matched_at
    return PaymentOut(
        id=payment.id,
        amount=payment.amount,
        method=payment.method,
        resident_id=payment.resident_id,
        status=payment.status,
        gateway_ref=payment.gateway_ref,
        created_at=payment.matched_at or datetime.utcnow(),
    )


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
    return _serialize_payment(payment)


@router.post("/reconcile")
async def manual_reconcile(body: ReconcileRequest, db: AsyncSession = Depends(get_db)):
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
async def list_unmatched(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Payment).where(Payment.status == "unreconciled"))
    payments = result.scalars().all()
    return [_serialize_payment(p) for p in payments]


@router.post("/{id}/match", response_model=PaymentOut)
async def match_payment(id: UUID, body: MatchRequest, db: AsyncSession = Depends(get_db)):
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
    return _serialize_payment(payment)


@router.get("/dsr", response_model=DSRReport)
async def daily_sales_report(db: AsyncSession = Depends(get_db)):
    today = date.today()
    start = datetime.combine(today, time.min)
    end = datetime.combine(today, time.max)

    result = await db.execute(
        select(func.sum(Payment.amount), func.count(Payment.id))
        .where(Payment.matched_at >= start, Payment.matched_at <= end)
    )
    row = result.one()
    total_amount = row[0] or Decimal("0.00")
    total_transactions = row[1] or 0

    return DSRReport(
        date=today.isoformat(),
        total_amount=total_amount,
        total_transactions=total_transactions,
    )
