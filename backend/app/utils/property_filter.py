"""
Shared utility for applying property_code filtering across all routers.

Handles three filtering paths:
1. Direct: model has property_code (Room, Inquiry)
2. Via Resident chain: model -> Resident -> Bed -> Room -> property_code
3. Via building: model has building (MeterReading, MeterReadingImport) -> subquery through Room
"""
from sqlalchemy import select
from app import models


async def get_property_buildings(db, property_code: str) -> list[str]:
    """Get all building names that belong to a property."""
    result = await db.execute(
        select(models.Room.building)
        .where(models.Room.property_code == property_code)
        .where(models.Room.building.isnot(None))
        .distinct()
    )
    return [row[0] for row in result.all() if row[0]]


def filter_rooms_by_property(query, property_code: str):
    """Filter a Room query by property_code."""
    return query.where(models.Room.property_code == property_code)


def filter_inquiries_by_property(query, property_code: str):
    """Filter an Inquiry query by property_code (direct column)."""
    return query.where(models.Inquiry.property_code == property_code)
