import os
import json
import uuid
import re
from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List
from io import BytesIO
from xml.sax.saxutils import escape as xml_escape

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

from app import models, auth
from app.database import get_db
from app.models import Resident, Bed, Room, Billing, BillingStatement, Payment, LedgerEntry
from app.schemas import (
    BillingStatementGenerateRequest,
    BillingStatementGenerateResponse,
    BillingStatementRow,
)
from app.routers import billing as billing_router

router = APIRouter()

STATEMENTS_BASE_DIR = os.environ.get("STATEMENTS_DIR", "/app/statements")


class StatementSendRequest(BaseModel):
    email: Optional[str] = None
    subject: Optional[str] = None
    body: Optional[str] = None


def _ensure_dir(path: str):
    os.makedirs(path, exist_ok=True)


def _safe_filename(name: str) -> str:
    return re.sub(r"[^\w\-]", "_", name).strip("_")[:50]


def _period_folder(period: str) -> str:
    return os.path.join(STATEMENTS_BASE_DIR, period, datetime.utcnow().strftime("%Y-%m-%d"))


def _compute_billing_for_resident(
    resident: Resident,
    billing_period: str,
    resident_electric: dict,
    resident_water: dict,
    resident_other: dict,
    fallback_other: Decimal,
    previous_balances: dict = None,
) -> dict:
    rid = str(resident.id)
    rent = resident.monthly_rate or Decimal("0")
    elec = resident_electric.get(rid, Decimal("0"))
    wat = resident_water.get(rid, Decimal("0"))
    other = resident_other.get(rid, fallback_other)
    prev_bal = (previous_balances or {}).get(rid, Decimal("0"))
    total = rent + elec + wat + other + prev_bal
    return {
        "rent_amount": rent,
        "electric_charge": elec,
        "water_charge": wat,
        "other_charges": other,
        "previous_balance": prev_bal,
        "total_amount": total,
    }


def _generate_pdf_statement(
    resident: Resident,
    bed: Optional[Bed],
    room: Optional[Room],
    billing_period: str,
    charges: dict,
    scope_type: str,
    scope_target: Optional[str],
) -> BytesIO:
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
    styles = getSampleStyleSheet()
    story = []

    resident_name = resident.full_name or "Unknown Resident"

    story.append(Paragraph("<b>DormTel Statement of Account</b>", styles["Title"]))
    story.append(Spacer(1, 12))
    story.append(Paragraph(f"Billing Period: <b>{xml_escape(billing_period)}</b>", styles["Normal"]))
    story.append(Paragraph(f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}", styles["Normal"]))
    if scope_type != "resident":
        story.append(Paragraph(f"Scope: {xml_escape(scope_type.title())} — {xml_escape(scope_target or 'N/A')}", styles["Normal"]))
    story.append(Spacer(1, 16))

    resident_info = [
        ["Resident", xml_escape(resident_name)],
        ["Email", xml_escape(resident.email) if resident.email else "—"],
        ["Phone", xml_escape(resident.phone) if resident.phone else "—"],
        ["Room", xml_escape(room.room_number) if room and room.room_number else "—"],
        ["Bed", xml_escape(bed.bed_code) if bed and bed.bed_code else "—"],
        ["Move-in", str(resident.move_in_date) if resident.move_in_date else "—"],
        ["Move-out", str(resident.move_out_date) if resident.move_out_date else "—"],
    ]
    info_table = Table(resident_info, colWidths=[120, 360])
    info_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), colors.lightgrey),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 20))

    charge_data = [
        ["Description", "Amount (₱)"],
        ["Rent", f"{charges['rent_amount']:,.2f}"],
        ["Electric", f"{charges['electric_charge']:,.2f}"],
        ["Water", f"{charges['water_charge']:,.2f}"],
        ["Other Charges", f"{charges['other_charges']:,.2f}"],
    ]
    prev_bal = charges.get("previous_balance", Decimal("0"))
    if prev_bal > 0:
        charge_data.append(["Previous Balance", f"{prev_bal:,.2f}"])
    charge_data.append(["Total Amount Due", f"{charges['total_amount']:,.2f}"])
    charge_table = Table(charge_data, colWidths=[360, 120])
    charge_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e3a5f")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("BACKGROUND", (0, -1), (-1, -1), colors.lightgrey),
        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    story.append(charge_table)
    story.append(Spacer(1, 20))
    story.append(Paragraph("Please settle your account on or before the due date. For questions, contact the administration office.", styles["Italic"]))

    doc.build(story)
    buffer.seek(0)
    return buffer


