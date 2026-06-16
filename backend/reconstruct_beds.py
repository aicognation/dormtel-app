"""
Data reconstruction script for SPEC v1.2 bed migration.
Creates beds for all rooms and assigns existing residents to beds
based on their monthly_rate matching the room's old rate_per_bed.
"""
import asyncio
import uuid
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, text
from app import models
from app.database import DATABASE_URL

# Bed type assignment based on capacity and bed number
BED_TYPE_MAP = {
    2: {1: "lower_bunk", 2: "upper_bunk"},
    4: {1: "lower_bunk", 2: "upper_bunk", 3: "lower_bunk", 4: "upper_bunk"},
    6: {1: "lower_bunk", 2: "upper_bunk", 3: "loft_type", 4: "lower_bunk", 5: "upper_bunk", 6: "loft_type"},
}

async def main():
    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as db:
        # Get all rooms with old columns via raw SQL
        rooms_result = await db.execute(text(
            "SELECT id, room_number, building, capacity, occupied_beds, rate_per_bed, status FROM rooms ORDER BY room_number"
        ))
        room_rows = rooms_result.mappings().all()

        # Get all active/reserved residents
        residents_result = await db.execute(
            select(models.Resident).where(models.Resident.status.in_(["active", "reserved"]))
        )
        residents = residents_result.scalars().all()

        # Group residents by monthly_rate
        residents_by_rate = {}
        for r in residents:
            rate = float(r.monthly_rate)
            residents_by_rate.setdefault(rate, []).append(r)

        # Group rooms by rate_per_bed
        rooms_by_rate = {}
        for room in room_rows:
            rate = float(room["rate_per_bed"])
            rooms_by_rate.setdefault(rate, []).append(room)

        # Create beds for each room
        bed_letter_map = {1: "A", 2: "B", 3: "C", 4: "D", 5: "E", 6: "F"}
        all_beds = []
        room_beds = {}  # room_id -> list of beds

        for room in room_rows:
            capacity = room["capacity"]
            bed_types = BED_TYPE_MAP.get(capacity, BED_TYPE_MAP[4])
            room_beds[room["id"]] = []

            for bed_num in range(1, capacity + 1):
                bed = models.Bed(
                    id=uuid.uuid4(),
                    bed_code=f"{room['room_number']}{bed_letter_map[bed_num]}",
                    room_id=room["id"],
                    bed_number=bed_num,
                    bed_type=bed_types.get(bed_num, "lower_bunk"),
                    rate_per_bed=room["rate_per_bed"],
                    status="available",
                )
                db.add(bed)
                all_beds.append(bed)
                room_beds[room["id"]].append(bed)

        await db.flush()

        # Assign residents to beds based on rate matching and occupied_beds
        for rate, rate_rooms in rooms_by_rate.items():
            rate_residents = residents_by_rate.get(rate, [])
            # Sort rooms by room_number for determinism
            rate_rooms_sorted = sorted(rate_rooms, key=lambda r: r["room_number"])

            resident_idx = 0
            for room in rate_rooms_sorted:
                occupied = room["occupied_beds"] or 0
                beds = room_beds[room["id"]]

                for _ in range(occupied):
                    if resident_idx < len(rate_residents) and beds:
                        resident = rate_residents[resident_idx]
                        bed = beds.pop(0)
                        bed.status = "occupied"
                        resident.bed_id = bed.id
                        resident_idx += 1

        await db.commit()

        # Update room statuses via ORM
        rooms_orm_result = await db.execute(select(models.Room))
        rooms_orm = rooms_orm_result.scalars().all()
        for room in rooms_orm:
            beds = room_beds.get(room.id, [])
            occupied = sum(1 for b in beds if b.status == "occupied")
            reserved = sum(1 for b in beds if b.status == "reserved")

            if occupied + reserved >= room.capacity:
                room.status = "full"
            elif occupied > 0 or reserved > 0:
                room.status = "partially_occupied"
            else:
                room.status = "available"

        await db.commit()

        # Summary
        total_beds = len(all_beds)
        assigned = sum(1 for r in residents if r.bed_id is not None)
        print(f"Created {total_beds} beds across {len(room_rows)} rooms")
        print(f"Assigned {assigned}/{len(residents)} residents to beds")

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(main())
