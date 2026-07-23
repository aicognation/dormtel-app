from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy import text
from fastapi import Request
from typing import Optional
import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/dormtel")

engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    future=True,
    # --- Connection pool hardening (FIX-014) ---
    # pool_pre_ping: emit a lightweight "SELECT 1" before handing a connection
    # to the application. If the connection is dead (killed by PG idle timeout,
    # network blip, container restart), it is silently discarded and replaced
    # instead of surfacing "Failed to connect to database" to the user.
    pool_pre_ping=True,
    # pool_recycle: proactively recycle connections after 5 minutes.
    # PostgreSQL's default tcp_keepalives_idle can kill idle connections;
    # recycling before that threshold avoids ever hitting a dead socket.
    pool_recycle=300,
    # pool_size / max_overflow: sized for moderate concurrent admin + tenant
    # traffic on a single ECS instance. 10 persistent + 20 burst = 30 max.
    pool_size=10,
    max_overflow=20,
    # pool_timeout: wait up to 30s for a free connection before raising.
    pool_timeout=30,
)
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
    if schema not in ALLOWED_SCHEMAS:
        schema = DEFAULT_SCHEMA
    # Pin the entire request to ONE dedicated connection.
    #
    # SET search_path is a per-connection (backend) setting. The previous
    # implementation ran it on the session's first connection, but a
    # SQLAlchemy async session returns its connection to the pool on every
    # commit() and may acquire a DIFFERENT connection for the next statement.
    # Under concurrent load, post-commit statements (e.g. db.refresh() right
    # after an INSERT) could execute on a connection still carrying another
    # tenant's search_path - or a fresh connection's default of "$user",
    # public - silently resolving unqualified tables to the wrong schema.
    # In production this surfaced as inquiry creation 500-ing with
    # 'column inquiries.campaign_id does not exist' because the refresh
    # SELECT landed on the legacy public.inquiries table.
    #
    # Binding the session to a single connection guarantees every statement
    # in the request - before OR after commit - uses the correct search_path.
    async with engine.connect() as conn:
        await conn.execute(text(f"SET search_path TO {schema}, public"))
        # End the transaction opened by the SET so the session manages its
        # own transactions on this connection. A plain SET is session-scoped
        # and survives this commit.
        await conn.commit()
        async with AsyncSession(bind=conn, expire_on_commit=False) as session:
            yield session