async def _send_statement_email(
    resident: Resident,
    statement: BillingStatement,
    subject: Optional[str],
    body: Optional[str],
) -> str:
    sendgrid_key = os.environ.get("SENDGRID_API_KEY")
    if not sendgrid_key:
        return "skipped_no_sendgrid_key"
    if not resident.email:
        return "skipped_no_email"

    try:
        from sendgrid import SendGridAPIClient
        from sendgrid.helpers.mail import Mail, Attachment, FileContent, FileName, FileType, Disposition
        import base64

        sg = SendGridAPIClient(sendgrid_key)
        message = Mail(
            from_email=os.environ.get("FROM_EMAIL", "billing@dormtel.app"),
            to_emails=resident.email,
            subject=subject or f"DormTel Statement of Account — {statement.billing_period}",
            html_content=body or f"<p>Hi {resident.full_name or 'Resident'},</p><p>Please find your statement of account for <strong>{statement.billing_period}</strong> attached.</p><p>Thank you.</p>",
        )
        with open(statement.file_path, "rb") as f:
            file_data = f.read()
        encoded = base64.b64encode(file_data).decode()
        attachment = Attachment(
            FileContent(encoded),
            FileName(statement.file_name),
            FileType("application/pdf"),
            Disposition("attachment"),
        )
        message.attachment = attachment
        response = sg.send(message)
        return f"sent_{response.status_code}"
    except Exception as e:
        return f"failed_{str(e)}"


