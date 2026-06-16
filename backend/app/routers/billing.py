import io
import os
import calendar

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional, List
from decimal import Decimal
from uuid import UUID
from datetime import datetime, date
from pydantic import BaseModel, Field

from app.database import get_db
from app.models import MeterReading, Billing, Resident, Room, Bed
from app.schemas import (
    MeterReadingCreate, MeterReadingOut, MeterReadingDailyGridOut,
    MeterReadingDailyRow, MeterReadingDailyCell,
    BillingOut, BillingWithResidentOut,
)


class BillingPreviewRow(BaseModel):
    resident_id: UUID
    resident_name: str
    room_number: Optional[str] = None
    bed_number: Optional[int] = None
    bed_code: Optional[str] = None
    monthly_rate: Decimal
    rent_amount: Decimal
    electric_charge: Decimal
    water_charge: Decimal
    other_charges: Decimal
    total_amount: Decimal


class BillingPreviewResponse(BaseModel):
    billing_period: str
    building: Optional[str] = None
    total_residents: int
    rows: List[BillingPreviewRow]
    summary: dict


def _parse_date(val):
    if isinstance(val, datetime):
        return val.date()
    if isinstance(val, date):
        return val
    if isinstance(val, str):
        for fmt in ("%Y-%m-%d", "%Y-%m-%d %H:%M:%S", "%m/%d/%Y", "%d/%m/%Y"):
            try:
                return datetime.strptime(val.strip(), fmt).date()
            except ValueError:
                continue
    return None


def _parse_decimal(val):
    if val is None or val == "":
        return None
    try:
        return Decimal(str(val).replace(",", ""))
    except Exception:
        return None


router = APIRouter()


class BillingGenerateRequest(BaseModel):
    billing_period: str
    building: Optional[str] = None
    other_charges: Decimal = Field(default=Decimal("0"), ge=0)
    total_water_bill: Decimal = Field(default=Decimal("0"), ge=0)


async def _get_active_residents_with_rooms(
    db: AsyncSession,
    building: Optional[str] = None,
):
    """Get active residents joined with their bed and room."""
    query = (
        select(Resident, Bed, Room)
        .join(Bed, Resident.bed_id == Bed.id, isouter=True)
        .join(Room, Bed.room_id == Room.id, isouter=True)
        .where(Resident.status == "active")
    )
    if building:
        query = query.where(Room.building == building)

    result = await db.execute(query)
    rows = result.all()

    # Group by room
    residents_by_room = {}
    no_room = []
    for resident, bed, room in rows:
        if room:
            rid = str(room.id)
            if rid not in residents_by_room:
                residents_by_room[rid] = {"room": room, "residents": []}
            residents_by_room[rid]["residents"].append((resident, bed))
        else:
            no_room.append((resident, bed))

    return residents_by_room, no_room, rows


async def _compute_resident_electric(
    db: AsyncSession,
    billing_period: str,
    building: Optional[str] = None,
):
    """Sum per-resident electric meter readings for the billing period."""
    year, month = map(int, billing_period.split("-"))
    start_date = date(year, month, 1)
    if month == 12:
        end_date = date(year + 1, 1, 1)
    else:
        end_date = date(year, month + 1, 1)

    query = select(MeterReading).where(
        MeterReading.reading_date >= start_date,
        MeterReading.reading_date < end_date,
        MeterReading.resident_id.isnot(None),
    )
    if building:
        query = query.where(MeterReading.building == building)

    result = await db.execute(query)
    readings = result.scalars().all()

    resident_electric = {}
    for reading in readings:
        rid = str(reading.resident_id)
        resident_electric[rid] = resident_electric.get(rid, Decimal("0")) + (reading.electric_reading or Decimal("0"))

    return resident_electric


def _count_days_stayed(move_in_date, move_out_date, period_start, period_end):
    """Count overlap days between resident stay and billing period."""
    if not move_in_date:
        # No move-in date: assume full period
        effective_start = period_start
    else:
        effective_start = max(move_in_date, period_start)

    if move_out_date and move_out_date < period_start:
        return 0

    if move_out_date:
        effective_end = min(move_out_date, period_end)
    else:
        effective_end = period_end

    if effective_start > effective_end:
        return 0

    return (effective_end - effective_start).days + 1


