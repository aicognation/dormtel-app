import pytest
from datetime import date, timedelta
from decimal import Decimal
import uuid

from sqlalchemy import select
from app import models

pytestmark = pytest.mark.asyncio


async def test_create_moveout_request(async_client, db_session):
    resident = models.Resident(
        full_name="MoveOut Request Resident",
        email="moveout_request@example.com",
        phone="09180000001",
        monthly_rate=Decimal("3000.00"),
        status="active",
        move_in_date=date(2023, 1, 1),
    )
    db_session.add(resident)
    await db_session.commit()
    await db_session.refresh(resident)

    payload = {
        "resident_id": str(resident.id),
        "requested_date": "2024-06-15",
        "reason": "Graduation",
    }
    response = await async_client.post("/api/v1/moveouts/", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "requested"
    assert data["resident_id"] == str(resident.id)
    assert data["reason"] == "Graduation"


async def test_early_termination_creates_checkpoint(async_client, db_session):
    move_in = date.today() - timedelta(days=30)
    resident = models.Resident(
        full_name="Early Termination Resident",
        email="early_term@example.com",
        phone="09180000002",
        monthly_rate=Decimal("3000.00"),
        status="active",
        move_in_date=move_in,
    )
    db_session.add(resident)
    await db_session.commit()
    await db_session.refresh(resident)

    payload = {
        "resident_id": str(resident.id),
        "requested_date": date.today().isoformat(),
        "reason": "Personal emergency",
    }
    response = await async_client.post("/api/v1/moveouts/", json=payload)
    assert response.status_code == 200

    result = await db_session.execute(
        select(models.Checkpoint).where(models.Checkpoint.checkpoint_id == "CP-11")
    )
    checkpoint = result.scalar_one_or_none()
    assert checkpoint is not None
    assert checkpoint.status == "pending"
    assert checkpoint.stage == "move_out_review"


async def test_clearance_generates_final_billing_with_prorated_rent(async_client, db_session):
    move_out_date = date(2024, 6, 15)
    resident = models.Resident(
        full_name="Clearance Resident",
        email="clearance@example.com",
        phone="09180000003",
        monthly_rate=Decimal("3000.00"),
        status="active",
        move_in_date=date(2024, 1, 1),
    )
    db_session.add(resident)
    await db_session.commit()
    await db_session.refresh(resident)

    moveout = models.MoveOut(
        resident_id=resident.id,
        requested_date=move_out_date,
        actual_date=move_out_date,
        status="requested",
    )
    db_session.add(moveout)
    await db_session.commit()
    await db_session.refresh(moveout)

    response = await async_client.post(f"/api/v1/moveouts/{moveout.id}/clearance")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "clearance"

    await db_session.refresh(moveout)
    result = await db_session.execute(
        select(models.Billing).where(models.Billing.id == moveout.final_billing_id)
    )
    billing = result.scalar_one_or_none()
    assert billing is not None
    # June has 30 days; 15/30 * 3000 = 1500
    assert billing.rent_amount == Decimal("1500.00")
    assert billing.total_amount == Decimal("1500.00")
    assert billing.resident_id == resident.id


async def test_finalize_creates_refund_ledger_entry(async_client, db_session):
    resident = models.Resident(
        full_name="Refund Resident",
        email="refund@example.com",
        phone="09180000004",
        monthly_rate=Decimal("3000.00"),
        deposit_paid=Decimal("5000.00"),
        status="active",
        move_in_date=date(2024, 1, 1),
    )
    db_session.add(resident)
    await db_session.commit()
    await db_session.refresh(resident)

    moveout = models.MoveOut(
        resident_id=resident.id,
        requested_date=date(2024, 6, 15),
        actual_date=date(2024, 6, 15),
        status="clearance",
    )
    db_session.add(moveout)
    await db_session.commit()
    await db_session.refresh(moveout)

    billing = models.Billing(
        resident_id=resident.id,
        billing_period="Final - 2024-06",
        rent_amount=Decimal("1000.00"),
        total_amount=Decimal("1000.00"),
        status="draft",
    )
    db_session.add(billing)
    await db_session.commit()
    await db_session.refresh(billing)

    moveout.final_billing_id = billing.id
    await db_session.commit()

    response = await async_client.post(f"/api/v1/moveouts/{moveout.id}/finalize")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "refund_pending"

    await db_session.refresh(moveout)
    # refund = deposit - total = 5000 - 1000 = 4000
    assert moveout.refund_amount == Decimal("4000.00")

    result = await db_session.execute(
        select(models.LedgerEntry)
        .where(
            models.LedgerEntry.resident_id == resident.id,
            models.LedgerEntry.entry_type == "credit",
        )
    )
    ledger = result.scalar_one_or_none()
    assert ledger is not None
    assert ledger.amount == Decimal("4000.00")
    assert "refund" in ledger.description.lower()


async def test_complete_sets_resident_moved_out(async_client, db_session):
    resident = models.Resident(
        full_name="Complete Resident",
        email="complete@example.com",
        phone="09180000005",
        monthly_rate=Decimal("3000.00"),
        status="active",
        move_in_date=date(2024, 1, 1),
    )
    db_session.add(resident)
    await db_session.commit()
    await db_session.refresh(resident)

    moveout = models.MoveOut(
        resident_id=resident.id,
        requested_date=date(2024, 6, 15),
        status="refund_pending",
    )
    db_session.add(moveout)
    await db_session.commit()
    await db_session.refresh(moveout)

    response = await async_client.post(f"/api/v1/moveouts/{moveout.id}/complete")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "completed"

    await db_session.refresh(resident)
    assert resident.status == "moved_out"