@router.post("/generate", response_model=BillingStatementGenerateResponse)
async def generate_statements(
    data: BillingStatementGenerateRequest,
    db: AsyncSession = Depends(get_db),
    current_staff: models.Staff = Depends(auth.require_staff),
):
    # Resolve scope to a list of active residents
    query = (
        select(Resident, Bed, Room)
        .join(Bed, Resident.bed_id == Bed.id, isouter=True)
        .join(Room, Bed.room_id == Room.id, isouter=True)
        .where(Resident.status == "active")
    )

    if data.scope_type == "resident":
        if not data.scope_target:
            raise HTTPException(status_code=400, detail="scope_target (resident_id) is required for resident scope")
        try:
            query = query.where(Resident.id == uuid.UUID(data.scope_target))
        except ValueError:
            raise HTTPException(status_code=400, detail="scope_target must be a valid resident UUID")
    elif data.scope_type == "room":
        if not data.scope_target:
            raise HTTPException(status_code=400, detail="scope_target (room_id) is required for room scope")
        try:
            query = query.where(Room.id == uuid.UUID(data.scope_target))
        except ValueError:
            raise HTTPException(status_code=400, detail="scope_target must be a valid room UUID")
    elif data.scope_type == "floor":
        if not data.scope_target:
            raise HTTPException(status_code=400, detail="scope_target (floor prefix) is required for floor scope")
        query = query.where(Room.room_number.ilike(f"{data.scope_target}%"))
    elif data.scope_type == "property":
        if data.scope_target:
            query = query.where(
                (Room.property_code.ilike(data.scope_target)) | (Room.building.ilike(data.scope_target))
            )
    else:
        raise HTTPException(status_code=400, detail=f"Invalid scope_type: {data.scope_type}. Valid options: resident, room, floor, property")

    result = await db.execute(query)
    rows = result.all()
    if not rows:
        raise HTTPException(status_code=400, detail="No active residents match the selected scope")

    # Compute utilities for the period
    building = None
    if data.scope_type == "property":
        building = data.scope_target or None
    elif data.scope_type == "room":
        room_ids = {str(room.id) for _, _, room in rows if room}
        # Use the building of the first room as filter for readings
        if room_ids:
            first_room = next((room for _, _, room in rows if room), None)
            building = first_room.building if first_room else None

    resident_electric = await billing_router._compute_resident_electric(db, data.billing_period, building)
    resident_water, _, _ = await billing_router._compute_water_by_days(
        db, data.billing_period, data.total_water_bill, building
    )
    resident_other, total_other = await billing_router._compute_other_charges(
        db, data.billing_period, data.other_charges, building
    )
    fallback_other = Decimal("0")  # result_map already has per-resident values
    previous_balances = await billing_router._compute_previous_balances(
        db, data.billing_period, building
    )

    folder = _period_folder(data.billing_period)
    _ensure_dir(folder)

    generated = 0
    skipped = 0
    errors = []
    statements_out = []

    for resident, bed, room in rows:
        rid = str(resident.id)
        resident_name = resident.full_name or "Unknown Resident"
        charges = _compute_billing_for_resident(
            resident, data.billing_period, resident_electric, resident_water, resident_other, fallback_other, previous_balances
        )

        # Check for existing billing record and statement
        existing_billing_query = select(Billing).where(
            Billing.resident_id == resident.id,
            Billing.billing_period == data.billing_period,
        )
        existing_billing_result = await db.execute(existing_billing_query)
        existing_billing = existing_billing_result.scalar_one_or_none()

        existing_statement_query = select(BillingStatement).where(
            BillingStatement.resident_id == resident.id,
            BillingStatement.billing_period == data.billing_period,
        )
        existing_statement_result = await db.execute(existing_statement_query)
        existing_statement = existing_statement_result.scalar_one_or_none()

        if existing_statement and not data.regenerate:
            skipped += 1
            errors.append(f"Statement already exists for {resident_name}; use regenerate to overwrite")
            continue

        # Upsert Billing record
        if existing_billing:
            existing_billing.rent_amount = charges["rent_amount"]
            existing_billing.electric_charge = charges["electric_charge"]
            existing_billing.water_charge = charges["water_charge"]
            existing_billing.other_charges = charges["other_charges"]
            existing_billing.previous_balance = charges.get("previous_balance", Decimal("0"))
            existing_billing.total_amount = charges["total_amount"]
            # Preserve existing workflow status (do not regress approved/distributed/paid billings)
            if existing_billing.status not in ("approved", "distributed", "paid"):
                existing_billing.status = "draft"
            billing_record = existing_billing
        else:
            billing_record = Billing(
                resident_id=resident.id,
                billing_period=data.billing_period,
                rent_amount=charges["rent_amount"],
                electric_charge=charges["electric_charge"],
                water_charge=charges["water_charge"],
                other_charges=charges["other_charges"],
                previous_balance=charges.get("previous_balance", Decimal("0")),
                total_amount=charges["total_amount"],
                status="draft",
            )
            db.add(billing_record)

        # Generate PDF
        scope_target = data.scope_target
        if data.scope_type == "resident":
            scope_target = resident_name
        pdf_buffer = _generate_pdf_statement(resident, bed, room, data.billing_period, charges, data.scope_type, scope_target)
        pdf_bytes = pdf_buffer.getvalue()

        file_name = f"statement_{_safe_filename(data.billing_period)}_{_safe_filename(resident_name)}_{rid[:8]}.pdf"
        file_path = os.path.join(folder, file_name)
        with open(file_path, "wb") as f:
            f.write(pdf_bytes)

        metadata = {
            "resident_id": rid,
            "resident_name": resident_name,
            "billing_period": data.billing_period,
            "scope_type": data.scope_type,
            "scope_target": data.scope_target,
            "charges": {k: str(v) for k, v in charges.items()},
            "room_number": room.room_number if room else None,
            "bed_code": bed.bed_code if bed else None,
            "generated_at": datetime.utcnow().isoformat(),
        }
        with open(file_path + ".meta.json", "w") as f:
            json.dump(metadata, f, indent=2)

        # Upsert BillingStatement record (existing_statement already queried above)
        if existing_statement and data.regenerate:
            existing_statement.file_path = file_path
            existing_statement.file_name = file_name
            existing_statement.file_size = len(pdf_bytes)
            existing_statement.metadata_json = metadata
            existing_statement.status = "generated"
            existing_statement.scope_type = data.scope_type
            existing_statement.scope_target = data.scope_target
            statement_record = existing_statement
        elif not existing_statement:
            statement_record = BillingStatement(
                resident_id=resident.id,
                billing_period=data.billing_period,
                scope_type=data.scope_type,
                scope_target=data.scope_target,
                file_path=file_path,
                file_name=file_name,
                file_size=len(pdf_bytes),
                metadata_json=metadata,
                status="generated",
            )
            db.add(statement_record)

        # Create debit ledger entry for new billing records
        if not existing_billing:
            await db.flush()  # ensure billing_record.id is available
            await billing_router._create_debit_ledger_entry(
                db,
                resident_id=billing_record.resident_id,
                amount=billing_record.total_amount,
                description=f"Billing for {billing_record.billing_period}",
                reference_id=billing_record.id,
            )

        await db.commit()
        await db.refresh(statement_record)
        await db.refresh(billing_record)

        # Optional auto-send email
        email_status = None
        if data.auto_send_email:
            email_status = await _send_statement_email(resident, statement_record, data.email_subject, data.email_body)
            statement_record.email_status = email_status
            if email_status.startswith("sent_"):
                statement_record.status = "sent"
                statement_record.sent_at = datetime.utcnow()
                statement_record.sent_to = resident.email
            await db.commit()

        generated += 1
        statements_out.append(BillingStatementRow(
            statement_id=statement_record.id,
            resident_id=resident.id,
            resident_name=resident_name,
            billing_period=data.billing_period,
            scope_type=data.scope_type,
            scope_target=data.scope_target,
            file_name=file_name,
            file_path=file_path,
            file_size=len(pdf_bytes),
            status=statement_record.status,
            sent_to=statement_record.sent_to,
            sent_at=statement_record.sent_at,
            email_status=email_status or statement_record.email_status,
            created_at=statement_record.created_at,
            total_amount=charges["total_amount"],
        ))

    # Write batch manifest
    manifest_path = os.path.join(folder, "manifest.json")
    manifest = {
        "billing_period": data.billing_period,
        "scope_type": data.scope_type,
        "scope_target": data.scope_target,
        "generated_at": datetime.utcnow().isoformat(),
        "generated_count": generated,
        "skipped_count": skipped,
        "errors": errors,
        "statements": [
            {
                "statement_id": str(s.statement_id),
                "resident_id": str(s.resident_id),
                "resident_name": s.resident_name,
                "file_name": s.file_name,
                "total_amount": str(s.total_amount),
                "status": s.status,
            }
            for s in statements_out
        ],
    }
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)

    return BillingStatementGenerateResponse(
        generated=generated,
        skipped=skipped,
        errors=errors,
        statements=statements_out,
    )


