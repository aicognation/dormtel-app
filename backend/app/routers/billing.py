from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional, List
from decimal import Decimal
from uuid import UUID
from datetime import datetime, date
from pydantic import BaseModel, Field

from app.database import get_db
from app.models import MeterReading, Billing, Resident
from app.schemas import MeterReadingCreate, MeterReadingOut, BillingOut

router = APIRouter()


class BillingGenerateRequest(BaseModel):
    billing_period: str
    building: Optional[str] = None
    total_electric_charge: Decimal = Field(..., ge=0)
    total_water_charge: Decimal = Field(..., ge=0)
    other_charges: Decimal = Field(default=Decimal("0"), ge=0)


def _ensure_created_at(obj):
    if not hasattr(obj, "created_at") or getattr(obj, "created_at", None) is None:
        obj.created_at = datetime.utcnow()
    return obj


@router.post("/meter-readings", response_model=MeterReadingOut)
async def submit_meter_reading(data: MeterReadingCreate, db: AsyncSession = Depends(get_db)):
    prev_result = await db.execute(
        select(MeterReading)
        .where(MeterReading.building == data.building)
        .where(MeterReading.reading_date < data.reading_date)
        .order_by(MeterReading.reading_date.desc())
        .limit(1)
    )
    prev = prev_result.scalar_one_or_none()

    variance_pct = Decimal("0")
    if prev:
        prev_electric = prev.electric_reading or Decimal("0")
        prev_water = prev.water_reading or Decimal("0")
        curr_electric = data.electric_reading or Decimal("0")
        curr_water = data.water_reading or Decimal("0")
        prev_total = prev_electric + prev_water
        curr_total = curr_electric + curr_water
        if prev_total > 0:
            variance_pct = ((curr_total - prev_total) / prev_total) * 100

    status = "pending" if variance_pct > 20 else "approved"

    reading = MeterReading(
        building=data.building,
        reading_date=data.reading_date,
        electric_reading=data.electric_reading,
        water_reading=data.water_reading,
        variance_pct=variance_pct,
        status=status,
    )
    db.add(reading)
    await db.commit()
    await db.refresh(reading)
    return reading


@router.post("/generate", response_model=List[BillingOut])
async def generate_billings(data: BillingGenerateRequest, db: AsyncSession = Depends(get_db)):
    residents_result = await db.execute(select(Resident).where(Resident.status == "active"))
    residents = residents_result.scalars().all()
    if not residents:
        raise HTTPException(status_code=400, detail="No active residents found")

    count = len(residents)

    variance_pct = Decimal("0")
    status = "draft"
    reading = None

    if data.building:
        reading_result = await db.execute(
            select(MeterReading)
            .where(MeterReading.building == data.building)
            .order_by(MeterReading.reading_date.desc())
            .limit(1)
        )
        reading = reading_result.scalar_one_or_none()

    if reading:
        variance_pct = reading.variance_pct or Decimal("0")
        if variance_pct < 15:
            status = "approved"
        else:
            status = "pending_review"
    else:
        if data.building:
            avg_result = await db.execute(
                select(
                    func.avg(MeterReading.electric_reading),
                    func.avg(MeterReading.water_reading),
                )
                .where(MeterReading.building == data.building)
            )
            row = avg_result.one_or_none()
            avg_electric = row[0] if row and row[0] is not None else Decimal("0")
            avg_water = row[1] if row and row[1] is not None else Decimal("0")
            estimated_reading = MeterReading(
                building=data.building,
                reading_date=date.today(),
                electric_reading=avg_electric,
                water_reading=avg_water,
                variance_pct=Decimal("0"),
                status="estimated",
            )
            db.add(estimated_reading)
            await db.flush()
        variance_pct = Decimal("0")
        status = "draft"

    electric_per_head = data.total_electric_charge / count
    water_per_head = data.total_water_charge / count
    other_per_head = data.other_charges / count

    billings = []
    for resident in residents:
        total = (
            resident.monthly_rate
            + electric_per_head
            + water_per_head
            + other_per_head
        )
        billing = Billing(
            resident_id=resident.id,
            billing_period=data.billing_period,
            rent_amount=resident.monthly_rate,
            electric_charge=electric_per_head,
            water_charge=water_per_head,
            other_charges=other_per_head,
            total_amount=total,
            variance_pct=variance_pct,
            status=status,
        )
        db.add(billing)
        billings.append(billing)

    await db.commit()
    for b in billings:
        await db.refresh(b)
        _ensure_created_at(b)
    return billings


@router.post("/{billing_id}/approve", response_model=BillingOut)
async def approve_billing(billing_id: UUID, db: AsyncSession = Depends(get_db)):
    billing = await db.get(Billing, billing_id)
    if not billing:
        raise HTTPException(status_code=404, detail="Billing not found")
    billing.status = "approved"
    await db.commit()
    await db.refresh(billing)
    _ensure_created_at(billing)
    return billing


@router.post("/{billing_id}/distribute", response_model=BillingOut)
async def distribute_billing(billing_id: UUID, db: AsyncSession = Depends(get_db)):
    billing = await db.get(Billing, billing_id)
    if not billing:
        raise HTTPException(status_code=404, detail="Billing not found")
    billing.status = "distributed"
    billing.distributed_at = datetime.utcnow()
    billing.payment_link = f"https://pay.dormtel.app/b/{billing_id}"
    await db.commit()
    await db.refresh(billing)
    _ensure_created_at(billing)
    return billing


@router.get("/", response_model=List[BillingOut])
async def list_billings(
    resident_id: Optional[UUID] = Query(None),
    status: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    query = select(Billing)
    if resident_id:
        query = query.where(Billing.resident_id == resident_id)
    if status:
        query = query.where(Billing.status == status)
    result = await db.execute(query)
    billings = result.scalars().all()
    for b in billings:
        _ensure_created_at(b)
    return billings
