"""
Dormtel Seed Data Loader

Loads real operational data from extracted CSVs into the PostgreSQL database.
Run with: python -m app.seed_data

Prerequisites:
- Database tables created (alembic upgrade head || create_all)
- Extracted CSVs present at: ../../../New Artifacts/extracted/
"""

import asyncio
import csv
import os
import uuid
from datetime import datetime, date
from decimal import Decimal
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import sessionmaker

from app.database import engine, Base
from app.models import (
    Room, Bed, Resident, Inquiry, Billing, LedgerEntry, Staff, MeterReading
)

DATA_DIR = Path(__file__).resolve().parent.parent.parent.parent / "New Artifacts" / "extracted"


def parse_date(val):
    if not val or str(val).strip() == "" or str(val).lower() == "nan":
        return None
    try:
        # Handles "2024-03-01 00:00:00" or "2024-03-01"
        return datetime.strptime(str(val)[:10], "%Y-%m-%d").date()
    except Exception:
        return None


def parse_decimal(val):
    if not val or str(val).strip() == "" or str(val).lower() == "nan":
        return Decimal("0.00")
    try:
        return Decimal(str(val))
    except Exception:
        return Decimal("0.00")


def parse_phone(val):
    if not val or str(val).strip() == "" or str(val).lower() == "nan":
        return None
    s = str(val).replace(".0", "").replace(" ", "").replace("-", "")
    if s.startswith("9") and len(s) == 10:
        s = "0" + s
    if s.startswith("63"):
        s = "0" + s[2:]
    return s if len(s) >= 10 else None


def normalize_inquiry_source(src, channel):
    """Map raw source/channel strings to model enum."""
    combined = f"{str(src).lower()} {str(channel).lower()}"
    if "fb" in combined or "facebook" in combined:
        return "facebook"
    if "tiktok" in combined or "tiktok" in combined:
        return "tiktok"
    if "instagram" in combined or "ig" in combined:
        return "instagram"
    if "walk" in combined:
        return "walkin"
    if "phone" in combined or "call" in combined:
        return "phone"
    return "walkin"  # default


def generate_email(name, phone, idx=0):
    """Generate a deterministic placeholder email for prospects."""
    slug = "".join(c for c in str(name).lower() if c.isalnum() or c == " ").replace(" ", "_")[:30]
    suffix = f"_{idx}" if idx else ""
    return f"{slug}{suffix}@inquiry.dormtel"


async def seed_rooms_and_beds(session: AsyncSession):
    """Seed rooms and beds from DT01 and DT02 room specifications."""
    rooms = []
    beds = []
    seen_rooms = set()

    for prop in ["DT01", "DT02"]:
        csv_path = DATA_DIR / f"details_{prop}_ROOM_SPECIFICATION.csv"
        if not csv_path.exists():
            continue
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            current_room = None
            room_obj = None
            for row in reader:
                rn = str(row.get("ROOM NUMBER", "")).strip().replace(".0", "")
                bed_letter = str(row.get("BED LETTER", "")).strip()
                btype = str(row.get("BED TYPE", "")).strip().lower()

                if rn:
                    current_room = rn
                    room_key = f"{prop}-{current_room}"
                    if room_key not in seen_rooms:
                        seen_rooms.add(room_key)
                        room_obj = Room(
                            id=uuid.uuid4(),
                            room_number=current_room,
                            display_room_number=room_key,
                            property_code=prop,
                            building=prop,
                            capacity=4 if "bunk" in btype else 2,
                            status="available",
                        )
                        session.add(room_obj)
                        rooms.append(room_obj)
                        await session.flush()  # get room_obj.id
                if not current_room or not bed_letter:
                    continue

                # Find the room object for this row
                room_for_bed = next((r for r in rooms if r.room_number == current_room and r.property_code == prop), None)
                if not room_for_bed:
                    continue

                rate = Decimal("3200.00") if prop == "DT01" else Decimal("5700.00")
                bed_num = ord(bed_letter.upper()) - 64  # A->1, B->2, etc.

                beds.append(Bed(
                    id=uuid.uuid4(),
                    bed_code=f"{current_room}{bed_letter.upper()}",
                    room_id=room_for_bed.id,
                    bed_number=bed_num,
                    bed_type=btype if btype else None,
                    rate_per_bed=rate,
                    status="available",
                ))

    session.add_all(beds)
    await session.commit()
    print(f"Seeded {len(rooms)} rooms and {len(beds)} beds.")
    return rooms, beds


