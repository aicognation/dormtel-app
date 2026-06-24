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
from app import models, auth
from app.models import MeterReading, MeterReadingImport, Billing, Resident, Room, Bed
from app.schemas import (
    MeterReadingCreate, MeterReadingOut, MeterReadingDailyGridOut,
    MeterReadingDailyRow, MeterReadingDailyCell,
    BillingOut, BillingWithResidentOut,
    MeterReadingUploadResult, MeterReadingDailySheetResult,
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
    other_charges: Optional[Decimal] = Field(default=Decimal("0"), ge=0)
    total_water_bill: Optional[Decimal] = Field(default=Decimal("0"), ge=0)


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
    """Sum per-resident electric meter readings for the billing period.
    If a daily-sheet import exists for the resident, use the pre-computed total."""
    year, month = map(int, billing_period.split("-"))
    start_date = date(year, month, 1)
    if month == 12:
        end_date = date(year + 1, 1, 1)
    else:
        end_date = date(year, month + 1, 1)

    # Check for imported daily-sheet totals first
    import_query = select(MeterReadingImport)
    if building:
        import_query = import_query.where(MeterReadingImport.building == building)
    import_query = import_query.where(
        MeterReadingImport.year == year,
        MeterReadingImport.month == month,
    )
    import_result = await db.execute(import_query)
    imports = import_result.scalars().all()

    resident_electric = {}
    imported_residents = set()
    for imp in imports:
        rid = str(imp.resident_id)
        if imp.total_electric_usage is not None:
            resident_electric[rid] = imp.total_electric_usage
            imported_residents.add(rid)

    # Build active resident -> room map so room-level readings can be split
    resident_room_query = (
        select(Resident, Bed, Room)
        .join(Bed, Resident.bed_id == Bed.id, isouter=True)
        .join(Room, Bed.room_id == Room.id, isouter=True)
        .where(Resident.status == "active")
    )
    if building:
        resident_room_query = resident_room_query.where(Room.building == building)
    resident_room_result = await db.execute(resident_room_query)
    room_to_residents = {}
    resident_to_room = {}
    for resident, bed, room in resident_room_result.all():
        rid = str(resident.id)
        if room:
            room_id = str(room.id)
            resident_to_room[rid] = room_id
            room_to_residents.setdefault(room_id, []).append(rid)

    # For residents without an import, fall back to summing meter readings
    query = select(MeterReading).where(
        MeterReading.reading_date >= start_date,
        MeterReading.reading_date < end_date,
    )
    if building:
        query = query.where(MeterReading.building == building)

    result = await db.execute(query)
    readings = result.scalars().all()

    for reading in readings:
        elec = reading.electric_reading or Decimal("0")
        if reading.resident_id:
            rid = str(reading.resident_id)
            if rid in imported_residents:
                continue
            resident_electric[rid] = resident_electric.get(rid, Decimal("0")) + elec
        elif reading.room_id:
            room_id = str(reading.room_id)
            rids = room_to_residents.get(room_id, [])
            if rids:
                split = elec / len(rids)
                for rid in rids:
                    if rid in imported_residents:
                        continue
                    resident_electric[rid] = resident_electric.get(rid, Decimal("0")) + split

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
    total_water_bill: Optional[Decimal] = None,
    building: Optional[str] = None,
):
    """Compute water charge per resident based on days stayed.
    If a daily-sheet import exists with a water_bill, use it directly."""
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

    # Check for imported water bills
    import_query = select(MeterReadingImport)
    if building:
        import_query = import_query.where(MeterReadingImport.building == building)
    import_query = import_query.where(
        MeterReadingImport.year == year,
        MeterReadingImport.month == month,
    )
    import_result = await db.execute(import_query)
    imports = import_result.scalars().all()

    imported_water = {str(imp.resident_id): imp.water_bill for imp in imports if imp.water_bill is not None}

    total_days = 0
    resident_days = {}
    for resident, bed, room in rows:
        days = _count_days_stayed(resident.move_in_date, resident.move_out_date, start_date, end_date)
        total_days += days
        resident_days[str(resident.id)] = days

    effective_total_water = total_water_bill if total_water_bill is not None else Decimal("0")
    rate_per_day = effective_total_water / total_days if total_days > 0 else Decimal("0")

    resident_water = {}
    for rid, days in resident_days.items():
        if rid in imported_water:
            resident_water[rid] = imported_water[rid]
        else:
            resident_water[rid] = Decimal(str(days)) * rate_per_day

    return resident_water, total_days, rate_per_day


