import uuid
from datetime import datetime
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app import models, auth
from app.database import get_db
from app.models import ServiceRequest, Resident
from app.schemas import ServiceRequestOut, ServiceRequestWithResidentOut, ServiceRequestAdminCreate

router = APIRouter()

VALID_STATUSES = {"submitted", "acknowledged", "in_progress", "resolved", "closed"}


class StatusUpdatePayload(BaseModel):
    status: str
    resolution_notes: Optional[str] = None


class AssignPayload(BaseModel):
    assigned_to: uuid.UUID


@router.get("/", response_model=List[ServiceRequestWithResidentOut])
async def list_service_requests(
    status: Optional[str] = Query(None),
    resident_id: Optional[uuid.UUID] = Query(None),
    category: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_staff: models.Staff = Depends(auth.require_staff),
    property_code: Optional[str] = Depends(auth.get_current_property),
):
    stmt = (
        select(ServiceRequest, Resident.full_name.label("resident_name"))
        .join(Resident, ServiceRequest.resident_id == Resident.id, isouter=True)
    )
    filters = []
    if status:
        filters.append(ServiceRequest.status == status)
    if resident_id:
        filters.append(ServiceRequest.resident_id == resident_id)
    if category:
        filters.append(ServiceRequest.category == category)
    if priority:
        filters.append(ServiceRequest.priority == priority)
    if filters:
        stmt = stmt.where(and_(*filters))
    if property_code:
        stmt = (stmt
            .join(models.Bed, Resident.bed_id == models.Bed.id, isouter=True)
            .join(models.Room, models.Bed.room_id == models.Room.id, isouter=True)
            .where(models.Room.property_code == property_code)
        )
    stmt = stmt.order_by(ServiceRequest.submitted_at.desc())
    result = await db.execute(stmt)
    rows = result.all()

    out = []
    for sr, resident_name in rows:
        base = ServiceRequestWithResidentOut.model_validate(sr)
        out.append(base.model_copy(update={"resident_name": resident_name}))
    return out


@router.post("/", response_model=ServiceRequestWithResidentOut, status_code=201)
async def create_service_request(
    payload: ServiceRequestAdminCreate,
    db: AsyncSession = Depends(get_db),
    current_staff: models.Staff = Depends(auth.require_staff),
):
    resident_result = await db.execute(select(Resident).where(Resident.id == payload.resident_id))
    resident = resident_result.scalar_one_or_none()
    if not resident:
        raise HTTPException(status_code=404, detail="Resident not found")

    sr = ServiceRequest(
        id=uuid.uuid4(),
        resident_id=payload.resident_id,
        category=payload.category,
        subject=payload.subject,
        description=payload.description,
        location=payload.location,
        priority=payload.priority,
        status="submitted",
        submitted_at=datetime.utcnow(),
        created_at=datetime.utcnow(),
    )
    db.add(sr)
    await db.commit()
    await db.refresh(sr)

    base = ServiceRequestWithResidentOut.model_validate(sr)
    return base.model_copy(update={"resident_name": resident.full_name})


@router.get("/{sr_id}", response_model=ServiceRequestWithResidentOut)
async def get_service_request(
    sr_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_staff: models.Staff = Depends(auth.require_staff),
):
    stmt = (
        select(ServiceRequest, Resident.full_name.label("resident_name"))
        .join(Resident, ServiceRequest.resident_id == Resident.id, isouter=True)
        .where(ServiceRequest.id == sr_id)
    )
    result = await db.execute(stmt)
    row = result.one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="Service request not found")
    sr, resident_name = row
    base = ServiceRequestWithResidentOut.model_validate(sr)
    return base.model_copy(update={"resident_name": resident_name})


@router.patch("/{sr_id}/status", response_model=ServiceRequestOut)
async def update_service_request_status(
    sr_id: uuid.UUID,
    payload: StatusUpdatePayload,
    db: AsyncSession = Depends(get_db),
    current_staff: models.Staff = Depends(auth.require_staff),
):
    if payload.status not in VALID_STATUSES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status. Must be one of: {', '.join(VALID_STATUSES)}",
        )

    stmt = select(ServiceRequest).where(ServiceRequest.id == sr_id)
    result = await db.execute(stmt)
    sr = result.scalar_one_or_none()
    if not sr:
        raise HTTPException(status_code=404, detail="Service request not found")

    sr.status = payload.status
    if payload.resolution_notes is not None:
        sr.resolution_notes = payload.resolution_notes
    if payload.status == "resolved" and not sr.resolved_at:
        sr.resolved_at = datetime.utcnow()

    await db.commit()
    await db.refresh(sr)
    return sr


@router.post("/{sr_id}/assign", response_model=ServiceRequestOut)
async def assign_service_request(
    sr_id: uuid.UUID,
    payload: AssignPayload,
    db: AsyncSession = Depends(get_db),
    current_staff: models.Staff = Depends(auth.require_staff),
):
    stmt = select(ServiceRequest).where(ServiceRequest.id == sr_id)
    result = await db.execute(stmt)
    sr = result.scalar_one_or_none()
    if not sr:
        raise HTTPException(status_code=404, detail="Service request not found")

    sr.assigned_to = payload.assigned_to
    await db.commit()
    await db.refresh(sr)
    return sr
