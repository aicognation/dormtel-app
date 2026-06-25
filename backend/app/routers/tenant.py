from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from datetime import datetime, date
from decimal import Decimal
from uuid import UUID
from typing import List, Optional
import os, base64, uuid as _uuid_mod

from app.database import get_db
from app.models import (
    Resident, Room, Bed, Billing, Payment, LedgerEntry,
    ServiceRequest, Announcement, MoveOut, Inquiry,
)
from app.schemas import (
    TenantLoginRequest, TenantLoginResponse,
    TenantDashboardResponse,
    BillingOut, PaymentOut,
    ServiceRequestCreate, ServiceRequestOut,
    MoveOutCreate, MoveOutOut,
    TenantPayRequest, TenantProfileResponse,
    AnnouncementOut, InquiryCreate, InquiryOut,
)

router = APIRouter()


@router.post("/login", response_model=TenantLoginResponse)
async def tenant_login(body: TenantLoginRequest, db: AsyncSession = Depends(get_db)):
    if not body.email and not body.phone and not body.bed_code:
        raise HTTPException(status_code=400, detail="Provide email, phone, or bed code")

    resident = None
    if body.bed_code:
        result = await db.execute(
            select(Bed).where(Bed.bed_code == body.bed_code.upper())
        )
        bed = result.scalar_one_or_none()
        if bed:
            result = await db.execute(
                select(Resident).where(Resident.bed_id == bed.id, Resident.status == "active")
            )
            resident = result.scalar_one_or_none()
    elif body.email:
        result = await db.execute(select(Resident).where(Resident.email == body.email))
        resident = result.scalar_one_or_none()
    else:
        result = await db.execute(select(Resident).where(Resident.phone == body.phone))
        resident = result.scalar_one_or_none()
    if not resident:
        raise HTTPException(status_code=404, detail="Resident not found")

    room_number = None
    building = None
    bed_code = None
    if resident.bed_id:
        b = await db.execute(
            select(Bed, Room)
            .join(Room, Bed.room_id == Room.id, isouter=True)
            .where(Bed.id == resident.bed_id)
        )
        row = b.one_or_none()
        if row:
            bed, room = row
            bed_code = bed.bed_code
            if room:
                room_number = room.room_number
                building = room.building

    return TenantLoginResponse(
        id=resident.id,
        full_name=resident.full_name,
        email=resident.email,
        phone=resident.phone,
        status=resident.status,
        room_number=room_number,
        building=building,
        bed_code=bed_code,
        monthly_rate=resident.monthly_rate,
        move_in_date=resident.move_in_date,
        contract_end_date=resident.contract_end_date,
        deposit_paid=resident.deposit_paid,
    )