async def _compute_water_by_days(
    db: AsyncSession,
    billing_period: str,
    total_water_bill: Decimal,
    building: Optional[str] = None,
):
    """Compute water charge per resident based on days stayed."""
    year, month = map(int, billing_period.split("-"))
    start_date = date(year, month, 1)
    if month == 12:
        end_date = date(year + 1, 1, 1)
    else:
        end_date = date(year, month + 1, 1)

    query = (
        select(Resident, Bed, Room)
        .join(Bed, Resident.bed_id == Bed.id, isouter=True)
        .join(Room, Bed.room_id == Room.id, isouter=True)
        .where(Resident.status == "active")
    )
    if building:
        query = query.where(Room.building == building)

    result = await db.execute(query)
    rows = result.all()

    total_days = 0
    resident_days = {}
    for resident, bed, room in rows:
        days = _count_days_stayed(resident.move_in_date, resident.move_out_date, start_date, end_date)
        total_days += days
        resident_days[str(resident.id)] = days

    rate_per_day = total_water_bill / total_days if total_days > 0 else Decimal("0")

    resident_water = {}
    for rid, days in resident_days.items():
        resident_water[rid] = Decimal(str(days)) * rate_per_day

    return resident_water, total_days, rate_per_day


@router.post("/meter-readings", response_model=MeterReadingOut)
async def submit_meter_reading(data: MeterReadingCreate, db: AsyncSession = Depends(get_db)):
    # Validate room if provided
    room = None
    if data.room_id:
        room_result = await db.execute(select(Room).where(Room.id == data.room_id))
        room = room_result.scalar_one_or_none()
        if not room:
            raise HTTPException(status_code=400, detail="Room not found")

    # Validate resident if provided
    resident = None
    if data.resident_id:
        resident_result = await db.execute(select(Resident).where(Resident.id == data.resident_id))
        resident = resident_result.scalar_one_or_none()
        if not resident:
            raise HTTPException(status_code=400, detail="Resident not found")

    # Previous reading for variance (same resident if resident_id provided, else same room/building)
    prev_query = select(MeterReading).where(
        MeterReading.building == data.building,
        MeterReading.reading_date < data.reading_date
    )
    if data.resident_id:
        prev_query = prev_query.where(MeterReading.resident_id == data.resident_id)
    elif data.room_id:
        prev_query = prev_query.where(MeterReading.room_id == data.room_id)
    prev_query = prev_query.order_by(MeterReading.reading_date.desc()).limit(1)

    prev_result = await db.execute(prev_query)
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
        room_id=data.room_id,
        resident_id=data.resident_id,
        reading_date=data.reading_date,
        electric_reading=data.electric_reading,
        water_reading=data.water_reading,
        variance_pct=variance_pct,
        status=status,
    )
    db.add(reading)
    await db.commit()
    await db.refresh(reading)

    # Attach related data for response
    bed = None
    if resident and resident.bed_id:
        bed_result = await db.execute(select(Bed).where(Bed.id == resident.bed_id))
        bed = bed_result.scalar_one_or_none()

    out = MeterReadingOut(
        id=reading.id,
        building=reading.building,
        room_id=reading.room_id,
        resident_id=reading.resident_id,
        reading_date=reading.reading_date,
        electric_reading=reading.electric_reading,
        water_reading=reading.water_reading,
        status=reading.status,
        variance_pct=reading.variance_pct,
        room_number=room.room_number if room else None,
        resident_name=resident.full_name if resident else None,
        bed_code=bed.bed_code if bed else None,
    )
    return out


