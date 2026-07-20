from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy import text
from fastapi import Request
from typing import Optional
import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/dormtel")

engine = create_async_engine(DATABASE_URL, echo=False, future=True)
AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

Base = declarative_base()

ALLOWED_SCHEMAS = {"demo", "pilot"}
DEFAULT_SCHEMA = "demo"


def _extract_schema_from_request(request: Request = None) -> str:
    if not request:
        return DEFAULT_SCHEMA
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        token = auth[7:]
        try:
            from jose import jwt
            payload = jwt.decode(token, os.getenv("JWT_SECRET_KEY", "dormtel-dev-secret-change-in-production"), algorithms=["HS256"])
            schema = payload.get("schema", DEFAULT_SCHEMA)
            if schema in ALLOWED_SCHEMAS:
                return schema
        except Exception:
            pass
    # Unauthenticated callers (public QR inquiry form, tenant portal) declare
    # their schema via header; JWT above always wins when present.
    header_schema = request.headers.get("X-Tenant-Schema", "")
    if header_schema in ALLOWED_SCHEMAS:
        return header_schema
    return DEFAULT_SCHEMA


def _extract_property_from_request(request: Request = None) -> Optional[str]:
    """Extract property_code from JWT token in request."""
    if not request:
        return None
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header[7:]
        try:
            from jose import jwt
            payload = jwt.decode(token, os.getenv("JWT_SECRET_KEY", "dormtel-dev-secret-change-in-production"), algorithms=["HS256"])
            return payload.get("property_code")
        except Exception:
            pass
    return None


async def get_db(request: Request = None):
    schema = _extract_schema_from_request(request)
    async with AsyncSessionLocal() as session:
        try:
            if schema in ALLOWED_SCHEMAS:
                await session.execute(text(f"SET search_path TO {schema}, public"))
            yield session
        finally:
            await session.close()