@router.get("/dashboard/{resident_id}", response_model=TenantDashboardResponse)
async def tenant_dashboard(resident_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Resident).where(Resident.id == resident_id))
    resident = result.scalar_one_or_none()
    if not resident:
        raise HTTPException(status_code=404, detail="Resident not found")

    room_number = None
    building = None
    bed_code = None
    if resident.bed_id:
        b = await db.execute(
            select(Bed, Room)
            .join(Room, Bed.room_id == Room.id, isouter=True)
            .where(Bed.id == resident.bed_id)
        )
        row = b.one_or_none()
        if row:
            bed, room = row
            bed_code = bed.bed_code
            if room:
                room_number = room.room_number
                building = room.building

    # Current billing
    result = await db.execute(
        select(Billing)
        .where(Billing.resident_id == resident_id)
        .order_by(Billing.created_at.desc())
        .limit(1)
    )
    latest_billing = result.scalar_one_or_none()

    # Outstanding balance from ledger
    result = await db.execute(
        select(LedgerEntry)
        .where(LedgerEntry.resident_id == resident_id)
        .order_by(LedgerEntry.created_at.desc())
        .limit(1)
    )
    last_ledger = result.scalar_one_or_none()
    balance = last_ledger.running_balance if last_ledger else Decimal("0.00")

    # If no ledger entries, use latest billing total as outstanding
    if not last_ledger and latest_billing and latest_billing.status != "paid":
        balance = latest_billing.total_amount

    # Open service requests count
    result = await db.execute(
        select(func.count(ServiceRequest.id))
        .where(
            ServiceRequest.resident_id == resident_id,
            ServiceRequest.status.in_(["submitted", "acknowledged", "in_progress"]),
        )
    )
    open_requests = result.scalar() or 0

    # Billing stats
    result = await db.execute(
        select(func.count(Billing.id))
        .where(
            Billing.resident_id == resident_id,
            Billing.status.in_(["draft", "pending_review", "approved", "distributed", "overdue"]),
        )
    )
    pending_billings_count = result.scalar() or 0

    result = await db.execute(
        select(func.count(Billing.id))
        .where(
            Billing.resident_id == resident_id,
            Billing.status == "paid",
        )
    )
    paid_billings_count = result.scalar() or 0

    # Service request stats
    result = await db.execute(
        select(func.count(ServiceRequest.id))
        .where(ServiceRequest.resident_id == resident_id)
    )
    total_requests_submitted = result.scalar() or 0

    result = await db.execute(
        select(func.count(ServiceRequest.id))
        .where(
            ServiceRequest.resident_id == resident_id,
            ServiceRequest.status.in_(["resolved", "closed"]),
        )
    )
    total_responses_received = result.scalar() or 0

    # Months to end contract
    months_to_end_contract = None
    if resident.contract_end_date:
        today = date.today()
        if resident.contract_end_date >= today:
            months = (resident.contract_end_date.year - today.year) * 12 + (resident.contract_end_date.month - today.month)
            if resident.contract_end_date.day < today.day:
                months -= 1
            months_to_end_contract = max(0, months)

    # Last payment
    result = await db.execute(
        select(Payment)
        .where(Payment.resident_id == resident_id)
        .order_by(Payment.created_at.desc())
        .limit(1)
    )
    last_payment = result.scalar_one_or_none()

    # Active announcements
    result = await db.execute(
        select(Announcement)
        .where(Announcement.is_active == True)
        .order_by(Announcement.published_at.desc())
        .limit(5)
    )
    announcements = result.scalars().all()

    return TenantDashboardResponse(
        resident_name=resident.full_name,
        room_number=room_number,
        building=building,
        bed_code=bed_code,
        outstanding_balance=balance,
        open_requests=open_requests,
        pending_billings_count=pending_billings_count,
        paid_billings_count=paid_billings_count,
        total_requests_submitted=total_requests_submitted,
        total_responses_received=total_responses_received,
        months_to_end_contract=months_to_end_contract,
        current_billing_period=latest_billing.billing_period if latest_billing else None,
        current_billing_total=latest_billing.total_amount if latest_billing else None,
        current_billing_status=latest_billing.status if latest_billing else None,
        last_payment_date=last_payment.created_at if last_payment else None,
        last_payment_amount=last_payment.amount if last_payment else None,
        announcements=[
            {
                "id": str(a.id),
                "title": a.title,
                "content": a.content,
                "category": a.category.value if hasattr(a.category, "value") else a.category,
                "priority": a.priority.value if hasattr(a.priority, "value") else a.priority,
                "published_at": a.published_at.isoformat(),
            }
            for a in announcements
        ],
    )


@router.get("/billings/{resident_id}", response_model=List[BillingOut])
async def tenant_billings(
    resident_id: UUID,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    query = select(Billing).where(Billing.resident_id == resident_id)
    if status:
        query = query.where(Billing.status == status)
    query = query.order_by(Billing.created_at.desc())
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/payments/{resident_id}", response_model=List[PaymentOut])
async def tenant_payments(resident_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Payment)
        .where(Payment.resident_id == resident_id)
        .order_by(Payment.created_at.desc())
    )
    return result.scalars().all()


