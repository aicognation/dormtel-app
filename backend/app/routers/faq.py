import uuid
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Faq
from app.schemas import FaqCreate, FaqOut

router = APIRouter()


@router.post("/", response_model=FaqOut, status_code=201)
async def create_faq(payload: FaqCreate, db: AsyncSession = Depends(get_db)):
    faq = Faq(
        question=payload.question,
        answer=payload.answer,
        category=payload.category or "general",
        order_index=payload.order_index or 0,
        is_active=True,
    )
    db.add(faq)
    await db.commit()
    await db.refresh(faq)
    return faq


@router.get("/", response_model=List[FaqOut])
async def list_faqs(
    category: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Faq).where(Faq.is_active == True)
    if category:
        stmt = stmt.where(Faq.category == category)
    if search:
        stmt = stmt.where(
            and_(
                Faq.question.ilike(f"%{search}%"),
                Faq.answer.ilike(f"%{search}%"),
            )
        )
    stmt = stmt.order_by(Faq.order_index.asc(), Faq.created_at.asc())
    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/categories", response_model=List[str])
async def list_faq_categories(db: AsyncSession = Depends(get_db)):
    stmt = select(Faq.category).distinct().where(Faq.is_active == True)
    result = await db.execute(stmt)
    return [r for r in result.scalars().all()]


@router.get("/{faq_id}", response_model=FaqOut)
async def get_faq(faq_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    stmt = select(Faq).where(Faq.id == faq_id)
    result = await db.execute(stmt)
    faq = result.scalar_one_or_none()
    if not faq:
        raise HTTPException(status_code=404, detail="FAQ not found")
    return faq


@router.put("/{faq_id}", response_model=FaqOut)
async def update_faq(faq_id: uuid.UUID, payload: FaqCreate, db: AsyncSession = Depends(get_db)):
    stmt = select(Faq).where(Faq.id == faq_id)
    result = await db.execute(stmt)
    faq = result.scalar_one_or_none()
    if not faq:
        raise HTTPException(status_code=404, detail="FAQ not found")
    faq.question = payload.question
    faq.answer = payload.answer
    faq.category = payload.category or faq.category
    faq.order_index = payload.order_index if payload.order_index is not None else faq.order_index
    await db.commit()
    await db.refresh(faq)
    return faq


@router.delete("/{faq_id}")
async def delete_faq(faq_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    stmt = select(Faq).where(Faq.id == faq_id)
    result = await db.execute(stmt)
    faq = result.scalar_one_or_none()
    if not faq:
        raise HTTPException(status_code=404, detail="FAQ not found")
    faq.is_active = False
    await db.commit()
    return {"detail": "FAQ deleted"}
