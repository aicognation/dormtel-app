from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from typing import Optional
import calendar

from app.database import get_db
from app import models, schemas

router = APIRouter()


@router.get("/stats", response_model=schemas.DashboardStatsOut)
async def get_dashboard_stats(
    period: str = Query("monthly", regex="^(daily|weekly|monthly|ytd)$"),
    db: AsyncSession = Depends(get_db)
):
    today = date.today()

    if period == "daily":
        start = datetime.combine(today, time.min)
        end = datetime.combine(today, time.max)
    elif period == "weekly":
        start = datetime.combine(today - timedelta(days=today.weekday()), time.min)
        end = datetime.combine(today, time.max)
    elif period == "monthly":
        start = datetime.combine(today.replace(day=1), time.min)
        end = datetime.combine(today.replace(day=calendar.monthrange(today.year, today.month)[1]), time.max)
    elif period == "ytd":
        start = datetime.combine(date(today.year, 1, 1), time.min)
        end = datetime.combine(today, time.max)
    else:
        start = end = None

    # Revenue
    revenue_result = await db.execute(
        select(func.coalesce(func.sum(models.Payment.amount), Decimal("0")))
        .where(models.Payment.matched_at >= start, models.Payment.matched_at <= end)
    )
    revenue = revenue_result.scalar() or Decimal("0")

    # Dormers (active residents not yet moved out) — always a snapshot
    dormers_result = await db.execute(
        select(func.count(models.Resident.id))
        .where(
            models.Resident.status == "active",
            or_(
                models.Resident.move_out_date.is_(None),
                models.Resident.move_out_date >= today
            )
        )
    )
    dormers_count = dormers_result.scalar() or 0

    # Inquiries
    inquiries_result = await db.execute(
        select(func.count(models.Inquiry.id))
        .where(models.Inquiry.created_at >= start, models.Inquiry.created_at <= end)
    )
    inquiries = inquiries_result.scalar() or 0

    # Reservations
    reservations_result = await db.execute(
        select(func.count(models.Resident.id))
        .where(
            models.Resident.status == "reserved",
            models.Resident.created_at >= start,
            models.Resident.created_at <= end
        )
    )
    reservations = reservations_result.scalar() or 0

    # Pending Bills
    pending_statuses = ["pending_review", "approved", "distributed"]

    pending_result = await db.execute(
        select(
            func.coalesce(func.sum(models.Billing.total_amount), Decimal("0")),
            func.count(models.Billing.id)
        )
        .where(
            models.Billing.status.in_(pending_statuses),
            models.Billing.created_at >= start,
            models.Billing.created_at <= end
        )
    )
    pending_row = pending_result.one_or_none()
    pending_amount = pending_row[0] if pending_row else Decimal("0")
    pending_count = pending_row[1] if pending_row else 0

    # Scheduled Move-ins
    moveins_result = await db.execute(
        select(func.count(models.Resident.id))
        .where(
            models.Resident.status.in_(["reserved", "active"]),
            models.Resident.move_in_date >= start,
            models.Resident.move_in_date <= end
        )
    )
    moveins = moveins_result.scalar() or 0

    # Scheduled Move-outs
    moveouts_result = await db.execute(
        select(func.count(models.MoveOut.id))
        .where(
            models.MoveOut.status != "completed",
            models.MoveOut.requested_date >= start,
            models.MoveOut.requested_date <= end
        )
    )
    moveouts = moveouts_result.scalar() or 0

    return schemas.DashboardStatsOut(
        revenue=revenue,
        dormers=dormers_count,
        inquiries=inquiries,
        reservations=reservations,
        pending_bills=pending_amount,
        pending_bills_count=pending_count,
        scheduled_moveins=moveins,
        scheduled_moveouts=moveouts,
    )


@router.get("/events", response_model=list[schemas.DashboardEventOut])
async def get_dashboard_events(
    type: str = Query(..., regex="^(movein|moveout)$"),
    year: int = Query(...),
    month: int = Query(...),
    db: AsyncSession = Depends(get_db),
):
    start_date = date(year, month, 1)
    if month == 12:
        end_date = date(year + 1, 1, 1)
    else:
        end_date = date(year, month + 1, 1)

    events = []

    if type == "movein":
        result = await db.execute(
            select(models.Resident, models.Bed)
            .join(models.Bed, models.Resident.bed_id == models.Bed.id, isouter=True)
            .where(
                models.Resident.status.in_(["reserved", "active"]),
                models.Resident.move_in_date >= start_date,
                models.Resident.move_in_date < end_date
            )
            .order_by(models.Resident.move_in_date)
        )
        rows = result.all()

        from collections import defaultdict
        by_date = defaultdict(list)
        for resident, bed in rows:
            by_date[resident.move_in_date].append(
                schemas.DashboardEventResident(
                    id=resident.id,
                    full_name=resident.full_name,
                    bed_code=bed.bed_code if bed else ""
                )
            )

        for d in sorted(by_date.keys()):
            events.append(schemas.DashboardEventOut(
                date=d,
                count=len(by_date[d]),
                residents=by_date[d]
            ))

    elif type == "moveout":
        result = await db.execute(
            select(models.MoveOut, models.Resident, models.Bed)
            .join(models.Resident, models.MoveOut.resident_id == models.Resident.id)
            .join(models.Bed, models.Resident.bed_id == models.Bed.id, isouter=True)
            .where(
                models.MoveOut.status != "completed",
                models.MoveOut.requested_date >= start_date,
                models.MoveOut.requested_date < end_date
            )
            .order_by(models.MoveOut.requested_date)
        )
        rows = result.all()

        from collections import defaultdict
        by_date = defaultdict(list)
        for moveout, resident, bed in rows:
            by_date[moveout.requested_date].append(
                schemas.DashboardEventResident(
                    id=resident.id,
                    full_name=resident.full_name,
                    bed_code=bed.bed_code if bed else ""
                )
            )

        for d in sorted(by_date.keys()):
            events.append(schemas.DashboardEventOut(
                date=d,
                count=len(by_date[d]),
                residents=by_date[d]
            ))

    return events