@router.post("/payments/{resident_id}/pay", response_model=PaymentOut)
async def tenant_pay(
    resident_id: UUID,
    body: TenantPayRequest,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Resident).where(Resident.id == resident_id))
    resident = result.scalar_one_or_none()
    if not resident:
        raise HTTPException(status_code=404, detail="Resident not found")

    billing_id = body.billing_id
    if not billing_id:
        result = await db.execute(
            select(Billing)
            .where(
                Billing.resident_id == resident_id,
                Billing.status.in_(["approved", "distributed", "overdue"]),
            )
            .order_by(Billing.created_at.desc())
            .limit(1)
        )
        billing = result.scalar_one_or_none()
        if billing:
            billing_id = billing.id

    import uuid as _uuid
    ref = body.gateway_ref or f"TP-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{str(_uuid.uuid4())[:8]}"

    # Save proof-of-payment file if provided (base64-encoded)
    receipt_path = None
    if body.proof_of_payment:
        try:
            now = datetime.utcnow()
            proof_dir = os.path.join("/app/proofs", str(now.year), f"{now.month:02d}")
            os.makedirs(proof_dir, exist_ok=True)
            ext = ".png"  # default
            header = body.proof_of_payment[:30]
            if "jpeg" in header or "jpg" in header:
                ext = ".jpg"
            elif "pdf" in header:
                ext = ".pdf"
            # Strip data-URI prefix if present
            b64_data = body.proof_of_payment
            if "," in b64_data[:80]:
                b64_data = b64_data.split(",", 1)[1]
            file_bytes = base64.b64decode(b64_data)
            fname = f"proof_{str(resident_id)[:8]}_{now.strftime('%Y%m%d%H%M%S')}_{str(_uuid.uuid4())[:6]}{ext}"
            fpath = os.path.join(proof_dir, fname)
            with open(fpath, "wb") as f:
                f.write(file_bytes)
            receipt_path = fpath
        except Exception:
            receipt_path = None  # non-fatal; payment still goes through

    payment = Payment(
        resident_id=resident_id,
        billing_id=billing_id,
        amount=body.amount,
        method=body.method,
        gateway_ref=ref,
        status="verified",
        matched_at=datetime.utcnow(),
        receipt_no=receipt_path,
    )
    db.add(payment)
    await db.flush()

    # Update billing status to paid if amount covers total
    if billing_id:
        result = await db.execute(select(Billing).where(Billing.id == billing_id))
        billing = result.scalar_one_or_none()
        if billing and body.amount >= billing.total_amount:
            billing.status = "paid"

    # Credit ledger
    result = await db.execute(
        select(LedgerEntry)
        .where(LedgerEntry.resident_id == resident_id)
        .order_by(LedgerEntry.created_at.desc())
        .limit(1)
    )
    last_entry = result.scalar_one_or_none()
    running_balance = last_entry.running_balance if last_entry else Decimal("0.00")
    new_balance = running_balance + body.amount

    ledger = LedgerEntry(
        resident_id=resident_id,
        entry_type="credit",
        amount=body.amount,
        description=f"Tenant payment via {body.method} ({ref})",
        reference_id=payment.id,
        running_balance=new_balance,
    )
    db.add(ledger)
    await db.commit()
    await db.refresh(payment)
    return payment


@router.get("/service-requests/{resident_id}", response_model=List[ServiceRequestOut])
async def tenant_service_requests(
    resident_id: UUID,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    query = select(ServiceRequest).where(ServiceRequest.resident_id == resident_id)
    if status:
        query = query.where(ServiceRequest.status == status)
    query = query.order_by(ServiceRequest.submitted_at.desc())
    result = await db.execute(query)
    return result.scalars().all()


@router.post("/service-requests/{resident_id}", response_model=ServiceRequestOut)
async def create_service_request(
    resident_id: UUID,
    body: ServiceRequestCreate,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Resident).where(Resident.id == resident_id))
    resident = result.scalar_one_or_none()
    if not resident:
        raise HTTPException(status_code=404, detail="Resident not found")

    bed_code = None
    if resident.bed_id:
        b = await db.execute(select(Bed).where(Bed.id == resident.bed_id))
        bed = b.scalar_one_or_none()
        if bed:
            bed_code = bed.bed_code

    sr = ServiceRequest(
        resident_id=resident_id,
        category=body.category,
        subject=body.subject,
        description=body.description,
        location=body.location or f"Bed {bed_code or 'N/A'}",
        priority=body.priority,
    )
    db.add(sr)
    await db.commit()
    await db.refresh(sr)
    return sr