async def _compute_other_charges(
    db: AsyncSession,
    billing_period: str,
    other_charges_input: Optional[Decimal] = None,
    building: Optional[str] = None,
):
    """Compute other charges per resident.
    If daily-sheet imports have misc_charges, use those per resident.
    Otherwise divide the input other_charges equally."""
    year, month = map(int, billing_period.split("-"))

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

    # Check for imported misc charges
    import_query = select(MeterReadingImport)
    if building:
        import_query = import_query.where(MeterReadingImport.building == building)
    import_query = import_query.where(
        MeterReadingImport.year == year,
        MeterReadingImport.month == month,
    )
    import_result = await db.execute(import_query)
    imports = import_result.scalars().all()

    imported_misc = {}
    for imp in imports:
        if imp.misc_charges:
            total_misc = Decimal("0")
            for key, val in imp.misc_charges.items():
                try:
                    total_misc += Decimal(str(val))
                except Exception:
                    pass
            if total_misc > 0:
                imported_misc[str(imp.resident_id)] = total_misc

    total_residents = len(rows)
    fallback_per_head = (other_charges_input or Decimal("0")) / total_residents if total_residents > 0 else Decimal("0")

    resident_other = {}
    for resident, bed, room in rows:
        rid = str(resident.id)
        if rid in imported_misc:
            resident_other[rid] = imported_misc[rid]
        else:
            resident_other[rid] = fallback_per_head

    return resident_other, total_residents, fallback_per_head


