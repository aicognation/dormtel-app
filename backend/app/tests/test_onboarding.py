import pytest
from datetime import date
from decimal import Decimal
from app import models

pytestmark = pytest.mark.asyncio


async def test_create_reservation(async_client, db_session):
    payload = {
        "full_name": "Juan Dela Cruz",
        "email": "juan@example.com",
        "phone": "09171234567",
        "monthly_rate": "5000.00",
        "id_type": "passport",
        "id_number": "P1234567",
        "move_in_date": str(date.today()),
    }
    response = await async_client.post("/api/v1/onboarding/reservations", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "reserved"
    assert data["full_name"] == "Juan Dela Cruz"
    assert data["email"] == "juan@example.com"


async def test_reservation_room_capacity(async_client, db_session):
    room = models.Room(
        room_number="101",
        building="A",
        capacity=1,
        status="available",
    )
    db_session.add(room)
    await db_session.commit()
    await db_session.refresh(room)

    bed = models.Bed(
        bed_code="101A",
        room_id=room.id,
        bed_number=1,
        bed_type="loft_type",
        rate_per_bed=Decimal("5000.00"),
        status="available",
    )
    db_session.add(bed)
    await db_session.commit()
    await db_session.refresh(bed)

    payload = {
        "full_name": "First Resident",
        "email": "first@example.com",
        "phone": "09171111111",
        "monthly_rate": "5000.00",
        "bed_id": str(bed.id),
    }
    response = await async_client.post("/api/v1/onboarding/reservations", json=payload)
    assert response.status_code == 201

    payload2 = {
        "full_name": "Second Resident",
        "email": "second@example.com",
        "phone": "09172222222",
        "monthly_rate": "5000.00",
        "bed_id": str(bed.id),
    }
    response2 = await async_client.post("/api/v1/onboarding/reservations", json=payload2)
    assert response2.status_code == 409
    assert "not available" in response2.json()["detail"].lower()


async def test_movein_activation_requires_payment(async_client, db_session):
    room = models.Room(
        room_number="102",
        building="A",
        capacity=2,
        status="available",
    )
    db_session.add(room)
    await db_session.commit()
    await db_session.refresh(room)

    bed = models.Bed(
        bed_code="102A",
        room_id=room.id,
        bed_number=1,
        bed_type="lower_bunk",
        rate_per_bed=Decimal("5000.00"),
        status="reserved",
    )
    db_session.add(bed)
    await db_session.commit()
    await db_session.refresh(bed)

    resident = models.Resident(
        full_name="Unpaid Resident",
        email="unpaid@example.com",
        phone="09173333333",
        status="reserved",
        bed_id=bed.id,
        monthly_rate=Decimal("5000.00"),
        id_type="passport",
        id_number="P9999999",
    )
    db_session.add(resident)
    await db_session.commit()
    await db_session.refresh(resident)

    response = await async_client.post(f"/api/v1/onboarding/moveins/{resident.id}/activate")
    assert response.status_code == 400
    assert "payment" in response.json()["detail"].lower()


async def test_movein_activation_sets_active(async_client, db_session):
    room = models.Room(
        room_number="103",
        building="A",
        capacity=2,
        status="available",
    )
    db_session.add(room)
    await db_session.commit()
    await db_session.refresh(room)

    bed = models.Bed(
        bed_code="103A",
        room_id=room.id,
        bed_number=1,
        bed_type="lower_bunk",
        rate_per_bed=Decimal("5000.00"),
        status="reserved",
    )
    db_session.add(bed)
    await db_session.commit()
    await db_session.refresh(bed)

    resident = models.Resident(
        full_name="Paid Resident",
        email="paid@example.com",
        phone="09174444444",
        status="reserved",
        bed_id=bed.id,
        monthly_rate=Decimal("5000.00"),
        id_type="passport",
        id_number="P8888888",
    )
    db_session.add(resident)
    await db_session.commit()
    await db_session.refresh(resident)

    payment = models.Payment(
        resident_id=resident.id,
        amount=Decimal("5000.00"),
        method="gcash",
        status="verified",
    )
    db_session.add(payment)
    await db_session.commit()

    response = await async_client.post(f"/api/v1/onboarding/moveins/{resident.id}/activate")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "active"


async def test_list_available_rooms(async_client, db_session):
    room = models.Room(
        room_number="104",
        building="B",
        capacity=3,
        status="available",
    )
    db_session.add(room)
    await db_session.commit()
    await db_session.refresh(room)

    bed = models.Bed(
        bed_code="104A",
        room_id=room.id,
        bed_number=1,
        bed_type="loft_type",
        rate_per_bed=Decimal("4500.00"),
        status="available",
    )
    db_session.add(bed)
    await db_session.commit()
    await db_session.refresh(bed)

    response = await async_client.get("/api/v1/onboarding/rooms")
    assert response.status_code == 200
    data = response.json()
    room_ids = [r["id"] for r in data]
    assert str(room.id) in room_ids


async def test_payment_link_creates_billing(async_client, db_session):
    room = models.Room(
        room_number="105",
        building="B",
        capacity=3,
        status="available",
    )
    db_session.add(room)
    await db_session.commit()
    await db_session.refresh(room)

    bed = models.Bed(
        bed_code="105A",
        room_id=room.id,
        bed_number=1,
        bed_type="loft_type",
        rate_per_bed=Decimal("4500.00"),
        status="reserved",
    )
    db_session.add(bed)
    await db_session.commit()
    await db_session.refresh(bed)

    resident = models.Resident(
        full_name="Billing Resident",
        email="billing@example.com",
        phone="09175555555",
        status="reserved",
        bed_id=bed.id,
        monthly_rate=Decimal("4500.00"),
    )
    db_session.add(resident)
    await db_session.commit()
    await db_session.refresh(resident)

    response = await async_client.post(f"/api/v1/onboarding/reservations/{resident.id}/payment-link")
    assert response.status_code == 200
    data = response.json()
    assert data["resident_id"] == str(resident.id)
    assert data["payment_link"] is not None
    assert "pay.dormtel.ph" in data["payment_link"]