@router.post("/generate", response_model=List[BillingOut])
async def generate_billings(data: BillingGenerateRequest, db: AsyncSession = Depends(get_db)):
    residents_by_room, no_room, all_rows = await _get_active_residents_with_rooms(db, data.building)
    if not all_rows:
        raise HTTPException(status_code=400, detail="No active residents found")

    resident_electric = await _compute_resident_electric(db, data.billing_period, data.building)
    resident_water, total_days, rate_per_day = await _compute_water_by_days(
        db, data.billing_period, data.total_water_bill, data.building
    )

    total_residents = len(all_rows)
    other_per_head = data.other_charges / total_residents if total_residents > 0 else Decimal("0")

    billings = []

    # Residents with rooms
    for room_id, room_data in residents_by_room.items():
        room_residents = room_data["residents"]

        for resident, bed in room_residents:
            rid = str(resident.id)
            elec = resident_electric.get(rid, Decimal("0"))
            wat = resident_water.get(rid, Decimal("0"))
            total = resident.monthly_rate + elec + wat + other_per_head
            billing = Billing(
                resident_id=resident.id,
                billing_period=data.billing_period,
                rent_amount=resident.monthly_rate,
                electric_charge=elec,
                water_charge=wat,
                other_charges=other_per_head,
                total_amount=total,
                variance_pct=Decimal("0"),
                status="draft",
            )
            db.add(billing)
            billings.append(billing)

    # Residents without a room (fallback: rent + other only, no utilities)
    for resident, bed in no_room:
        rid = str(resident.id)
        elec = resident_electric.get(rid, Decimal("0"))
        wat = resident_water.get(rid, Decimal("0"))
        total = resident.monthly_rate + elec + wat + other_per_head
        billing = Billing(
            resident_id=resident.id,
            billing_period=data.billing_period,
            rent_amount=resident.monthly_rate,
            electric_charge=elec,
            water_charge=wat,
            other_charges=other_per_head,
            total_amount=total,
            variance_pct=Decimal("0"),
            status="draft",
        )
        db.add(billing)
        billings.append(billing)

    await db.commit()
    for b in billings:
        await db.refresh(b)
    return billings


@router.post("/{billing_id}/approve", response_model=BillingOut)
async def approve_billing(billing_id: UUID, db: AsyncSession = Depends(get_db)):
    billing = await db.get(Billing, billing_id)
    if not billing:
        raise HTTPException(status_code=404, detail="Billing not found")
    billing.status = "approved"
    await db.commit()
    await db.refresh(billing)
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
    return billing


@router.get("/meter-readings/template")
async def download_meter_reading_template():
    template_path = os.path.join(os.path.dirname(__file__), "..", "templates", "meter_reading_template.xlsx")
    if not os.path.exists(template_path):
        raise HTTPException(status_code=404, detail="Template not found")
    with open(template_path, "rb") as f:
        data = f.read()
    return StreamingResponse(
        io.BytesIO(data),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=meter_reading_template.xlsx"}
    )


