from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import date
from uuid import UUID
import uuid
from typing import Optional

from app.database import get_db
from app import models, schemas, auth

router = APIRouter()


@router.get("", response_model=list[schemas.MiscellaneousTransactionOut])
async def list_transactions(
    branch: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    from_date: Optional[date] = Query(None),
    to_date: Optional[date] = Query(None),
    current_staff: models.Staff = Depends(auth.require_staff),
    property_code: Optional[str] = Depends(auth.get_current_property),
    db: AsyncSession = Depends(get_db),
):
    query = select(models.MiscellaneousTransaction).order_by(models.MiscellaneousTransaction.created_at.desc())

    if branch:
        query = query.where(models.MiscellaneousTransaction.branch == branch)
    if category:
        query = query.where(models.MiscellaneousTransaction.category == category)
    if status:
        query = query.where(models.MiscellaneousTransaction.status == status)
    if from_date:
        query = query.where(models.MiscellaneousTransaction.transaction_date >= from_date)
    if to_date:
        query = query.where(models.MiscellaneousTransaction.transaction_date <= to_date)

    # Property filter via JWT — filter by branch column or include transactions with no room
    if property_code:
        query = query.where(
            (models.MiscellaneousTransaction.branch == property_code) |
            (models.MiscellaneousTransaction.room_id.is_(None))
        )

    # Branch admin filter
    if current_staff.role == "admin" and current_staff.managed_branch:
        query = query.where(models.MiscellaneousTransaction.branch == current_staff.managed_branch)

    result = await db.execute(query)
    return result.scalars().all()


@router.post("", response_model=schemas.MiscellaneousTransactionOut, status_code=status.HTTP_201_CREATED)
async def create_transaction(
    payload: schemas.MiscellaneousTransactionCreate,
    current_staff: models.Staff = Depends(auth.require_admin),
    db: AsyncSession = Depends(get_db),
):
    tx = models.MiscellaneousTransaction(
        id=uuid.uuid4(),
        resident_id=payload.resident_id,
        branch=payload.branch,
        room_id=payload.room_id,
        description=payload.description,
        amount=payload.amount,
        category=payload.category,
        transaction_date=payload.transaction_date,
        status=payload.status,
        recorded_by=current_staff.id,
    )
    db.add(tx)
    await db.commit()
    await db.refresh(tx)
    return tx


@router.patch("/{tx_id}", response_model=schemas.MiscellaneousTransactionOut)
async def update_transaction(
    tx_id: UUID,
    payload: schemas.MiscellaneousTransactionUpdate,
    current_staff: models.Staff = Depends(auth.require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(models.MiscellaneousTransaction).where(models.MiscellaneousTransaction.id == tx_id))
    tx = result.scalar_one_or_none()
    if not tx:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")

    if payload.resident_id is not None:
        tx.resident_id = payload.resident_id
    if payload.branch is not None:
        tx.branch = payload.branch
    if payload.room_id is not None:
        tx.room_id = payload.room_id
    if payload.description is not None:
        tx.description = payload.description
    if payload.amount is not None:
        tx.amount = payload.amount
    if payload.category is not None:
        tx.category = payload.category
    if payload.transaction_date is not None:
        tx.transaction_date = payload.transaction_date
    if payload.status is not None:
        tx.status = payload.status

    await db.commit()
    await db.refresh(tx)
    return tx


@router.delete("/{tx_id}")
async def delete_transaction(
    tx_id: UUID,
    current_staff: models.Staff = Depends(auth.require_manager),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(models.MiscellaneousTransaction).where(models.MiscellaneousTransaction.id == tx_id))
    tx = result.scalar_one_or_none()
    if not tx:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")

    await db.delete(tx)
    await db.commit()
    return {"message": "Transaction deleted"}