@router.get("/moveout/{resident_id}", response_model=Optional[MoveOutOut])
async def tenant_moveout(resident_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(MoveOut)
        .where(MoveOut.resident_id == resident_id)
        .order_by(MoveOut.created_at.desc())
        .limit(1)
    )
    moveout = result.scalar_one_or_none()
    return moveout


@router.post("/moveout/{resident_id}", response_model=MoveOutOut)
async def create_moveout(
    resident_id: UUID,
    body: MoveOutCreate,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Resident).where(Resident.id == resident_id))
    resident = result.scalar_one_or_none()
    if not resident:
        raise HTTPException(status_code=404, detail="Resident not found")

    # Check no existing active moveout
    result = await db.execute(
        select(MoveOut).where(
            MoveOut.resident_id == resident_id,
            MoveOut.status.in_(["requested", "clearance", "final_billing", "refund_pending"]),
        ).limit(1)
    )
    existing = result.scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=400, detail="Active move-out request already exists")

    moveout = MoveOut(
        resident_id=resident_id,
        requested_date=body.requested_date,
        reason=body.reason,
        forwarding_contact=body.forwarding_contact,
    )
    db.add(moveout)
    await db.commit()
    await db.refresh(moveout)
    return moveout


@router.get("/profile/{resident_id}", response_model=TenantProfileResponse)
async def tenant_profile(resident_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Resident).where(Resident.id == resident_id))
    resident = result.scalar_one_or_none()
    if not resident:
        raise HTTPException(status_code=404, detail="Resident not found")

    room_number = None
    building = None
    bed_code = None
    bed_number = None
    if resident.bed_id:
        b = await db.execute(
            select(Bed, Room)
            .join(Room, Bed.room_id == Room.id, isouter=True)
            .where(Bed.id == resident.bed_id)
        )
        row = b.one_or_none()
        if row:
            bed, room = row
            bed_code = bed.bed_code
            bed_number = bed.bed_number
            if room:
                room_number = room.room_number
                building = room.building

    # Ledger balance
    result = await db.execute(
        select(LedgerEntry)
        .where(LedgerEntry.resident_id == resident_id)
        .order_by(LedgerEntry.created_at.desc())
        .limit(1)
    )
    last_entry = result.scalar_one_or_none()
    balance = last_entry.running_balance if last_entry else Decimal("0.00")

    return TenantProfileResponse(
        id=resident.id,
        full_name=resident.full_name,
        email=resident.email,
        phone=resident.phone,
        id_type=resident.id_type,
        id_number=resident.id_number,
        status=resident.status,
        room_number=room_number,
        building=building,
        bed_code=bed_code,
        bed_number=bed_number,
        monthly_rate=resident.monthly_rate,
        deposit_paid=resident.deposit_paid,
        move_in_date=resident.move_in_date,
        contract_end_date=resident.contract_end_date,
        ledger_balance=balance,
    )


@router.get("/announcements", response_model=List[AnnouncementOut])
async def list_announcements(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Announcement)
        .where(Announcement.is_active == True)
        .order_by(Announcement.published_at.desc())
    )
    return result.scalars().all()


@router.get("/inquiries/{resident_id}", response_model=List[InquiryOut])
async def tenant_inquiries(
    resident_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Inquiry)
        .where(Inquiry.resident_id == resident_id)
        .order_by(Inquiry.created_at.desc())
    )
    return result.scalars().all()


@router.post("/inquiry/{resident_id}", response_model=InquiryOut)
async def create_tenant_inquiry(
    resident_id: UUID,
    body: InquiryCreate,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Resident).where(Resident.id == resident_id))
    resident = result.scalar_one_or_none()
    if not resident:
        raise HTTPException(status_code=404, detail="Resident not found")

    inquiry = Inquiry(
        source="website",
        content=body.content,
        inquiry_type=body.inquiry_type,
        resident_id=resident_id,
        property_code=body.property_code or "DT01",
        prospect_name=resident.full_name,
        prospect_phone=resident.phone,
        prospect_email=resident.email,
        status="new",
    )
    db.add(inquiry)
    await db.commit()
    await db.refresh(inquiry)
    return inquiry
