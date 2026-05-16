import uuid
from datetime import datetime, timedelta
from typing import Optional, List
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Inquiry, Checkpoint
from app.schemas import InquiryCreate, InquiryOut

router = APIRouter()

POSITIVE_KEYWORDS = [
    "interested", "love", "great", "amazing", "perfect",
    "good", "happy", "excited", "yes", "please"
]
NEGATIVE_KEYWORDS = [
    "angry", "mad", "frustrated", "terrible", "awful",
    "hate", "bad", "worst", "disappointed", "upset"
]


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
async def create_inquiry(payload: InquiryCreate, db: AsyncSession = Depends(get_db)):
    sentiment = _calculate_sentiment(payload.content)
    lead = _calculate_lead_score(payload.content, payload.source)
    inquiry = Inquiry(
        source=payload.source,
        external_id=payload.external_id,
        content=payload.content,
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
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Inquiry)
    filters = []
    if status:
        filters.append(Inquiry.status == status)
    if source:
        filters.append(Inquiry.source == source)
    if filters:
        stmt = stmt.where(and_(*filters))
    stmt = stmt.order_by(Inquiry.created_at.desc())
    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/{inquiry_id}", response_model=InquiryOut)
async def get_inquiry(inquiry_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    stmt = select(Inquiry).where(Inquiry.id == inquiry_id)
    result = await db.execute(stmt)
    inquiry = result.scalar_one_or_none()
    if not inquiry:
        raise HTTPException(status_code=404, detail="Inquiry not found")
    return inquiry


@router.post("/{inquiry_id}/respond", response_model=dict)
async def respond_to_inquiry(inquiry_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
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


@router.post("/{inquiry_id}/escalate", response_model=dict)
async def escalate_inquiry(inquiry_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
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
