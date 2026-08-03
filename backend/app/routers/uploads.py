"""FIX-019 WP-8: Upload Monitor Dashboard endpoints."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from typing import Optional
from uuid import UUID
from datetime import datetime

from app.database import get_db
from app import auth, models

router = APIRouter(prefix="/uploads", tags=["uploads"])


@router.get("/")
async def list_uploads(
    property_code: Optional[str] = Query(None),
    status: Optional[str] = Query(None),  # accepted/rejected/partial
    template_type: Optional[str] = Query(None),
    uploaded_by: Optional[str] = Query(None),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_staff: models.Staff = Depends(auth.require_staff),
    selected_property: Optional[str] = Depends(auth.get_current_property),
    db: AsyncSession = Depends(get_db),
):
    """List all upload attempts with filtering and pagination."""
    pc = property_code or selected_property
    query = select(models.MeterReadingUploadLog)
    count_query = select(func.count(models.MeterReadingUploadLog.id))

    if pc:
        query = query.where(models.MeterReadingUploadLog.property_code == pc)
        count_query = count_query.where(models.MeterReadingUploadLog.property_code == pc)
    if status:
        query = query.where(models.MeterReadingUploadLog.result == status)
        count_query = count_query.where(models.MeterReadingUploadLog.result == status)
    if template_type:
        query = query.where(models.MeterReadingUploadLog.template_type == template_type)
        count_query = count_query.where(models.MeterReadingUploadLog.template_type == template_type)
    if date_from:
        try:
            df = datetime.strptime(date_from, "%Y-%m-%d")
            query = query.where(models.MeterReadingUploadLog.uploaded_at >= df)
            count_query = count_query.where(models.MeterReadingUploadLog.uploaded_at >= df)
        except ValueError:
            pass
    if date_to:
        try:
            dt = datetime.strptime(date_to, "%Y-%m-%d")
            query = query.where(models.MeterReadingUploadLog.uploaded_at <= dt)
            count_query = count_query.where(models.MeterReadingUploadLog.uploaded_at <= dt)
        except ValueError:
            pass

    # Get total count
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Apply pagination
    offset = (page - 1) * page_size
    query = query.order_by(desc(models.MeterReadingUploadLog.uploaded_at)).offset(offset).limit(page_size)

    result = await db.execute(query)
    logs = result.scalars().all()

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "uploads": [
            {
                "id": str(log.id),
                "property_code": log.property_code,
                "uploaded_by": str(log.uploaded_by) if log.uploaded_by else None,
                "uploaded_at": log.uploaded_at.isoformat() if log.uploaded_at else None,
                "source_filename": log.source_filename,
                "template_id": str(log.template_id) if log.template_id else None,
                "template_type": log.template_type,
                "period_start": log.period_start.isoformat() if log.period_start else None,
                "period_end": log.period_end.isoformat() if log.period_end else None,
                "upload_kind": log.upload_kind,
                "rows_presented": log.rows_presented,
                "residents_matched": log.residents_matched,
                "readings_imported": log.readings_imported,
                "skipped": log.skipped,
                "allow_missing": log.allow_missing,
                "result": log.result,
                "issues": log.issues,
                "archive_upload_id": str(log.archive_upload_id) if log.archive_upload_id else None,
            }
            for log in logs
        ],
    }


@router.get("/stats")
async def upload_stats(
    property_code: Optional[str] = Query(None),
    current_staff: models.Staff = Depends(auth.require_staff),
    selected_property: Optional[str] = Depends(auth.get_current_property),
    db: AsyncSession = Depends(get_db),
):
    """Summary statistics for the upload monitor dashboard."""
    pc = property_code or selected_property

    base_query = select(models.MeterReadingUploadLog)
    if pc:
        base_query = base_query.where(models.MeterReadingUploadLog.property_code == pc)

    # Total uploads
    total_result = await db.execute(select(func.count(models.MeterReadingUploadLog.id)).where(
        models.MeterReadingUploadLog.property_code == pc if pc else True
    ))
    total_uploads = total_result.scalar() or 0

    # Accepted count
    accepted_result = await db.execute(select(func.count(models.MeterReadingUploadLog.id)).where(
        models.MeterReadingUploadLog.property_code == pc if pc else True,
        models.MeterReadingUploadLog.result == "accepted"
    ))
    accepted = accepted_result.scalar() or 0

    # Rejected count
    rejected_result = await db.execute(select(func.count(models.MeterReadingUploadLog.id)).where(
        models.MeterReadingUploadLog.property_code == pc if pc else True,
        models.MeterReadingUploadLog.result == "rejected"
    ))
    rejected = rejected_result.scalar() or 0

    # Total readings imported
    readings_result = await db.execute(select(func.coalesce(func.sum(models.MeterReadingUploadLog.readings_imported), 0)).where(
        models.MeterReadingUploadLog.property_code == pc if pc else True
    ))
    total_readings = readings_result.scalar() or 0

    # Total residents matched
    residents_result = await db.execute(select(func.coalesce(func.sum(models.MeterReadingUploadLog.residents_matched), 0)).where(
        models.MeterReadingUploadLog.property_code == pc if pc else True
    ))
    total_residents = residents_result.scalar() or 0

    rejection_rate = (rejected / total_uploads * 100) if total_uploads > 0 else 0

    return {
        "total_uploads": total_uploads,
        "accepted": accepted,
        "rejected": rejected,
        "partial": total_uploads - accepted - rejected,
        "total_readings_imported": total_readings,
        "total_residents_matched": total_residents,
        "rejection_rate_pct": round(rejection_rate, 1),
    }


@router.get("/{upload_id}")
async def get_upload_detail(
    upload_id: str,
    current_staff: models.Staff = Depends(auth.require_staff),
    db: AsyncSession = Depends(get_db),
):
    """Get full detail for a single upload."""
    try:
        uid = UUID(upload_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid upload ID")

    result = await db.execute(
        select(models.MeterReadingUploadLog).where(models.MeterReadingUploadLog.id == uid)
    )
    log = result.scalar_one_or_none()
    if not log:
        raise HTTPException(status_code=404, detail="Upload not found")

    return {
        "id": str(log.id),
        "property_code": log.property_code,
        "uploaded_by": str(log.uploaded_by) if log.uploaded_by else None,
        "uploaded_at": log.uploaded_at.isoformat() if log.uploaded_at else None,
        "source_filename": log.source_filename,
        "template_id": str(log.template_id) if log.template_id else None,
        "template_type": log.template_type,
        "period_start": log.period_start.isoformat() if log.period_start else None,
        "period_end": log.period_end.isoformat() if log.period_end else None,
        "upload_kind": log.upload_kind,
        "rows_presented": log.rows_presented,
        "residents_matched": log.residents_matched,
        "readings_imported": log.readings_imported,
        "skipped": log.skipped,
        "allow_missing": log.allow_missing,
        "result": log.result,
        "issues": log.issues,
        "archive_upload_id": str(log.archive_upload_id) if log.archive_upload_id else None,
    }
