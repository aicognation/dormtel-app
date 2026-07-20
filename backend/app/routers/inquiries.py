import uuid
from datetime import datetime, timedelta
from typing import Optional, List
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app import models, auth
from app.models import Inquiry, Checkpoint, QrCampaign
from app.schemas import InquiryCreate, InquiryOut, InquiryAdminResponse

router = APIRouter()

POSITIVE_KEYWORDS = [
    "interested", "love", "great", "amazing", "perfect",
    "good", "happy", "excited", "yes", "please"
]
NEGATIVE_KEYWORDS = [
    "angry", "mad", "frustrated", "terrible", "awful",
    "hate", "bad", "worst", "disappointed", "upset"
]

# Must match the inquiry_source PostgreSQL enum (lowercase)
ALLOWED_SOURCES = {
    "facebook", "instagram", "tiktok", "walkin",
    "phone", "referral", "website", "email",
}


def _clean_optional(value: Optional[str]) -> Optional[str]:
    """Trim whitespace and store NULL instead of empty strings."""
    if value is None:
        return None
    value = value.strip()
    return value or None


def _calculate_sentiment(content: Optional[str]) -> float:
    if not content:
        return 0.5
    text = content.lower()
    pos_count = sum(1 for kw in POSITIVE_KEYWORDS if kw in text)
    neg_count = sum(1 for kw in NEGATIVE_KEYWORDS if kw in text)

    if pos_count > 0 and neg_count == 0:
        return min(1.0, 0.85 + pos_count * 0.03)
    if neg_count > 0 and pos_count == 0:
        return max(0.0, 0.3 - neg_count * 0.05)
    if pos_count > 0 and neg_count > 0:
        return 0.5
    return 0.5


def _calculate_lead_score(content: Optional[str], source: str) -> int:
    score = 50
    if content:
        text = content.lower()
        pos_count = sum(1 for kw in POSITIVE_KEYWORDS if kw in text)
        score += pos_count * 10
    if source in ("walkin", "phone"):
        score += 20
    return min(100, score)


@router.post("/", response_model=InquiryOut, status_code=201)
async def create_inquiry(
    payload: InquiryCreate,
    property_code: Optional[str] = Depends(auth.get_current_property),
    db: AsyncSession = Depends(get_db),
):
    # DB enum is lowercase — normalize casing so stale/legacy clients don't 500
    source = (payload.source or "").strip().lower()
    if source not in ALLOWED_SOURCES:
        raise HTTPException(
            status_code=422,
            detail=(
                f"Invalid inquiry source '{payload.source}'. "
                f"Allowed values: {', '.join(sorted(ALLOWED_SOURCES))}"
            ),
        )

    sentiment = _calculate_sentiment(payload.content)
    lead = _calculate_lead_score(payload.content, source)

    # Attribute the lead to the QR campaign encoded in the scanned code (if any)
    campaign_id = None
    campaign_title = None
    if payload.campaign_id:
        camp_result = await db.execute(
            select(QrCampaign).where(QrCampaign.id == payload.campaign_id)
        )
        campaign = camp_result.scalar_one_or_none()
        if not campaign:
            raise HTTPException(
                status_code=422,
                detail=f"Campaign '{payload.campaign_id}' not found",
            )
        campaign_id = campaign.id
        campaign_title = campaign.title

    inquiry = Inquiry(
        source=source,
        external_id=_clean_optional(payload.external_id),
        content=payload.content,
        # QR kiosk sends it explicitly; portal relies on the JWT property
        property_code=payload.property_code or property_code or "DT01",
        campaign_id=campaign_id,
        campaign_title=campaign_title,
        prospect_name=payload.prospect_name,
        prospect_phone=_clean_optional(payload.prospect_phone),
        prospect_email=_clean_optional(payload.prospect_email),
        school=payload.school,
        course=payload.course,
        review_center=payload.review_center,
        exam_date=payload.exam_date,
        first_time_dormer=payload.first_time_dormer,
        previous_dorm=payload.previous_dorm,
        desired_move_in_date=payload.desired_move_in_date,
        length_of_stay=payload.length_of_stay,
        inquiry_form_data=payload.inquiry_form_data,
        sentiment_score=Decimal(str(round(sentiment, 2))),
        lead_score=lead,
        status="new",
    )
    db.add(inquiry)
    await db.commit()
    await db.refresh(inquiry)
    return inquiry


@router.get("/", response_model=List[InquiryOut])
async def list_inquiries(
    status: Optional[str] = Query(None),
    source: Optional[str] = Query(None),
    campaign_id: Optional[uuid.UUID] = Query(None),
    via_qr: bool = Query(False),
    db: AsyncSession = Depends(get_db),
    current_staff: models.Staff = Depends(auth.require_staff),
    property_code: Optional[str] = Depends(auth.get_current_property),
):
    stmt = select(Inquiry)
    filters = []
    if status:
        filters.append(Inquiry.status == status)
    if source:
        filters.append(Inquiry.source == source)
    if campaign_id:
        filters.append(Inquiry.campaign_id == campaign_id)
    if via_qr:
        filters.append(
            or_(
                Inquiry.campaign_id.is_not(None),
                Inquiry.inquiry_form_data["submitted_via"].as_string() == "public_qr_form",
            )
        )
    if property_code:
        filters.append(Inquiry.property_code == property_code)
    if filters:
        stmt = stmt.where(and_(*filters))
    stmt = stmt.order_by(Inquiry.created_at.desc())
    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/tenant", response_model=List[InquiryOut])
