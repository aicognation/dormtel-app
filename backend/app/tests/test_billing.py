import pytest
from decimal import Decimal
from datetime import date
from sqlalchemy import select

from app.models import MeterReading, Billing, Resident


@pytest.mark.asyncio
async def test_meter_reading_variance_over_20_percent_flags_review(async_client, db_session):
    baseline = {
        "building": "Bldg-A",
        "reading_date": "2024-01-01",
        "electric_reading": "100.00",
        "water_reading": "50.00",
    }
    response = await async_client.post("/api/v1/billings/meter-readings", json=baseline)
    assert response.status_code == 200
    assert response.json()["status"] == "approved"

    high_variance = {
        "building": "Bldg-A",
        "reading_date": "2024-02-01",
        "electric_reading": "175.00",
        "water_reading": "50.00",
    }
    response = await async_client.post("/api/v1/billings/meter-readings", json=high_variance)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "pending"
    assert Decimal(str(data["variance_pct"])) > 20


@pytest.mark.asyncio
async def test_billing_generation_computes_total_correctly(async_client, db_session):
    resident = Resident(
        full_name="Test Resident",
        email="test@example.com",
        phone="1234567890",
        status="active",
        monthly_rate=Decimal("5000.00"),
    )
    db_session.add(resident)
    await db_session.commit()

    payload = {
        "billing_period": "2024-02",
        "building": "Bldg-A",
        "total_electric_charge": "3000.00",
        "total_water_charge": "1500.00",
        "other_charges": "500.00",
    }
    response = await async_client.post("/api/v1/billings/generate", json=payload)
    assert response.status_code == 200

    result = await db_session.execute(select(Billing).where(Billing.resident_id == resident.id))
    billing = result.scalar_one()
    result_active = await db_session.execute(select(Resident).where(Resident.status == "active"))
    count = len(result_active.scalars().all())
    expected_total = (
        Decimal("5000.00")
        + Decimal("3000.00") / count
        + Decimal("1500.00") / count
        + Decimal("500.00") / count
    )
    assert billing.total_amount == expected_total


@pytest.mark.asyncio
async def test_billing_auto_approves_when_variance_under_15_percent(async_client, db_session):
    reading1 = MeterReading(
        building="Bldg-B",
        reading_date=date(2024, 1, 1),
        electric_reading=Decimal("100.00"),
        water_reading=Decimal("50.00"),
        variance_pct=Decimal("0"),
        status="approved",
    )
    reading2 = MeterReading(
        building="Bldg-B",
        reading_date=date(2024, 2, 1),
        electric_reading=Decimal("110.00"),
        water_reading=Decimal("50.00"),
        variance_pct=Decimal("10.00"),
        status="approved",
    )
    db_session.add_all([reading1, reading2])
    await db_session.commit()

    resident = Resident(
        full_name="Test Resident 2",
        email="test2@example.com",
        phone="1234567891",
        status="active",
        monthly_rate=Decimal("4000.00"),
    )
    db_session.add(resident)
    await db_session.commit()

    payload = {
        "billing_period": "2024-02",
        "building": "Bldg-B",
        "total_electric_charge": "1000.00",
        "total_water_charge": "500.00",
        "other_charges": "0.00",
    }
    response = await async_client.post("/api/v1/billings/generate", json=payload)
    assert response.status_code == 200

    result = await db_session.execute(select(Billing).where(Billing.resident_id == resident.id))
    billing = result.scalar_one()
    assert billing.status == "approved"


@pytest.mark.asyncio
async def test_billing_distribution_adds_payment_link(async_client, db_session):
    resident = Resident(
        full_name="Test Resident 3",
        email="test3@example.com",
        phone="1234567892",
        status="active",
        monthly_rate=Decimal("3000.00"),
    )
    db_session.add(resident)
    await db_session.commit()

    billing = Billing(
        resident_id=resident.id,
        billing_period="2024-03",
        rent_amount=Decimal("3000.00"),
        total_amount=Decimal("3000.00"),
        status="draft",
    )
    db_session.add(billing)
    await db_session.commit()
    await db_session.refresh(billing)

    response = await async_client.post(f"/api/v1/billings/{billing.id}/distribute")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "distributed"

    result = await db_session.execute(select(Billing).where(Billing.id == billing.id))
    updated = result.scalar_one()
    assert updated.payment_link is not None
    assert str(billing.id) in updated.payment_link


@pytest.mark.asyncio
async def test_missing_meter_reading_uses_estimate(async_client, db_session):
    resident = Resident(
        full_name="Test Resident 4",
        email="test4@example.com",
        phone="1234567893",
        status="active",
        monthly_rate=Decimal("4500.00"),
    )
    db_session.add(resident)
    await db_session.commit()

    payload = {
        "billing_period": "2024-04",
        "building": "Bldg-C",
        "total_electric_charge": "2000.00",
        "total_water_charge": "1000.00",
        "other_charges": "0.00",
    }
    response = await async_client.post("/api/v1/billings/generate", json=payload)
    assert response.status_code == 200

    result = await db_session.execute(
        select(MeterReading).where(MeterReading.building == "Bldg-C")
    )
    readings = result.scalars().all()
    estimated = [r for r in readings if r.status == "estimated"]
    assert len(estimated) >= 1

    result2 = await db_session.execute(select(Billing).where(Billing.resident_id == resident.id))
    billing = result2.scalar_one_or_none()
    assert billing is not None