@router.post("/meter-readings", response_model=MeterReadingOut)
async def submit_meter_reading(
    data: MeterReadingCreate,
    current_staff: models.Staff = Depends(auth.require_staff),
    db: AsyncSession = Depends(get_db),
):
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
async def generate_billings(
    data: BillingGenerateRequest,
    current_staff: models.Staff = Depends(auth.require_staff),
    db: AsyncSession = Depends(get_db),
):
    residents_by_room, no_room, all_rows = await _get_active_residents_with_rooms(db, data.building)
    if not all_rows:
        detail = f"No active residents found" + (f" for building '{data.building}'" if data.building else "")
        raise HTTPException(status_code=400, detail=detail)

    # Idempotency: do not duplicate billings for the same period
    resident_ids = [str(resident.id) for resident, bed, room in all_rows]
    existing_result = await db.execute(
        select(Billing).where(
            Billing.billing_period == data.billing_period,
            Billing.resident_id.in_(resident_ids),
        )
    )
    existing = existing_result.scalars().all()
    if existing:
        return existing

    resident_electric = await _compute_resident_electric(db, data.billing_period, data.building)
    resident_water, total_days, rate_per_day = await _compute_water_by_days(
        db, data.billing_period, data.total_water_bill, data.building
    )
    resident_other, total_residents, fallback_per_head = await _compute_other_charges(
        db, data.billing_period, data.other_charges, data.building
    )

    billings = []

    # Residents with rooms
    for room_id, room_data in residents_by_room.items():
        room_residents = room_data["residents"]

        for resident, bed in room_residents:
            rid = str(resident.id)
            elec = resident_electric.get(rid, Decimal("0"))
            wat = resident_water.get(rid, Decimal("0"))
            other = resident_other.get(rid, fallback_per_head)
            total = resident.monthly_rate + elec + wat + other
            billing = Billing(
                resident_id=resident.id,
                billing_period=data.billing_period,
                rent_amount=resident.monthly_rate,
                electric_charge=elec,
                water_charge=wat,
                other_charges=other,
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
        other = resident_other.get(rid, fallback_per_head)
        total = resident.monthly_rate + elec + wat + other
        billing = Billing(
            resident_id=resident.id,
            billing_period=data.billing_period,
            rent_amount=resident.monthly_rate,
            electric_charge=elec,
            water_charge=wat,
            other_charges=other,
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
async def approve_billing(
    billing_id: UUID,
    current_staff: models.Staff = Depends(auth.require_staff),
    db: AsyncSession = Depends(get_db),
):
    billing = await db.get(Billing, billing_id)
    if not billing:
        raise HTTPException(status_code=404, detail="Billing not found")
    billing.status = "approved"
    await db.commit()
    await db.refresh(billing)
    return billing


@router.post("/{billing_id}/distribute", response_model=BillingOut)
async def distribute_billing(
    billing_id: UUID,
    current_staff: models.Staff = Depends(auth.require_staff),
    db: AsyncSession = Depends(get_db),
):
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
async def download_meter_reading_template(
    current_staff: models.Staff = Depends(auth.require_staff),
):
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


@router.post("/meter-readings/upload", response_model=MeterReadingUploadResult)
async def upload_meter_readings(
    file: UploadFile = File(...),
    current_staff: models.Staff = Depends(auth.require_staff),
    db: AsyncSession = Depends(get_db),
):
    if not file.filename.endswith((".xlsx", ".xls")):
        raise HTTPException(status_code=400, detail="Only Excel files (.xlsx, .xls) are allowed")

    try:
        from openpyxl import load_workbook
        contents = await file.read()
        wb = load_workbook(io.BytesIO(contents), data_only=True)
        ws = wb["Meter Readings"]
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to read Excel file: {str(e)}")

    # Read headers from first row
    headers = [cell.value for cell in ws[1]]
    header_map = {h: i for i, h in enumerate(headers) if h}

    required_cols = {"Branch Code", "Building", "Room Number", "Bed", "Resident Name",
                     "Reading Date (YYYY-MM-DD)", "Electric Reading (kWh)", "Water Reading (m³)"}
    missing = required_cols - set(header_map.keys())
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

    for row in ws.iter_rows(min_row=2, values_only=True):
        if not row or row[0] is None:
            continue

        building = str(row[header_map.get("Building")]).strip() if header_map.get("Building") is not None and row[header_map.get("Building")] is not None else None
        room_number = str(row[header_map.get("Room Number")]).strip() if header_map.get("Room Number") is not None and row[header_map.get("Room Number")] is not None else None
        resident_name = str(row[header_map.get("Resident Name")]).strip() if header_map.get("Resident Name") is not None and row[header_map.get("Resident Name")] is not None else None
        reading_date = _parse_date(row[header_map.get("Reading Date (YYYY-MM-DD)")])
        electric = _parse_decimal(row[header_map.get("Electric Reading (kWh)")])
        water = _parse_decimal(row[header_map.get("Water Reading (m³)")])

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
                errors.append(f"Room '{room_number}' not found")

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
    return MeterReadingUploadResult(
        imported=imported,
        skipped=skipped,
        errors=errors,
        message=f"Imported {imported} meter readings. Skipped {skipped} rows."
    )


@router.post("/meter-readings/upload-daily-sheet", response_model=MeterReadingDailySheetResult)
async def upload_daily_meter_sheet(
    file: UploadFile = File(...),
    current_staff: models.Staff = Depends(auth.require_staff),
    db: AsyncSession = Depends(get_db),
):
    """Upload a daily meter reading Excel per dormer (e.g. '05_DORMERS ELEC & WATER - MAY 2026').

    The workbook is expected to have one sheet per building (e.g. DT01, DT02).
    Row 2 contains headers; daily date columns are detected automatically.
    Row 1 may contain a month/year title that we also parse as a fallback.
    """
    if not file.filename.endswith((".xlsx", ".xls")):
        raise HTTPException(status_code=400, detail="Only Excel files (.xlsx, .xls) are allowed")

    try:
        from openpyxl import load_workbook
        contents = await file.read()
        wb = load_workbook(io.BytesIO(contents), data_only=True)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to read Excel file: {str(e)}")

    # Pre-load rooms and residents for matching
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

    total_residents_imported = 0
    total_daily_readings = 0
    all_errors = []

    for sheet_name in wb.sheetnames:
        ws = wb[sheet_name]
        building = sheet_name.strip()
        if not building:
            continue

        # Auto-detect header row by finding the row with the most datetime values
        header_row_idx = None
        header_row = None
        max_dates = 0
        for r_idx in range(1, min(6, ws.max_row + 1)):
            row_vals = list(ws.iter_rows(min_row=r_idx, max_row=r_idx, values_only=True))[0]
            date_count = sum(1 for v in row_vals if isinstance(v, datetime))
            if date_count > max_dates:
                max_dates = date_count
                header_row_idx = r_idx
                header_row = row_vals

        if not header_row:
            all_errors.append(f"Sheet '{sheet_name}': Could not detect header row with date columns.")
            continue

        # Build header map from header row for robust column detection
        header_map = {}
        for idx, val in enumerate(header_row):
            if val is not None:
                header_map[str(val).upper().strip()] = idx

        date_cols = []  # list of (col_index, date_value)
        col_total_usage = None
        col_water_days = None
        col_water_bill = None
        col_water_rate = None
        col_misc = {}

        for idx, val in enumerate(header_row):
            if val is None:
                continue
            if isinstance(val, datetime):
                date_cols.append((idx, val))
            elif isinstance(val, str):
                vup = val.upper().strip()
                if vup == "TOTAL USAGE":
                    col_total_usage = idx
                elif "# OF DAYS" in vup and "WATER" in vup:
                    col_water_days = idx
                elif vup == "WATER BILL":
                    col_water_bill = idx
                elif vup == "RATE" and col_water_days is not None:
                    # RATE column that appears after water days = water rate
                    col_water_rate = idx
                elif vup in {"LAUNDRY", "DRINKING WATER", "ICE CREAM", "HONESTY STORE", "COFFEE", "LOST KEYCARD", "REF RENTAL", "LAUNDRY DORM"}:
                    col_misc[vup] = idx

        if not date_cols:
            all_errors.append(f"Sheet '{sheet_name}': No date columns found in header row.")
            continue

        # Filter out stray date columns from misc sections (large gap from contiguous block)
        filtered_date_cols = []
        for idx, d in date_cols:
            if not filtered_date_cols:
                filtered_date_cols.append((idx, d))
            else:
                gap = abs((d - filtered_date_cols[-1][1]).days)
                if gap <= 60:
                    filtered_date_cols.append((idx, d))
                else:
                    break
        date_cols = filtered_date_cols

        # Determine year/month from the most common month among date columns
        from collections import Counter
        month_counts = Counter([d.month for _, d in date_cols])
        year = date_cols[0][1].year
        month = month_counts.most_common(1)[0][0]

        # Detect column layout: new format has 'BED' header at col 2
        # Old format: room(0), bed(1), name(2), rate(3), move_in(4), move_out(5)
        # New format: room(0), flag(1), bed(2), name(3), rate(4), move_in(5), move_out(6)
        has_bed_header = "BED" in header_map
        bed_col = 2 if has_bed_header else 1
        name_col = 3 if has_bed_header else 2
        rate_col = 4 if has_bed_header else 3
        move_in_col = 5 if has_bed_header else 4
        move_out_col = 6 if has_bed_header else 5

        sheet_residents = 0
        sheet_readings = 0
        current_room = None

        for row in ws.iter_rows(min_row=header_row_idx + 1, values_only=True):
            if not row:
                continue

            # Room number may be on its own row or repeated; forward-fill
            if row[0] is not None:
                try:
                    current_room = str(int(row[0]))
                except (ValueError, TypeError):
                    current_room = str(row[0]).strip()

            room_number = current_room
            bed_letter = str(row[bed_col]).strip() if row[bed_col] is not None else None
            resident_name = str(row[name_col]).strip() if row[name_col] is not None else None
            rate = _parse_decimal(row[rate_col]) if len(row) > rate_col else None
            move_in = _parse_date(row[move_in_col]) if len(row) > move_in_col else None
            move_out = _parse_date(row[move_out_col]) if len(row) > move_out_col else None

            if not resident_name:
                continue

            # Match resident
            resident = resident_lookup.get(resident_name.upper())
            if not resident and bed_letter and room_number:
                bed_code = f"{room_number}{bed_letter}".upper()
                resident = resident_lookup.get(bed_code)

            if not resident:
                all_errors.append(f"Sheet '{sheet_name}': Resident '{resident_name}' not found (room {room_number}, bed {bed_letter}).")
                continue

            # Extract pre-computed totals
            total_usage = _parse_decimal(row[col_total_usage]) if col_total_usage is not None and len(row) > col_total_usage else None
            water_days = None
            if col_water_days is not None and len(row) > col_water_days:
                try:
                    water_days = int(row[col_water_days])
                except (ValueError, TypeError):
                    water_days = None
            water_bill = _parse_decimal(row[col_water_bill]) if col_water_bill is not None and len(row) > col_water_bill else None

            misc_charges = {}
            for misc_name, col_idx in col_misc.items():
                if len(row) > col_idx and row[col_idx] is not None:
                    try:
                        val = Decimal(str(row[col_idx]))
                        if val > 0:
                            misc_charges[misc_name.lower().replace(" ", "_")] = str(val)
                    except Exception:
                        pass

            # Upsert summary import record
            existing_import_query = select(MeterReadingImport).where(
                MeterReadingImport.resident_id == resident.id,
                MeterReadingImport.year == year,
                MeterReadingImport.month == month,
            )
            existing_import_result = await db.execute(existing_import_query)
            existing_import = existing_import_result.scalar_one_or_none()

            water_rate_val = _parse_decimal(row[col_water_rate]) if col_water_rate is not None and len(row) > col_water_rate else None

            if existing_import:
                existing_import.building = building
                existing_import.total_electric_usage = total_usage
                existing_import.water_bill = water_bill
                existing_import.water_days = water_days
                existing_import.water_rate = water_rate_val
                existing_import.misc_charges = misc_charges if misc_charges else None
                existing_import.source_filename = file.filename
            else:
                imp = MeterReadingImport(
                    resident_id=resident.id,
                    building=building,
                    year=year,
                    month=month,
                    total_electric_usage=total_usage,
                    water_bill=water_bill,
                    water_days=water_days,
                    water_rate=water_rate_val,
                    misc_charges=misc_charges if misc_charges else None,
                    source_filename=file.filename,
                )
                db.add(imp)

            sheet_residents += 1

            # Import daily readings into meter_readings (store cumulative values for reference)
            room_id = None
            if room_number:
                room = room_by_number.get(room_number.upper())
                if room:
                    room_id = room.id

            for col_idx, col_date in date_cols:
                if col_idx >= len(row):
                    continue
                val = row[col_idx]
                if val is None:
                    continue
                try:
                    reading_val = Decimal(str(val))
                except Exception:
                    continue

                # Upsert meter reading for this date
                existing_reading_query = select(MeterReading).where(
                    MeterReading.resident_id == resident.id,
                    MeterReading.reading_date == col_date.date() if isinstance(col_date, datetime) else col_date,
                )
                existing_reading_result = await db.execute(existing_reading_query)
                existing_reading = existing_reading_result.scalar_one_or_none()

                if existing_reading:
                    existing_reading.electric_reading = reading_val
                    existing_reading.building = building
                    existing_reading.room_id = room_id
                else:
                    reading = MeterReading(
                        building=building,
                        room_id=room_id,
                        resident_id=resident.id,
                        reading_date=col_date.date() if isinstance(col_date, datetime) else col_date,
                        electric_reading=reading_val,
                        water_reading=None,
                        status="estimated",
                        variance_pct=Decimal("0"),
                    )
                    db.add(reading)
                sheet_readings += 1

        total_residents_imported += sheet_residents
        total_daily_readings += sheet_readings

    await db.commit()
    return MeterReadingDailySheetResult(
        building=", ".join(wb.sheetnames),
        year=year,
        month=month,
        residents_imported=total_residents_imported,
        daily_readings_imported=total_daily_readings,
        errors=all_errors,
        message=f"Imported {total_residents_imported} residents with {total_daily_readings} daily readings across {len(wb.sheetnames)} sheet(s)."
    )


@router.get("/meter-readings", response_model=List[MeterReadingOut])
async def list_meter_readings(
    building: Optional[str] = Query(None),
    resident_id: Optional[UUID] = Query(None),
    year: Optional[int] = Query(None),
    month: Optional[int] = Query(None),
    limit: int = Query(1000, ge=1, le=5000),
    current_staff: models.Staff = Depends(auth.require_staff),
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
    current_staff: models.Staff = Depends(auth.require_staff),
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
    current_staff: models.Staff = Depends(auth.require_staff),
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
async def preview_billings(
    data: BillingGenerateRequest,
    current_staff: models.Staff = Depends(auth.require_staff),
    db: AsyncSession = Depends(get_db),
):
    residents_by_room, no_room, all_rows = await _get_active_residents_with_rooms(db, data.building)
    if not all_rows:
        detail = f"No active residents found" + (f" for building '{data.building}'" if data.building else "")
        raise HTTPException(status_code=400, detail=detail)

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
    current_staff: models.Staff = Depends(auth.require_staff),
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
