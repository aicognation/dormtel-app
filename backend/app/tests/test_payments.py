import pytest
from datetime import datetime
from decimal import Decimal
from uuid import uuid4
from sqlalchemy import select

from app.models import Payment, Resident, LedgerEntry

pytestmark = pytest.mark.asyncio


async def test_webhook_creates_payment_and_auto_reconciles(async_client, db_session):
    resident = Resident(
        id=uuid4(),
        full_name="Webhook Resident",
        email="webhook@test.com",
        phone="09111111111",
        monthly_rate=Decimal("5000.00"),
        status="active",
    )
    db_session.add(resident)
    await db_session.commit()

    payload = {
        "reference_id": f"RES-{resident.id}-2024-01",
        "amount": "2500.00",
        "method": "gcash",
        "gateway_ref": "GCASH123",
        "signature": "mock_sig",
    }
    response = await async_client.post("/api/v1/payments/webhook", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "matched"
    assert str(data["resident_id"]) == str(resident.id)

    result = await db_session.execute(
        select(LedgerEntry).where(LedgerEntry.resident_id == resident.id)
    )
    entries = result.scalars().all()
    assert len(entries) == 1
    assert entries[0].entry_type == "credit"
    assert entries[0].amount == Decimal("2500.00")


async def test_unmatched_payment_appears_in_unmatched_queue(async_client, db_session):
    resident = Resident(
        id=uuid4(),
        full_name="Unmatched Resident",
        email="unmatched@test.com",
        phone="09222222222",
        monthly_rate=Decimal("5000.00"),
        status="active",
    )
    db_session.add(resident)
    await db_session.commit()

    payment = Payment(
        id=uuid4(),
        resident_id=resident.id,
        amount=Decimal("1000.00"),
        method="cash",
        status="unreconciled",
    )
    db_session.add(payment)
    await db_session.commit()

    response = await async_client.get("/api/v1/payments/unmatched")
    assert response.status_code == 200
    data = response.json()
    payment_ids = [p["id"] for p in data]
    assert str(payment.id) in payment_ids


async def test_manual_match_updates_payment_status_to_matched(async_client, db_session):
    resident = Resident(
        id=uuid4(),
        full_name="Match Resident",
        email="match@test.com",
        phone="09333333333",
        monthly_rate=Decimal("5000.00"),
        status="active",
    )
    db_session.add(resident)
    await db_session.commit()

    payment = Payment(
        id=uuid4(),
        resident_id=resident.id,
        amount=Decimal("2000.00"),
        method="bank_transfer",
        status="unreconciled",
    )
    db_session.add(payment)
    await db_session.commit()

    body = {"resident_id": str(resident.id), "billing_id": None}
    response = await async_client.post(
        f"/api/v1/payments/{payment.id}/match", json=body
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "matched"


async def test_dsr_includes_todays_payments(async_client, db_session):
    resident = Resident(
        id=uuid4(),
        full_name="DSR Resident",
        email="dsr@test.com",
        phone="09444444444",
        monthly_rate=Decimal("5000.00"),
        status="active",
    )
    db_session.add(resident)
    await db_session.commit()

    # Baseline before creating today's payment
    response = await async_client.get("/api/v1/payments/dsr")
    assert response.status_code == 200
    before = response.json()
    before_amount = Decimal(before["total_amount"])
    before_count = before["total_transactions"]

    payment = Payment(
        id=uuid4(),
        resident_id=resident.id,
        amount=Decimal("3000.00"),
        method="maya",
        status="matched",
        matched_at=datetime.utcnow(),
    )
    db_session.add(payment)
    await db_session.commit()

    response = await async_client.get("/api/v1/payments/dsr")
    assert response.status_code == 200
    after = response.json()
    after_amount = Decimal(after["total_amount"])
    after_count = after["total_transactions"]

    assert after_amount - before_amount == Decimal("3000.00")
    assert after_count - before_count == 1


async def test_manual_match_updates_resident_ledger(async_client, db_session):
    resident = Resident(
        id=uuid4(),
        full_name="Ledger Resident",
        email="ledger@test.com",
        phone="09555555555",
        monthly_rate=Decimal("5000.00"),
        status="active",
    )
    db_session.add(resident)
    await db_session.commit()

    # Seed an initial debit to give context to running balance
    initial = LedgerEntry(
        id=uuid4(),
        resident_id=resident.id,
        entry_type="debit",
        amount=Decimal("5000.00"),
        description="Rent due",
        running_balance=Decimal("-5000.00"),
    )
    db_session.add(initial)
    await db_session.commit()

    payment = Payment(
        id=uuid4(),
        resident_id=resident.id,
        amount=Decimal("5000.00"),
        method="gcash",
        status="unreconciled",
    )
    db_session.add(payment)
    await db_session.commit()

    body = {"resident_id": str(resident.id), "billing_id": None}
    response = await async_client.post(
        f"/api/v1/payments/{payment.id}/match", json=body
    )
    assert response.status_code == 200

    result = await db_session.execute(
        select(LedgerEntry)
        .where(LedgerEntry.resident_id == resident.id)
        .order_by(LedgerEntry.created_at.desc())
    )
    entries = result.scalars().all()
    assert len(entries) == 2
    latest = entries[0]
    assert latest.entry_type == "credit"
    assert latest.amount == Decimal("5000.00")
    assert latest.running_balance == Decimal("0.00")