async def seed_staff(session: AsyncSession):
    """Seed default staff members."""
    staff_list = [
        Staff(id=uuid.uuid4(), full_name="Admin User", email="admin@dormtel.ph", role="admin", phone="09171234567"),
        Staff(id=uuid.uuid4(), full_name="Manager User", email="manager@dormtel.ph", role="manager", phone="09171234568"),
        Staff(id=uuid.uuid4(), full_name="DM User", email="dm@dormtel.ph", role="dm", phone="09171234569"),
    ]
    session.add_all(staff_list)
    await session.commit()
    print(f"Seeded {len(staff_list)} staff.")
    return staff_list


async def seed_residents_from_billing(session: AsyncSession, beds: list):
    """Seed active residents from April 2026 billing data."""
    csv_path = DATA_DIR / "billing_clean.csv"
    if not csv_path.exists():
        print("billing_clean.csv not found, skipping resident seed from billing.")
        return []

    # Build bed lookup by bed_code (e.g. "101A")
    bed_map = {b.bed_code: b for b in beds}

    residents = []
    seen_phones = set()
    dup_counter = {}

    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = str(row.get("name", "")).strip()
            if not name or name.upper() == "NAME":
                continue

            prop = row.get("property", "DT01")
            bed = str(row.get("bed", "")).strip().upper()
            room_num_raw = str(row.get("room", "")).strip().replace(".0", "")
            bed_code = f"{room_num_raw}{bed}" if room_num_raw and bed else None

            phone_raw = parse_phone(row.get("CELLPHONE", row.get("phone", "")))
            if not phone_raw:
                phone_raw = f"09990000000"
            # Handle duplicate phones
            if phone_raw in seen_phones:
                dup_counter[phone_raw] = dup_counter.get(phone_raw, 0) + 1
                phone_raw = phone_raw[:-2] + f"{dup_counter[phone_raw]:02d}"
            seen_phones.add(phone_raw)

            email = generate_email(name, phone_raw)
            move_in = parse_date(row.get("move_in"))
            move_out = parse_date(row.get("move_out"))
            rate = parse_decimal(row.get("rate"))

            bed_id = bed_map.get(bed_code).id if bed_code and bed_code in bed_map else None

            residents.append(Resident(
                id=uuid.uuid4(),
                full_name=name.title(),
                email=email,
                phone=phone_raw,
                status="active" if not move_out or move_out >= date.today() else "moved_out",
                bed_id=bed_id,
                move_in_date=move_in,
                move_out_date=move_out,
                monthly_rate=rate if rate > 0 else Decimal("3200.00"),
                deposit_paid=Decimal("0.00"),
            ))

    session.add_all(residents)
    await session.commit()
    print(f"Seeded {len(residents)} residents from billing.")
    return residents


async def seed_inquiries(session: AsyncSession):
    """Seed inquiries from cleaned inquiry CSV."""
    csv_path = DATA_DIR / "inquiries_clean.csv"
    if not csv_path.exists():
        print("inquiries_clean.csv not found, skipping inquiry seed.")
        return []

    inquiries = []
    seen_phones = {}
    staff_id = (await session.execute(select(Staff).limit(1))).scalar_one_or_none()
    staff_id = staff_id.id if staff_id else None

    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for idx, row in enumerate(reader):
            name = str(row.get("NAME", "")).strip()
            if not name:
                continue

            raw_date = parse_date(row.get("DATE"))
            raw_time = str(row.get("TIME", "")).strip()
            inquiry_dt = None
            if raw_date and raw_time and raw_time.lower() != "nan":
                try:
                    inquiry_dt = datetime.strptime(f"{raw_date} {raw_time[:8]}", "%Y-%m-%d %H:%M:%S")
                except Exception:
                    inquiry_dt = datetime.combine(raw_date, datetime.min.time())
            elif raw_date:
                inquiry_dt = datetime.combine(raw_date, datetime.min.time())

            phone = parse_phone(row.get("CELLPHONE", row.get("phone", "")))
            if not phone:
                phone = f"09990000{idx:03d}"

            # Create or reuse prospect resident
            if phone not in seen_phones:
                email = generate_email(name, phone, idx)
                resident = Resident(
                    id=uuid.uuid4(),
                    full_name=name.title(),
                    email=email,
                    phone=phone,
                    status="prospect",
                    monthly_rate=Decimal("0.00"),
                )
                session.add(resident)
                await session.flush()
                seen_phones[phone] = resident.id

            resident_id = seen_phones[phone]
            source = normalize_inquiry_source(row.get("SOURCE", ""), row.get("INQUIRY_FROM", ""))
            content = str(row.get("REMARKS", "")).strip() or f"Inquiry from {source}"

            inquiries.append(Inquiry(
                id=uuid.uuid4(),
                source=source,
                content=content[:500],
                status="new",
                assigned_to=staff_id,
                resident_id=resident_id,
                created_at=inquiry_dt or datetime.utcnow(),
            ))

    session.add_all(inquiries)
    await session.commit()
    print(f"Seeded {len(inquiries)} inquiries.")
    return inquiries


