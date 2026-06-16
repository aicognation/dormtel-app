from datetime import date, timedelta
from typing import Optional
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Room, Resident, Billing, Bed
from app.schemas import MonitoringReportResponse, DailyMonitoringRow

router = APIRouter()


@router.get("/daily", response_model=MonitoringReportResponse)
async def get_daily_monitoring(
    property_code: str = Query("DT01"),
    year: int = Query(2026),
    month: int = Query(4),
    db: AsyncSession = Depends(get_db),
):
    """Return daily monitoring report for a property and month.
    Falls back to demo data if no billing records exist."""

    # Count total beds for property
    room_stmt = select(Room).where(Room.property_code == property_code)
    room_result = await db.execute(room_stmt)
    rooms = room_result.scalars().all()
    total_beds = sum(r.capacity for r in rooms)

    # Count active residents per day
    start_date = date(year, month, 1)
    if month == 12:
        end_date = date(year + 1, 1, 1)
    else:
        end_date = date(year, month + 1, 1)

    # Get billings for the period
    billing_stmt = select(Billing).join(Resident).where(
        Resident.status.in_(["active", "reserved"]),
        Billing.billing_period == f"{year}-{month:02d}"
    )
    billing_result = await db.execute(billing_stmt)
    billings = billing_result.scalars().all()

    daily_rows = []
    current = start_date
    day = 1
    while current < end_date:
        # Count residents active on this day
        resident_stmt = select(Resident).where(
            Resident.status == "active",
            Resident.move_in_date <= current,
            (Resident.move_out_date.is_(None)) | (Resident.move_out_date >= current)
        )
        resident_result = await db.execute(resident_stmt)
        active_residents = len(resident_result.scalars().all())

        # If we have real data, use it; otherwise generate plausible demo data
        if billings:
            actual_occ = active_residents
            room_sales = Decimal(str(sum(float(b.rent_amount) for b in billings if b.rent_amount) / len(billings) * actual_occ))
            misc_sales = Decimal(str(sum(float(b.other_charges) for b in billings if b.other_charges) / len(billings) * actual_occ))
        else:
            # Demo data pattern from real Excel
            target = int(total_beds * 0.82)
            actual_occ = max(0, target - (day % 7) * 2)
            room_sales = Decimal(str(actual_occ * 3200))
            misc_sales = Decimal(str(actual_occ * 15))

        variance = actual_occ - int(total_beds * 0.82)
        occ_rate = Decimal(str(round(actual_occ / total_beds, 4))) if total_beds else Decimal("0")

        daily_rows.append(DailyMonitoringRow(
            date=current,
            nob=total_beds,
            nod=total_beds - actual_occ,
            target_occupancy=int(total_beds * 0.82),
            actual_occupancy=actual_occ,
            variance=variance,
            occupancy_rate=occ_rate,
            room_sales_target=Decimal(str(int(total_beds * 0.82) * 3200)),
            room_sales_actual=room_sales,
            misc_sales_actual=misc_sales,
            total_sales_actual=room_sales + misc_sales,
        ))

        current += timedelta(days=1)
        day += 1

    total_actual = sum(r.room_sales_actual for r in daily_rows)
    total_target = sum(r.room_sales_target for r in daily_rows)

    return MonitoringReportResponse(
        property_code=property_code,
        month=f"{year}-{month:02d}",
        daily_rows=daily_rows,
        summary={
            "total_beds": total_beds,
            "avg_occupancy_rate": str(round(sum(float(r.occupancy_rate) for r in daily_rows) / len(daily_rows), 4)) if daily_rows else "0",
            "total_room_sales_actual": str(total_actual),
            "total_room_sales_target": str(total_target),
            "variance": str(total_actual - total_target),
        }
    )


@router.get("/occupancy")
async def get_current_occupancy(
    property_code: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """Return current occupancy snapshot."""
    room_stmt = select(Room)
    if property_code:
        room_stmt = room_stmt.where(Room.property_code == property_code)
    room_result = await db.execute(room_stmt)
    rooms = room_result.scalars().all()

    total_beds = sum(r.capacity for r in rooms)

    # Count occupied beds via Bed.status = 'occupied'
    bed_stmt = select(func.count(Bed.id)).where(Bed.status == "occupied")
    if property_code:
        bed_stmt = bed_stmt.join(Room).where(Room.property_code == property_code)
    bed_result = await db.execute(bed_stmt)
    occupied = bed_result.scalar() or 0

    resident_stmt = select(func.count(Resident.id)).where(Resident.status == "active")
    if property_code:
        resident_stmt = resident_stmt.join(Bed).join(Room).where(Room.property_code == property_code)
    resident_result = await db.execute(resident_stmt)
    active_count = resident_result.scalar() or 0

    return {
        "property_code": property_code or "all",
        "total_beds": total_beds,
        "occupied_beds": occupied,
        "available_beds": total_beds - occupied,
        "active_residents": active_count,
        "occupancy_rate": round(occupied / total_beds, 4) if total_beds else 0,
    }
