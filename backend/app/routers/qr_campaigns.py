import uuid
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app import models, auth
from app.models import QrCampaign, Inquiry
from app.schemas import QrCampaignCreate, QrCampaignOut, QrCampaignPublic, InquiryOut

router = APIRouter()


@router.post("/", response_model=QrCampaignOut, status_code=201)
async def create_campaign(
    payload: QrCampaignCreate,
    current_staff: models.Staff = Depends(auth.get_current_staff),
    property_code: Optional[str] = Depends(auth.get_current_property),
    db: AsyncSession = Depends(get_db),
):
    if payload.start_date and payload.end_date and payload.start_date > payload.end_date:
        raise HTTPException(status_code=422, detail="Campaign start date must be on or before the end date")

    campaign = QrCampaign(
        title=payload.title.strip(),
        property_code=payload.property_code or property_code or "DT01",
        start_date=payload.start_date,
        end_date=payload.end_date,
        notes=payload.notes.strip() if payload.notes else None,
        created_by=current_staff.id,
    )
    db.add(campaign)
    await db.commit()
    await db.refresh(campaign)

    return QrCampaignOut(
        **_campaign_fields(campaign),
        created_by_name=current_staff.full_name,
        leads_count=0,
        new_count=0,
        converted_count=0,
        last_lead_at=None,
    )


def _campaign_fields(campaign: QrCampaign) -> dict:
    return {
        "id": campaign.id,
        "title": campaign.title,
        "property_code": campaign.property_code,
        "start_date": campaign.start_date,
        "end_date": campaign.end_date,
        "notes": campaign.notes,
        "created_by": campaign.created_by,
        "created_at": campaign.created_at,
    }


@router.get("/", response_model=List[QrCampaignOut])
async def list_campaigns(
    property_code: Optional[str] = Depends(auth.get_current_property),
    current_staff: models.Staff = Depends(auth.require_staff),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(QrCampaign)
    if property_code:
        stmt = stmt.where(QrCampaign.property_code == property_code)
    stmt = stmt.order_by(QrCampaign.created_at.desc())
    result = await db.execute(stmt)
    campaigns = result.scalars().all()
    if not campaigns:
        return []

    campaign_ids = [c.id for c in campaigns]

    # Per-campaign lead statistics in a single aggregate query
    stats_stmt = (
        select(
            Inquiry.campaign_id,
            func.count(Inquiry.id),
            func.count(Inquiry.id).filter(Inquiry.status == "new"),
            func.count(Inquiry.id).filter(Inquiry.status == "converted"),
            func.max(Inquiry.created_at),
        )
        .where(Inquiry.campaign_id.in_(campaign_ids))
        .group_by(Inquiry.campaign_id)
    )
    stats_result = await db.execute(stats_stmt)
    stats = {row[0]: row[1:] for row in stats_result.all()}

    # Creator names
    creator_ids = [c.created_by for c in campaigns if c.created_by]
    names = {}
    if creator_ids:
        staff_result = await db.execute(select(models.Staff).where(models.Staff.id.in_(creator_ids)))
        names = {s.id: s.full_name for s in staff_result.scalars().all()}

    out = []
    for c in campaigns:
        s = stats.get(c.id)
        out.append(
            QrCampaignOut(
                **_campaign_fields(c),
                created_by_name=names.get(c.created_by),
                leads_count=s[0] if s else 0,
                new_count=s[1] if s else 0,
                converted_count=s[2] if s else 0,
                last_lead_at=s[3] if s else None,
            )
        )
    return out


@router.get("/public/{campaign_id}", response_model=QrCampaignPublic)
async def get_public_campaign(
    campaign_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Unauthenticated lookup used by the public QR inquiry form.

    Schema is resolved from the X-Tenant-Schema header (embedded in the QR URL),
    so a pilot QR code resolves its campaign from the pilot schema.
    """
    result = await db.execute(select(QrCampaign).where(QrCampaign.id == campaign_id))
    campaign = result.scalar_one_or_none()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return campaign


@router.get("/{campaign_id}/leads", response_model=List[InquiryOut])
async def list_campaign_leads(
    campaign_id: uuid.UUID,
    current_staff: models.Staff = Depends(auth.require_staff),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(QrCampaign).where(QrCampaign.id == campaign_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Campaign not found")

    stmt = (
        select(Inquiry)
        .where(Inquiry.campaign_id == campaign_id)
        .order_by(Inquiry.created_at.desc())
    )
    result = await db.execute(stmt)
    return result.scalars().all()