async def seed_billings_and_ledger(session: AsyncSession, residents: list):
    """Seed April 2026 billings and ledger entries from billing data."""
    csv_path = DATA_DIR / "billing_clean.csv"
    if not csv_path.exists():
        return

    # Build resident lookup by name
    resident_map = {}
    for r in residents:
        key = r.full_name.upper().strip()
        resident_map[key] = r

    billings = []
    ledger_entries = []

    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = str(row.get("name", "")).strip().upper()
            if not name or name == "NAME":
                continue

            resident = resident_map.get(name)
            if not resident:
                continue

            rent = parse_decimal(row.get("rate"))
            elec = parse_decimal(row.get("electricity_bill"))
            water = parse_decimal(row.get("water_bill"))
            misc = parse_decimal(row.get("electricity_subtotal"))  # fallback
            total = rent + elec + water + misc

            billing = Billing(
                id=uuid.uuid4(),
                resident_id=resident.id,
                billing_period="2026-04",
                rent_amount=rent,
                electric_charge=elec,
                water_charge=water,
                other_charges=misc,
                previous_balance=Decimal("0.00"),
                total_amount=total,
                status="draft",
            )
            billings.append(billing)

            # Create ledger entry for the billing (debit)
            ledger_entries.append(LedgerEntry(
                id=uuid.uuid4(),
                resident_id=resident.id,
                entry_type="debit",
                amount=total,
                description=f"April 2026 billing",
                reference_id=billing.id,
                running_balance=total,
            ))

    session.add_all(billings)
    await session.flush()
    session.add_all(ledger_entries)
    await session.commit()
    print(f"Seeded {len(billings)} billings and {len(ledger_entries)} ledger entries.")


async def seed_meter_readings(session: AsyncSession, staff_list: list):
    """Seed aggregate meter readings for April 2026."""
    csv_path = DATA_DIR / "billing_clean.csv"
    if not csv_path.exists():
        return

    # Aggregate total kWh by property
    prop_usage = {}
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            prop = row.get("property", "DT01")
            usage = parse_decimal(row.get("total_kwh_usage"))
            prop_usage[prop] = prop_usage.get(prop, Decimal("0.00")) + usage

    dm = next((s for s in staff_list if s.role == "dm"), staff_list[0] if staff_list else None)
    dm_id = dm.id if dm else None

    readings = []
    for prop, total_kwh in prop_usage.items():
        readings.append(MeterReading(
            id=uuid.uuid4(),
            building=prop,
            reading_date=date(2026, 4, 30),
            electric_reading=total_kwh,
            water_reading=Decimal("0.00"),
            submitted_by=dm_id,
            status="approved",
        ))

    session.add_all(readings)
    await session.commit()
    print(f"Seeded {len(readings)} meter readings.")


async def main():
    print("Dormtel Seed Data Loader")
    print("========================")

    # Create tables if needed
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)() as session:
        rooms, beds = await seed_rooms_and_beds(session)
        staff_list = await seed_staff(session)
        residents = await seed_residents_from_billing(session, beds)
        await seed_inquiries(session)
        await seed_billings_and_ledger(session, residents)
        await seed_meter_readings(session, staff_list)

    print("\nSeed complete.")


if __name__ == "__main__":
    asyncio.run(main())