async def list_tenant_inquiries(
    db: AsyncSession = Depends(get_db),
    current_staff: models.Staff = Depends(auth.require_staff),
    property_code: Optional[str] = Depends(auth.get_current_property),
):
    stmt = (
        select(Inquiry)
        .where(Inquiry.resident_id.is_not(None))
        .order_by(Inquiry.created_at.desc())
    )
    if property_code:
        stmt = stmt.where(Inquiry.property_code == property_code)
    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/convertible", response_model=List[InquiryOut])
async def list_convertible_inquiries(
    db: AsyncSession = Depends(get_db),
    current_staff: models.Staff = Depends(auth.require_staff),
    property_code: Optional[str] = Depends(auth.get_current_property),
):
    stmt = (
        select(Inquiry)
        .where(Inquiry.status.in_(["new", "responded", "escalated"]))
        .order_by(Inquiry.created_at.desc())
    )
    if property_code:
        stmt = stmt.where(Inquiry.property_code == property_code)
    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/{inquiry_id}", response_model=InquiryOut)
async def get_inquiry(
    inquiry_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_staff: models.Staff = Depends(auth.require_staff),
):
    stmt = select(Inquiry).where(Inquiry.id == inquiry_id)
    result = await db.execute(stmt)
    inquiry = result.scalar_one_or_none()
    if not inquiry:
        raise HTTPException(status_code=404, detail="Inquiry not found")
    return inquiry


@router.post("/{inquiry_id}/respond", response_model=dict)
async def respond_to_inquiry(
    inquiry_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_staff: models.Staff = Depends(auth.require_staff),
):
    stmt = select(Inquiry).where(Inquiry.id == inquiry_id)
    result = await db.execute(stmt)
    inquiry = result.scalar_one_or_none()
    if not inquiry:
        raise HTTPException(status_code=404, detail="Inquiry not found")

    inquiry.status = "responded"
    await db.commit()

    if inquiry.sentiment_score is not None and float(inquiry.sentiment_score) >= 0.85:
        auto_text = (
            "Thank you for your interest! We'd love to help you find the perfect space. "
            "Reply to schedule a tour."
        )
    else:
        auto_text = (
            "Thanks for reaching out. A team member will follow up with you shortly."
        )

    return {"status": "responded", "auto_response": auto_text}


@router.patch("/{inquiry_id}/respond", response_model=InquiryOut)
async def respond_to_inquiry_manual(
    inquiry_id: uuid.UUID,
    payload: InquiryAdminResponse,
    db: AsyncSession = Depends(get_db),
    current_staff: models.Staff = Depends(auth.require_staff),
):
    stmt = select(Inquiry).where(Inquiry.id == inquiry_id)
    result = await db.execute(stmt)
    inquiry = result.scalar_one_or_none()
    if not inquiry:
        raise HTTPException(status_code=404, detail="Inquiry not found")

    inquiry.response = payload.response
    inquiry.status = "responded"
    await db.commit()
    await db.refresh(inquiry)
    return inquiry


@router.post("/{inquiry_id}/escalate", response_model=dict)
async def escalate_inquiry(
    inquiry_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_staff: models.Staff = Depends(auth.require_staff),
):
    stmt = select(Inquiry).where(Inquiry.id == inquiry_id)
    result = await db.execute(stmt)
    inquiry = result.scalar_one_or_none()
    if not inquiry:
        raise HTTPException(status_code=404, detail="Inquiry not found")

    content_lower = (inquiry.content or "").lower()
    has_discount = any(kw in content_lower for kw in ("discount", "negotiate"))
    has_angry = any(kw in content_lower for kw in NEGATIVE_KEYWORDS)
    sentiment_low = inquiry.sentiment_score is not None and float(inquiry.sentiment_score) < 0.3

    if has_discount:
        checkpoint_id = f"CP-01-{inquiry_id}"
        stage = "Admin Review"
        reason = "discount/negotiate request"
    elif has_angry or sentiment_low:
        checkpoint_id = f"CP-02-{inquiry_id}"
        stage = "Manager Review"
        reason = "angry sentiment"
    else:
        checkpoint_id = f"CP-01-{inquiry_id}"
        stage = "Admin Review"
        reason = "general escalation"

    existing_stmt = select(Checkpoint).where(Checkpoint.checkpoint_id == checkpoint_id)
    existing_result = await db.execute(existing_stmt)
    if existing_result.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Checkpoint already exists for this inquiry")

    checkpoint = Checkpoint(
        checkpoint_id=checkpoint_id,
        stage=stage,
        sla_deadline=datetime.utcnow() + timedelta(hours=24),
        status="pending",
        context_package={"inquiry_id": str(inquiry_id), "reason": reason},
    )
    db.add(checkpoint)
    inquiry.status = "escalated"
    await db.commit()

    return {
        "status": "escalated",
        "checkpoint_id": checkpoint_id,
        "stage": stage,
    }