@router.get("/", response_model=List[BillingStatementRow])
async def list_statements(
    resident_id: Optional[uuid.UUID] = Query(None),
    billing_period: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
    current_staff: models.Staff = Depends(auth.require_staff),
):
    query = (
        select(BillingStatement, Resident)
        .join(Resident, BillingStatement.resident_id == Resident.id)
        .order_by(BillingStatement.created_at.desc())
    )
    if resident_id:
        query = query.where(BillingStatement.resident_id == resident_id)
    if billing_period:
        query = query.where(BillingStatement.billing_period == billing_period)
    query = query.limit(limit)
    result = await db.execute(query)
    out = []
    for stmt, resident in result.all():
        total = None
        if stmt.metadata_json and "charges" in stmt.metadata_json:
            try:
                total = Decimal(stmt.metadata_json["charges"].get("total_amount", "0"))
            except Exception:
                pass
        out.append(BillingStatementRow(
            statement_id=stmt.id,
            resident_id=stmt.resident_id,
            resident_name=resident.full_name if resident else None,
            billing_period=stmt.billing_period,
            scope_type=stmt.scope_type,
            scope_target=stmt.scope_target,
            file_name=stmt.file_name,
            file_path=stmt.file_path,
            file_size=stmt.file_size,
            status=stmt.status,
            sent_to=stmt.sent_to,
            sent_at=stmt.sent_at,
            email_status=stmt.email_status,
            created_at=stmt.created_at,
            total_amount=total,
        ))
    return out


@router.get("/{statement_id}/download")
async def download_statement(
    statement_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_staff: models.Staff = Depends(auth.require_staff),
):
    stmt = await db.get(BillingStatement, statement_id)
    if not stmt:
        raise HTTPException(status_code=404, detail="Statement not found")
    if not os.path.exists(stmt.file_path):
        raise HTTPException(status_code=404, detail="Statement file not found")
    return FileResponse(
        stmt.file_path,
        filename=stmt.file_name,
        media_type="application/pdf",
    )


@router.post("/{statement_id}/send-email")
async def send_statement_email(
    statement_id: uuid.UUID,
    payload: StatementSendRequest,
    db: AsyncSession = Depends(get_db),
    current_staff: models.Staff = Depends(auth.require_staff),
):
    stmt = await db.get(BillingStatement, statement_id)
    if not stmt:
        raise HTTPException(status_code=404, detail="Statement not found")

    resident = await db.get(Resident, stmt.resident_id)
    if not resident:
        raise HTTPException(status_code=404, detail="Resident not found")

    email = payload.email or resident.email
    if not email:
        raise HTTPException(status_code=400, detail="No recipient email available")

    email_status = await _send_statement_email(resident, stmt, payload.subject, payload.body)
    stmt.email_status = email_status
    if email_status.startswith("sent_"):
        stmt.status = "sent"
        stmt.sent_at = datetime.utcnow()
        stmt.sent_to = email
    await db.commit()
    await db.refresh(stmt)
    return {"status": email_status}