@router.post("/meter-readings/upload")
async def upload_meter_readings(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    if not file.filename.endswith((".xlsx", ".xls")):
        raise HTTPException(status_code=400, detail="Only Excel files (.xlsx, .xls) are allowed")

    try:
        import pandas as pd
        contents = await file.read()
        df = pd.read_excel(io.BytesIO(contents), sheet_name="Meter Readings")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to read Excel file: {str(e)}")

    required_cols = {"Branch Code", "Building", "Room Number", "Bed", "Resident Name",
                     "Reading Date (YYYY-MM-DD)", "Electric Reading (kWh)", "Water Reading (m³)"}
    missing = required_cols - set(df.columns)
    if missing:
        raise HTTPException(status_code=400, detail=f"Missing required columns: {', '.join(missing)}")

    # Pre-load rooms and residents for lookup
    rooms_result = await db.execute(select(Room))
    rooms = rooms_result.scalars().all()
    room_by_number = {r.room_number.strip().upper(): r for r in rooms}

    residents_result = await db.execute(
        select(Resident, Bed)
        .join(Bed, Resident.bed_id == Bed.id, isouter=True)
        .where(Resident.status == "active")
    )
    residents_rows = residents_result.all()
    resident_lookup = {}
    for resident, bed in residents_rows:
        key = (resident.full_name or "").strip().upper()
        resident_lookup[key] = resident
        if bed and bed.bed_code:
            resident_lookup[bed.bed_code.upper()] = resident

    imported = 0
    skipped = 0
    errors = []

    for idx, row in df.iterrows():
        if idx == 0 and str(row.get("Branch Code", "")).lower() in ("branch code", ""):
            continue

        building = str(row.get("Building", "")).strip() if pd.notna(row.get("Building")) else None
        room_number = str(row.get("Room Number", "")).strip() if pd.notna(row.get("Room Number")) else None
        resident_name = str(row.get("Resident Name", "")).strip() if pd.notna(row.get("Resident Name")) else None
        reading_date = _parse_date(row.get("Reading Date (YYYY-MM-DD)"))
        electric = _parse_decimal(row.get("Electric Reading (kWh)"))
        water = _parse_decimal(row.get("Water Reading (m³)"))

        if not building or not reading_date:
            skipped += 1
            continue
        if electric is None and water is None:
            skipped += 1
            continue

        room_id = None
        if room_number:
            room = room_by_number.get(room_number.upper())
            if room:
                room_id = room.id
            else:
                errors.append(f"Row {idx + 1}: Room '{room_number}' not found")

        resident_id = None
        if resident_name:
            resident = resident_lookup.get(resident_name.upper())
            if resident:
                resident_id = resident.id

        prev_query = select(MeterReading).where(
            MeterReading.building == building,
            MeterReading.reading_date < reading_date
        )
        if resident_id:
            prev_query = prev_query.where(MeterReading.resident_id == resident_id)
        elif room_id:
            prev_query = prev_query.where(MeterReading.room_id == room_id)
        prev_query = prev_query.order_by(MeterReading.reading_date.desc()).limit(1)

        prev_result = await db.execute(prev_query)
        prev = prev_result.scalar_one_or_none()

        variance_pct = Decimal("0")
        if prev:
            prev_electric = prev.electric_reading or Decimal("0")
            prev_water = prev.water_reading or Decimal("0")
            curr_electric = electric or Decimal("0")
            curr_water = water or Decimal("0")
            prev_total = prev_electric + prev_water
            curr_total = curr_electric + curr_water
            if prev_total > 0:
                variance_pct = ((curr_total - prev_total) / prev_total) * 100

        status = "pending" if variance_pct > 20 else "approved"

        reading = MeterReading(
            building=building,
            room_id=room_id,
            resident_id=resident_id,
            reading_date=reading_date,
            electric_reading=electric,
            water_reading=water,
            variance_pct=variance_pct,
            status=status,
        )
        db.add(reading)
        imported += 1

    await db.commit()
    return {
        "imported": imported,
        "skipped": skipped,
        "errors": errors,
        "message": f"Imported {imported} meter readings. Skipped {skipped} rows."
    }


@router.get("/meter-readings", response_model=List[MeterReadingOut])
async def list_meter_readings(
    building: Optional[str] = Query(None),
    resident_id: Optional[UUID] = Query(None),
    year: Optional[int] = Query(None),
    month: Optional[int] = Query(None),
    limit: int = Query(1000, ge=1, le=5000),
    db: AsyncSession = Depends(get_db),
):
    query = (
        select(MeterReading, Room, Resident, Bed)
        .join(Room, MeterReading.room_id == Room.id, isouter=True)
        .join(Resident, MeterReading.resident_id == Resident.id, isouter=True)
        .join(Bed, Resident.bed_id == Bed.id, isouter=True)
        .order_by(MeterReading.reading_date.desc())
    )
    if building:
        query = query.where(MeterReading.building == building)
    if resident_id:
        query = query.where(MeterReading.resident_id == resident_id)
    if year and month:
        start = date(year, month, 1)
        if month == 12:
            end = date(year + 1, 1, 1)
        else:
            end = date(year, month + 1, 1)
        query = query.where(MeterReading.reading_date >= start, MeterReading.reading_date < end)

    query = query.limit(limit)
    result = await db.execute(query)
    rows = result.all()

    out = []
    for reading, room, resident, bed in rows:
        out.append(MeterReadingOut(
            id=reading.id,
            building=reading.building,
            room_id=reading.room_id,
            resident_id=reading.resident_id,
            reading_date=reading.reading_date,
            electric_reading=reading.electric_reading,
            water_reading=reading.water_reading,
            status=reading.status,
            variance_pct=reading.variance_pct,
            room_number=room.room_number if room else None,
            resident_name=resident.full_name if resident else None,
            bed_code=bed.bed_code if bed else None,
        ))
    return out


@router.get("/meter-readings/daily-grid", response_model=MeterReadingDailyGridOut)
async def get_daily_meter_grid(
    year: int = Query(...),
    month: int = Query(...),
    building: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    start_date = date(year, month, 1)
    if month == 12:
        end_date = date(year + 1, 1, 1)
    else:
        end_date = date(year, month + 1, 1)
    days_in_month = calendar.monthrange(year, month)[1]

    # Fetch active residents with bed/room info
    query = (
        select(Resident, Bed, Room)
        .join(Bed, Resident.bed_id == Bed.id, isouter=True)
        .join(Room, Bed.room_id == Room.id, isouter=True)
        .where(Resident.status == "active")
    )
    if building:
        query = query.where(Room.building == building)
    query = query.order_by(Room.room_number.asc().nullslast(), Bed.bed_number.asc().nullslast())
    result = await db.execute(query)
    rows = result.all()

    # Fetch meter readings for the period
    reading_query = select(MeterReading).where(
        MeterReading.reading_date >= start_date,
        MeterReading.reading_date < end_date,
        MeterReading.resident_id.isnot(None),
    )
    if building:
        reading_query = reading_query.where(MeterReading.building == building)
    reading_result = await db.execute(reading_query)
    readings = reading_result.scalars().all()

    # Index readings by resident_id and date
    readings_map = {}
    for r in readings:
        rid = str(r.resident_id)
        dkey = r.reading_date.strftime("%Y-%m-%d")
        if rid not in readings_map:
            readings_map[rid] = {}
        readings_map[rid][dkey] = MeterReadingDailyCell(
            reading_id=r.id,
            electric_reading=r.electric_reading,
            water_reading=r.water_reading,
            status=r.status,
        )

    residents_out = []
    for resident, bed, room in rows:
        rid = str(resident.id)
        days = _count_days_stayed(resident.move_in_date, resident.move_out_date, start_date, end_date)
        bed_letter = None
        if bed and bed.bed_code:
            bed_letter = bed.bed_code[-1] if len(bed.bed_code) > 0 else None

        residents_out.append(MeterReadingDailyRow(
            resident_id=resident.id,
            resident_name=resident.full_name,
            room_number=room.room_number if room else None,
            bed_code=bed.bed_code if bed else None,
            bed_letter=bed_letter,
            monthly_rate=resident.monthly_rate,
            move_in_date=resident.move_in_date,
            move_out_date=resident.move_out_date,
            days_in_month=days,
            readings=readings_map.get(rid, {}),
        ))

    return MeterReadingDailyGridOut(
        year=year,
        month=month,
        days_in_month=days_in_month,
        residents=residents_out,
        water_config={},
    )


@router.post("/meter-readings/bulk-upsert")
async def bulk_upsert_meter_readings(
    data: List[MeterReadingCreate],
    db: AsyncSession = Depends(get_db),
):
    """Bulk upsert daily meter readings (used by the grid UI)."""
    created = 0
    updated = 0
    for item in data:
        if not item.resident_id or not item.reading_date:
            continue

        # Check if reading already exists for this resident + date
        existing_query = select(MeterReading).where(
            MeterReading.resident_id == item.resident_id,
            MeterReading.reading_date == item.reading_date,
        )
        existing_result = await db.execute(existing_query)
        existing = existing_result.scalar_one_or_none()

        if existing:
            if item.electric_reading is not None:
                existing.electric_reading = item.electric_reading
            if item.water_reading is not None:
                existing.water_reading = item.water_reading
            updated += 1
        else:
            reading = MeterReading(
                building=item.building,
                room_id=item.room_id,
                resident_id=item.resident_id,
                reading_date=item.reading_date,
                electric_reading=item.electric_reading,
                water_reading=item.water_reading,
                variance_pct=Decimal("0"),
                status="approved",
            )
            db.add(reading)
            created += 1

    await db.commit()
    return {"created": created, "updated": updated}


@router.post("/preview", response_model=BillingPreviewResponse)
async def preview_billings(data: BillingGenerateRequest, db: AsyncSession = Depends(get_db)):
    residents_by_room, no_room, all_rows = await _get_active_residents_with_rooms(db, data.building)
    if not all_rows:
        raise HTTPException(status_code=400, detail="No active residents found")

    resident_electric = await _compute_resident_electric(db, data.billing_period, data.building)
    resident_water, total_days, rate_per_day = await _compute_water_by_days(
        db, data.billing_period, data.total_water_bill, data.building
    )

    total_residents = len(all_rows)
    other_per_head = data.other_charges / total_residents if total_residents > 0 else Decimal("0")

    preview_rows = []
    total_rent = Decimal("0")
    total_electric = Decimal("0")
    total_water = Decimal("0")
    total_other = Decimal("0")
    total_all = Decimal("0")

    # Residents with rooms
    for room_id, room_data in residents_by_room.items():
        room = room_data["room"]
        room_residents = room_data["residents"]

        for resident, bed in room_residents:
            rid = str(resident.id)
            elec = resident_electric.get(rid, Decimal("0"))
            wat = resident_water.get(rid, Decimal("0"))
            total = resident.monthly_rate + elec + wat + other_per_head
            preview_rows.append(BillingPreviewRow(
                resident_id=resident.id,
                resident_name=resident.full_name,
                room_number=room.room_number if room else None,
                bed_number=bed.bed_number if bed else None,
                bed_code=bed.bed_code if bed else None,
                monthly_rate=resident.monthly_rate,
                rent_amount=resident.monthly_rate,
                electric_charge=elec,
                water_charge=wat,
                other_charges=other_per_head,
                total_amount=total,
            ))
            total_rent += resident.monthly_rate
            total_electric += elec
            total_water += wat
            total_other += other_per_head
            total_all += total

    # Residents without a room
    for resident, bed in no_room:
        rid = str(resident.id)
        elec = resident_electric.get(rid, Decimal("0"))
        wat = resident_water.get(rid, Decimal("0"))
        total = resident.monthly_rate + elec + wat + other_per_head
        preview_rows.append(BillingPreviewRow(
            resident_id=resident.id,
            resident_name=resident.full_name,
            room_number=None,
            bed_number=bed.bed_number if bed else None,
            bed_code=bed.bed_code if bed else None,
            monthly_rate=resident.monthly_rate,
            rent_amount=resident.monthly_rate,
            electric_charge=elec,
            water_charge=wat,
            other_charges=other_per_head,
            total_amount=total,
        ))
        total_rent += resident.monthly_rate
        total_electric += elec
        total_water += wat
        total_other += other_per_head
        total_all += total

    return BillingPreviewResponse(
        billing_period=data.billing_period,
        building=data.building,
        total_residents=total_residents,
        rows=preview_rows,
        summary={
            "total_rent": str(total_rent),
            "total_electric": str(total_electric),
            "total_water": str(total_water),
            "total_other": str(total_other),
            "grand_total": str(total_all),
            "electric_per_head": str(total_electric / total_residents if total_residents > 0 else Decimal("0")),
            "water_per_head": str(total_water / total_residents if total_residents > 0 else Decimal("0")),
            "other_per_head": str(other_per_head),
            "total_days": total_days,
            "water_rate_per_day": str(rate_per_day),
        }
    )


@router.get("/", response_model=List[BillingWithResidentOut])
async def list_billings(
    resident_id: Optional[UUID] = Query(None),
    status: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    query = (
        select(Billing, Resident, Bed, Room)
        .join(Resident, Billing.resident_id == Resident.id)
        .join(Bed, Resident.bed_id == Bed.id, isouter=True)
        .join(Room, Bed.room_id == Room.id, isouter=True)
    )
    if resident_id:
        query = query.where(Billing.resident_id == resident_id)
    if status:
        query = query.where(Billing.status == status)
    query = query.order_by(Billing.created_at.desc())
    result = await db.execute(query)
    rows = result.all()

    out = []
    for billing, resident, bed, room in rows:
        out.append(BillingWithResidentOut(
            id=billing.id,
            resident_id=billing.resident_id,
            billing_period=billing.billing_period,
            rent_amount=billing.rent_amount,
            electric_charge=billing.electric_charge,
            water_charge=billing.water_charge,
            other_charges=billing.other_charges,
            total_amount=billing.total_amount,
            status=billing.status,
            created_at=billing.created_at,
            resident_name=resident.full_name if resident else None,
            bed_code=bed.bed_code if bed else None,
            room_number=room.room_number if room else None,
        ))
    return out
