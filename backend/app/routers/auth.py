from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text
from datetime import datetime, timedelta
from uuid import UUID
import uuid

from app.database import get_db, ALLOWED_SCHEMAS, DEFAULT_SCHEMA
from app import models, schemas, auth

router = APIRouter()


@router.post("/login", response_model=schemas.StaffLoginResponse)
async def login(payload: schemas.StaffLoginRequest, db: AsyncSession = Depends(get_db)):
    # Validate and apply selected schema for login
    db_schema_name = payload.db_schema if payload.db_schema in ALLOWED_SCHEMAS else DEFAULT_SCHEMA
    await db.execute(text(f"SET search_path TO {db_schema_name}, public"))

    result = await db.execute(select(models.Staff).where(models.Staff.email == payload.email))
    staff = result.scalar_one_or_none()
    if not staff or not staff.password_hash:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    if not auth.verify_password(payload.password, staff.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    if not staff.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account inactive")

    staff.last_login_at = datetime.utcnow()
    await db.commit()

    access_token = auth.create_access_token(data={"sub": str(staff.id), "role": staff.role, "schema": db_schema_name})
    return schemas.StaffLoginResponse(
        access_token=access_token,
        staff=schemas.StaffOut.model_validate(staff),
        requires_property_selection=True,
    )


@router.get("/properties")
async def list_properties(db: AsyncSession = Depends(get_db)):
    """List all active properties. No auth required."""
    result = await db.execute(
        select(models.Property).where(models.Property.is_active == True).order_by(models.Property.code)
    )
    properties = result.scalars().all()
    return [
        {"code": p.code, "name": p.name, "address": p.address}
        for p in properties
    ]


@router.post("/select-property")
async def select_property(
    payload: schemas.PropertySelectRequest,
    request: Request,
    current_staff: models.Staff = Depends(auth.get_current_staff),
    db: AsyncSession = Depends(get_db),
):
    """Issue a new JWT with property_code embedded."""
    # Validate property exists
    result = await db.execute(
        select(models.Property).where(models.Property.code == payload.property_code)
    )
    prop = result.scalar_one_or_none()
    if not prop:
        raise HTTPException(status_code=400, detail="Invalid property code")

    # Extract schema from current JWT
    auth_header = request.headers.get("Authorization", "")
    schema_name = "demo"
    if auth_header.startswith("Bearer "):
        from jose import jwt as jose_jwt
        try:
            token_payload = jose_jwt.decode(
                auth_header[7:],
                auth.SECRET_KEY,
                algorithms=[auth.ALGORITHM]
            )
            schema_name = token_payload.get("schema", "demo")
        except Exception:
            pass

    # Issue new token with property_code
    access_token = auth.create_access_token(data={
        "sub": str(current_staff.id),
        "role": current_staff.role,
        "schema": schema_name,
        "property_code": payload.property_code,
    })
    return schemas.PropertyLoginResponse(
        access_token=access_token,
        property_code=payload.property_code,
        property_name=prop.name,
    )


@router.post("/password-reset-request")
async def password_reset_request(payload: schemas.PasswordResetRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(models.Staff).where(models.Staff.email == payload.email))
    staff = result.scalar_one_or_none()
    if not staff:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Email not found")

    token = auth.generate_reset_token()
    token_hash = auth.get_password_hash(token)
    reset = models.PasswordReset(
        id=uuid.uuid4(),
        staff_id=staff.id,
        token_hash=token_hash,
        expires_at=datetime.utcnow() + timedelta(hours=1),
    )
    db.add(reset)

    # Notify super admin
    admin_result = await db.execute(select(models.Staff).where(models.Staff.role == "manager"))
    admins = admin_result.scalars().all()
    for admin in admins:
        if admin.id != staff.id:
            note = models.Notification(
                id=uuid.uuid4(),
                staff_id=admin.id,
                type="password_reset",
                message=f"Password reset requested for {staff.email} ({staff.full_name}).",
            )
            db.add(note)

    await db.commit()

    # In demo mode, return the token directly since we have no SMTP
    return {"message": "Password reset requested. Use the token to reset.", "token": token, "staff_id": str(staff.id)}


@router.post("/password-reset-confirm")
async def password_reset_confirm(payload: schemas.PasswordResetConfirm, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(models.PasswordReset)
        .where(models.PasswordReset.used_at.is_(None))
        .where(models.PasswordReset.expires_at > datetime.utcnow())
    )
    resets = result.scalars().all()

    matched = None
    for r in resets:
        if auth.verify_password(payload.token, r.token_hash):
            matched = r
            break

    if not matched:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired token")

    staff_result = await db.execute(select(models.Staff).where(models.Staff.id == matched.staff_id))
    staff = staff_result.scalar_one_or_none()
    if not staff:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    staff.password_hash = auth.get_password_hash(payload.new_password)
    matched.used_at = datetime.utcnow()
    await db.commit()
    return {"message": "Password reset successful"}


@router.post("/verification-code-request")
async def verification_code_request(
    payload: schemas.VerificationCodeRequest,
    current_staff: models.Staff = Depends(auth.require_manager),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(models.Staff).where(models.Staff.id == payload.staff_id))
    staff = result.scalar_one_or_none()
    if not staff:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Staff not found")

    code = str(auth.generate_verification_code())
    vc = models.VerificationCode(
        id=uuid.uuid4(),
        staff_id=staff.id,
        code=code,
        purpose="email_verification",
        expires_at=datetime.utcnow() + timedelta(hours=24),
    )
    db.add(vc)
    await db.commit()

    # In demo mode, return the code directly
    return {"message": "Verification code generated.", "code": code, "staff_id": str(staff.id)}


@router.post("/verification-code-verify")
async def verification_code_verify(payload: schemas.VerificationCodeVerify, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(models.VerificationCode)
        .where(models.VerificationCode.staff_id == payload.staff_id)
        .where(models.VerificationCode.code == payload.code)
        .where(models.VerificationCode.purpose == "email_verification")
        .where(models.VerificationCode.used_at.is_(None))
        .where(models.VerificationCode.expires_at > datetime.utcnow())
    )
    vc = result.scalar_one_or_none()
    if not vc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired code")

    staff_result = await db.execute(select(models.Staff).where(models.Staff.id == payload.staff_id))
    staff = staff_result.scalar_one_or_none()
    if staff:
        staff.is_verified = True
        staff.email_verified_at = datetime.utcnow()

    vc.used_at = datetime.utcnow()
    await db.commit()
    return {"message": "Email verified successfully"}


# --- Staff Management (Super Admin only) ---

@router.get("/staff", response_model=list[schemas.StaffOut])
async def list_staff(
    current_staff: models.Staff = Depends(auth.require_staff),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(models.Staff).order_by(models.Staff.created_at.desc()))
    return result.scalars().all()


@router.post("/staff", response_model=schemas.StaffOut, status_code=status.HTTP_201_CREATED)
async def create_staff(
    payload: schemas.StaffCreate,
    current_staff: models.Staff = Depends(auth.require_manager),
    db: AsyncSession = Depends(get_db),
):
    existing = await db.execute(select(models.Staff).where(models.Staff.email == payload.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    # staff.id is client-generated (uuid4), so the verification code row can
    # be added in the SAME transaction -- a failure rolls back both instead of
    # leaving a staff row with no password and no verification code.
    staff = models.Staff(
        id=uuid.uuid4(),
        full_name=payload.full_name,
        email=payload.email,
        phone=payload.phone,
        role=payload.role,
        managed_branch=payload.managed_branch,
        password_hash=auth.get_password_hash(payload.password) if payload.password else None,
        created_at=datetime.utcnow(),
    )
    db.add(staff)

    if not staff.password_hash:
        code = str(auth.generate_verification_code())
        vc = models.VerificationCode(
            id=uuid.uuid4(),
            staff_id=staff.id,
            code=code,
            purpose="email_verification",
            expires_at=datetime.utcnow() + timedelta(hours=24),
        )
        db.add(vc)

    await db.commit()
    await db.refresh(staff)
    return schemas.StaffOut.model_validate(staff)


@router.patch("/staff/{staff_id}", response_model=schemas.StaffOut)
async def update_staff(
    staff_id: UUID,
    payload: schemas.StaffUpdate,
    current_staff: models.Staff = Depends(auth.require_manager),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(models.Staff).where(models.Staff.id == staff_id))
    staff = result.scalar_one_or_none()
    if not staff:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Staff not found")

    if payload.full_name is not None:
        staff.full_name = payload.full_name
    if payload.phone is not None:
        staff.phone = payload.phone
    if payload.role is not None:
        staff.role = payload.role
    if payload.managed_branch is not None:
        staff.managed_branch = payload.managed_branch
    if payload.is_active is not None:
        staff.is_active = payload.is_active

    await db.commit()
    await db.refresh(staff)
    return schemas.StaffOut.model_validate(staff)


# --- Notifications ---

@router.get("/notifications", response_model=list[schemas.NotificationOut])
async def list_notifications(
    current_staff: models.Staff = Depends(auth.get_current_staff),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(models.Notification)
        .where(models.Notification.staff_id == current_staff.id)
        .order_by(models.Notification.created_at.desc())
    )
    return result.scalars().all()


@router.post("/notifications/{notification_id}/read")
async def mark_notification_read(
    notification_id: UUID,
    current_staff: models.Staff = Depends(auth.get_current_staff),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(models.Notification)
        .where(models.Notification.id == notification_id)
        .where(models.Notification.staff_id == current_staff.id)
    )
    note = result.scalar_one_or_none()
    if not note:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")
    note.is_read = True
    await db.commit()
    return {"message": "Marked as read"}


# --- Me ---

@router.get("/me", response_model=schemas.StaffOut)
async def get_me(current_staff: models.Staff = Depends(auth.get_current_staff)):
    return schemas.StaffOut.model_validate(current_staff)
