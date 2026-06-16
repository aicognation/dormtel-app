import asyncio
import uuid
from datetime import datetime, date, timedelta
from decimal import Decimal
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://dormtel:dormtel_pass@db:5432/dormtel_db")

engine = create_async_engine(DATABASE_URL)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def seed():
    async with AsyncSessionLocal() as session:
        # Clear existing data
        await session.execute(text("DELETE FROM service_requests"))
        await session.execute(text("DELETE FROM announcements"))
        await session.execute(text("DELETE FROM move_outs"))
        await session.execute(text("DELETE FROM ledger_entries"))
        await session.execute(text("DELETE FROM payments"))
        await session.execute(text("DELETE FROM billings"))
        await session.execute(text("DELETE FROM inquiries"))
        await session.execute(text("DELETE FROM residents"))
        await session.execute(text("DELETE FROM rooms"))
        await session.execute(text("DELETE FROM staff"))
        await session.execute(text("DELETE FROM meter_readings"))
        await session.commit()

        # STAFF
        staff_id = str(uuid.uuid4())
        await session.execute(text(
            "INSERT INTO staff (id, full_name, email, role, phone, created_at) VALUES (:id, :name, :email, :role, :phone, :created)"
        ), {"id": staff_id, "name": "Maria Santos", "email": "maria@dormtel.com", "role": "manager", "phone": "09171234567", "created": datetime(2025, 1, 15)})

        # ROOMS - 3 buildings, realistic dormitory layout
        rooms = []
        buildings = [
            ("Tower A", [("A101", 4, 6500), ("A102", 4, 6500), ("A103", 6, 5800), ("A104", 6, 5800), ("A105", 2, 8500), ("A106", 4, 6500), ("A201", 4, 6500), ("A202", 6, 5800), ("A203", 2, 8500), ("A204", 4, 6500)]),
            ("Tower B", [("B101", 4, 6000), ("B102", 6, 5500), ("B103", 4, 6000), ("B104", 2, 8000), ("B105", 6, 5500), ("B201", 4, 6000), ("B202", 6, 5500), ("B203", 4, 6000), ("B204", 2, 8000), ("B205", 4, 6000)]),
            ("Tower C", [("C101", 2, 9000), ("C102", 2, 9000), ("C103", 4, 7000), ("C104", 4, 7000), ("C105", 4, 7000)])
        ]

        for building, room_list in buildings:
            for room_num, capacity, rate in room_list:
                rid = str(uuid.uuid4())
                rooms.append((rid, room_num, building, capacity, rate))
                await session.execute(text(
                    "INSERT INTO rooms (id, room_number, building, capacity, occupied_beds, rate_per_bed, status) VALUES (:id, :num, :bldg, :cap, 0, :rate, :status)"
                ), {"id": rid, "num": room_num, "bldg": building, "cap": capacity, "rate": rate, "status": "available"})

        # RESIDENTS - 18 total (15 active, 3 reserved)
        resident_data = [
            ("Juan dela Cruz", "juan.delacruz@email.com", "09171111001", "active", 0, 6500),
            ("Ana Marie Reyes", "ana.reyes@email.com", "09171111002", "active", 0, 6500),
            ("Carlo Miguel Santos", "carlo.santos@email.com", "09171111003", "active", 1, 6500),
            ("Patricia Mae Garcia", "patricia.garcia@email.com", "09171111004", "active", 2, 5800),
            ("Jose Rizal Jr.", "jose.rizal@email.com", "09171111005", "active", 2, 5800),
            ("Maria Clara Bautista", "maria.clara@email.com", "09171111006", "active", 4, 8500),
            ("Andrew James Tan", "andrew.tan@email.com", "09171111007", "active", 3, 5800),
            ("Sofia Isabel Cruz", "sofia.cruz@email.com", "09171111008", "active", 10, 6000),
            ("Miguel Angelo Ramos", "miguel.ramos@email.com", "09171111009", "active", 11, 5500),
            ("Bianca Joy Mendoza", "bianca.mendoza@email.com", "09171111010", "active", 11, 5500),
            ("Gabriel Lim", "gabriel.lim@email.com", "09171111011", "active", 12, 6000),
            ("Isabelle Rose Torres", "isabelle.torres@email.com", "09171111012", "active", 13, 8000),
            ("Rafael Martin Aquino", "rafael.aquino@email.com", "09171111013", "active", 20, 9000),
            ("Camille Anne Villanueva", "camille.villanueva@email.com", "09171111014", "active", 21, 9000),
            ("Daniel Patrick Ong", "daniel.ong@email.com", "09171111015", "active", 22, 7000),
            ("Katherine May Sy", "katherine.sy@email.com", "09171111016", "reserved", 23, 7000),
            ("Mark Joseph Rivera", "mark.rivera@email.com", "09171111017", "reserved", 24, 7000),
            ("Nicole Anne Chua", "nicole.chua@email.com", "09171111018", "reserved", None, 7000),
        ]

        resident_ids = []
        for i, (name, email, phone, status, room_idx, rate) in enumerate(resident_data):
            rid = str(uuid.uuid4())
            resident_ids.append(rid)
            room_id = rooms[room_idx][0] if room_idx is not None and room_idx < len(rooms) else None
            bed = (i % 4) + 1
            move_in = date(2025, 6, 1) + timedelta(days=i * 15) if status == "active" else None
            await session.execute(text(
                "INSERT INTO residents (id, full_name, email, phone, status, room_id, bed_number, monthly_rate, move_in_date, id_type, id_number, created_at, updated_at) VALUES (:id, :name, :email, :phone, :status, :room_id, :bed, :rate, :move_in, :id_type, :id_num, :created, :updated)"
            ), {
                "id": rid, "name": name, "email": email, "phone": phone,
                "status": status, "room_id": room_id, "bed": bed,
                "rate": rate, "move_in": move_in,
                "id_type": "national_id", "id_num": f"PSN-{1000+i}",
                "created": datetime(2025, 5, 1) + timedelta(days=i*10),
                "updated": datetime(2025, 5, 1) + timedelta(days=i*10),
            })

        # Update room occupied_beds counts
        room_occupancy = {}
        for i, (name, email, phone, status, room_idx, rate) in enumerate(resident_data):
            if status == "active" and room_idx is not None and room_idx < len(rooms):
                room_occupancy[room_idx] = room_occupancy.get(room_idx, 0) + 1

        for room_idx, count in room_occupancy.items():
            rid = rooms[room_idx][0]
            cap = rooms[room_idx][3]
            st = "full" if count >= cap else "available"
            await session.execute(text("UPDATE rooms SET occupied_beds = :count, status = :st WHERE id = :id"),
                {"count": count, "st": st, "id": rid})

        # INQUIRIES - mix of statuses and sources
        inquiry_data = [
            ("facebook", "Hi! I saw your ad. How much is a bed space in Tower A?", "new", 0.85, 78),
            ("instagram", "Is there available room for 2 students near UST? Move in June.", "new", 0.90, 85),
            ("tiktok", "Saw your TikTok tour video! Do you accept short-term stays?", "new", 0.72, 60),
            ("walkin", "Walk-in inquiry about Tower C premium rooms. Very interested.", "responded", 0.95, 92),
            ("facebook", "How do I reserve a bed? Can I pay via GCash?", "responded", 0.88, 80),
            ("phone", "Parent calling to inquire about safety features and visiting hours.", "responded", 0.82, 75),
            ("instagram", "Looking for a room near my workplace. Budget is 7k.", "escalated", 0.65, 55),
            ("walkin", "Group of 3 friends looking for beds in same room. Tower B preferred.", "new", 0.92, 88),
            ("facebook", "Is there parking available? I have a motorcycle.", "converted", 0.78, 70),
            ("tiktok", "Love the amenities! When is the next available slot?", "new", 0.88, 82),
            ("phone", "Asking about refund policy if I move out early.", "closed", 0.30, 20),
            ("walkin", "Student transferee from province. Needs bed ASAP.", "new", 0.95, 90),
        ]

        for i, (source, content, status, sentiment, lead) in enumerate(inquiry_data):
            iid = str(uuid.uuid4())
            await session.execute(text(
                "INSERT INTO inquiries (id, source, content, status, sentiment_score, lead_score, created_at) VALUES (:id, :source, :content, :status, :sentiment, :lead, :created)"
            ), {
                "id": iid, "source": source, "content": content,
                "status": status, "sentiment": sentiment, "lead": lead,
                "created": datetime(2026, 5, 10) + timedelta(hours=i*6)
            })

        # BILLINGS - for active residents, May 2026 period
        billing_ids = []
        billing_statuses = ["approved", "distributed", "distributed", "pending_review", "pending_review", "distributed", "approved", "distributed", "paid", "paid", "distributed", "pending_review", "distributed", "distributed", "pending_review"]
        for i in range(min(15, len(resident_ids))):
            bid = str(uuid.uuid4())
            billing_ids.append(bid)
            rate = resident_data[i][5]
            electric = round(350 + (i * 45), 2)
            water = round(150 + (i * 20), 2)
            total = rate + electric + water
            status = billing_statuses[i]
            await session.execute(text(
                "INSERT INTO billings (id, resident_id, billing_period, rent_amount, electric_charge, water_charge, other_charges, total_amount, status, created_at) VALUES (:id, :res_id, :period, :rent, :elec, :water, :other, :total, :status, :created)"
            ), {
                "id": bid, "res_id": resident_ids[i], "period": "2026-05",
                "rent": rate, "elec": electric, "water": water, "other": 0,
                "total": total, "status": status,
                "created": datetime(2026, 5, 1, 8, 0) + timedelta(hours=i)
            })

        # PAYMENTS - mix of matched and unmatched
        payment_data = [
            (0, 7000, "gcash", "verified", "GC-2026051701"),
            (1, 7000, "gcash", "matched", "GC-2026051702"),
            (2, 6600, "maya", "matched", "MY-2026051703"),
            (3, 6200, "bank_transfer", "verified", "BT-2026051704"),
            (4, 6700, "gcash", "pending", "GC-2026051705"),
            (5, 5950, "cash", "matched", None),
            (8, 7100, "gcash", "matched", "GC-2026051708"),
            (9, 7300, "maya", "matched", "MY-2026051709"),
            (10, 6800, "bank_transfer", "verified", "BT-2026051710"),
            (11, 8500, "gcash", "unreconciled", "GC-2026051711"),
            (12, 9800, "maya", "pending", "MY-2026051712"),
            (13, 9700, "gcash", "verified", "GC-2026051713"),
        ]

        for res_idx, amount, method, status, ref in payment_data:
            pid = str(uuid.uuid4())
            await session.execute(text(
                "INSERT INTO payments (id, resident_id, amount, method, status, gateway_ref, created_at) VALUES (:id, :res_id, :amount, :method, :status, :ref, :created)"
            ), {
                "id": pid, "res_id": resident_ids[res_idx],
                "amount": amount, "method": method,
                "status": status, "ref": ref,
                "created": datetime(2026, 5, 15, 9, 0) + timedelta(hours=res_idx * 2)
            })

        # MOVE-OUTS - 3 in different statuses
        moveout_data = [
            (7, date(2026, 6, 1), "Graduating and moving back to province", "09189990001", "requested"),
            (9, date(2026, 5, 30), "Transferring to another dormitory closer to work", "09189990002", "clearance"),
            (4, date(2026, 6, 15), "End of internship period", "09189990003", "requested"),
        ]

        for res_idx, req_date, reason, contact, status in moveout_data:
            mid = str(uuid.uuid4())
            await session.execute(text(
                "INSERT INTO move_outs (id, resident_id, requested_date, reason, forwarding_contact, status, created_at) VALUES (:id, :res_id, :date, :reason, :contact, :status, :created)"
            ), {
                "id": mid, "res_id": resident_ids[res_idx],
                "date": req_date, "reason": reason,
                "contact": contact, "status": status,
                "created": datetime(2026, 5, 14, 10, 0)
            })

        # METER READINGS
        meter_data = [
            ("Tower A", date(2026, 5, 1), 4520.50, 1280.30),
            ("Tower B", date(2026, 5, 1), 3890.75, 1050.20),
            ("Tower C", date(2026, 5, 1), 2150.25, 680.10),
            ("Tower A", date(2026, 4, 1), 4180.20, 1190.50),
            ("Tower B", date(2026, 4, 1), 3620.40, 980.80),
            ("Tower C", date(2026, 4, 1), 1980.60, 620.30),
        ]

        for building, rdate, elec, water in meter_data:
            mrid = str(uuid.uuid4())
            await session.execute(text(
                "INSERT INTO meter_readings (id, building, reading_date, electric_reading, water_reading, status) VALUES (:id, :bldg, :date, :elec, :water, :status)"
            ), {
                "id": mrid, "bldg": building, "date": rdate,
                "elec": elec, "water": water, "status": "approved"
            })

        # HISTORICAL BILLINGS for demo tenant (Juan dela Cruz, index 0) - April & March 2026
        hist_billing_data = [
            ("2026-04", 6500, 310, 130, "paid"),
            ("2026-03", 6500, 290, 120, "paid"),
        ]
        for period, rent, elec, water, bstatus in hist_billing_data:
            hbid = str(uuid.uuid4())
            await session.execute(text(
                "INSERT INTO billings (id, resident_id, billing_period, rent_amount, electric_charge, water_charge, other_charges, total_amount, status, created_at) VALUES (:id, :res_id, :period, :rent, :elec, :water, :other, :total, :status, :created)"
            ), {
                "id": hbid, "res_id": resident_ids[0], "period": period,
                "rent": rent, "elec": elec, "water": water, "other": 0,
                "total": rent + elec + water, "status": bstatus,
                "created": datetime(2026, int(period.split("-")[1]), 1, 8, 0),
            })

        # HISTORICAL PAYMENTS for demo tenant - matching above billings
        hist_payment_data = [
            (6940, "gcash", "matched", "GC-2026041501", datetime(2026, 4, 15, 10, 30)),
            (6910, "maya", "matched", "MY-2026031502", datetime(2026, 3, 16, 9, 15)),
        ]
        for amt, method, pstatus, ref, created in hist_payment_data:
            hpid = str(uuid.uuid4())
            await session.execute(text(
                "INSERT INTO payments (id, resident_id, amount, method, status, gateway_ref, matched_at, created_at) VALUES (:id, :res_id, :amount, :method, :status, :ref, :matched, :created)"
            ), {
                "id": hpid, "res_id": resident_ids[0],
                "amount": amt, "method": method, "status": pstatus,
                "ref": ref, "matched": created, "created": created,
            })

        # SERVICE REQUESTS - 12 across multiple residents
        service_request_data = [
            (0, "aircon", "Aircon not cooling properly", "Unit blows warm air even at lowest temperature setting. Started 2 days ago.", "Room A101", "high", "resolved", datetime(2026, 5, 13, 8, 0), "Replaced aircon filter and recharged refrigerant. Unit tested and confirmed working."),
            (0, "plumbing", "Bathroom faucet leaking", "The faucet in the bathroom drips continuously even when fully closed.", "Room A101, bathroom", "medium", "in_progress", datetime(2026, 5, 16, 14, 30), None),
            (1, "wifi", "WiFi connection keeps dropping", "Internet connection drops every 30 minutes. Need to reconnect manually each time.", "Room A102", "high", "acknowledged", datetime(2026, 5, 17, 9, 0), None),
            (2, "electrical", "Power outlet not working near desk", "The outlet closest to my study desk stopped working yesterday.", "Room A103, near window", "medium", "submitted", datetime(2026, 5, 18, 6, 0), None),
            (3, "pest_control", "Cockroach sighting in kitchen area", "Found several cockroaches in the shared kitchen area during evening.", "Tower A, shared kitchen", "high", "resolved", datetime(2026, 5, 11, 20, 0), "Pest control treatment applied to kitchen and surrounding areas. Follow-up scheduled in 2 weeks."),
            (4, "lock_key", "Room door lock is stiff", "Room door lock is very hard to turn. Key gets stuck sometimes.", "Room A103", "medium", "in_progress", datetime(2026, 5, 14, 11, 0), None),
            (5, "water_supply", "Low water pressure in shower", "Water pressure has been very low since last week. Takes long to shower.", "Room A105, bathroom", "medium", "submitted", datetime(2026, 5, 18, 7, 30), None),
            (6, "aircon", "Aircon making loud noise", "The aircon unit makes a rattling noise when set to high fan speed.", "Room A103", "low", "acknowledged", datetime(2026, 5, 17, 15, 0), None),
            (7, "cleaning", "Common area bathroom needs deep cleaning", "The shared bathroom on 2nd floor needs thorough cleaning. Tiles are stained.", "Tower A, 2F bathroom", "medium", "resolved", datetime(2026, 5, 8, 10, 0), "Deep cleaning completed. Tiles scrubbed and sanitized. Will schedule regular weekly deep clean."),
            (8, "appliance", "Shared refrigerator not cooling", "The refrigerator in the common pantry is not maintaining cold temperature.", "Tower B, common pantry", "high", "in_progress", datetime(2026, 5, 15, 16, 0), None),
            (0, "electrical", "Flickering light in hallway", "The hallway light outside Room A101 has been flickering for the past 3 days.", "Tower A, 1F hallway", "low", "submitted", datetime(2026, 5, 18, 8, 0), None),
            (9, "wifi", "Cannot connect to 5GHz network", "My laptop cannot detect the 5GHz WiFi network. Only 2.4GHz is visible.", "Room B102", "low", "resolved", datetime(2026, 5, 12, 13, 0), "Router firmware updated and 5GHz band re-enabled. Tested with resident device - connection stable."),
        ]

        for res_idx, cat, subject, desc, loc, priority, sr_status, submitted, resolution in service_request_data:
            srid = str(uuid.uuid4())
            resolved_at = (submitted + timedelta(days=2)) if sr_status == "resolved" else None
            await session.execute(text(
                "INSERT INTO service_requests (id, resident_id, category, subject, description, location, priority, status, resolution_notes, submitted_at, resolved_at, created_at) VALUES (:id, :res_id, :cat, :subj, :desc, :loc, :pri, :status, :notes, :submitted, :resolved, :created)"
            ), {
                "id": srid, "res_id": resident_ids[res_idx],
                "cat": cat, "subj": subject, "desc": desc, "loc": loc,
                "pri": priority, "status": sr_status, "notes": resolution,
                "submitted": submitted, "resolved": resolved_at, "created": submitted,
            })

        # ANNOUNCEMENTS - 6 active announcements
        announcement_data = [
            ("Water Supply Interruption - May 20", "Scheduled water maintenance from 10:00 AM to 2:00 PM on May 20. Please store enough water for the duration. We apologize for the inconvenience.", "maintenance", "important", datetime(2026, 5, 17, 8, 0)),
            ("Monthly Fire Drill - May 25 at 10:00 AM", "All residents are required to participate in the monthly fire drill. Please proceed to your designated assembly area when the alarm sounds.", "event", "normal", datetime(2026, 5, 15, 9, 0)),
            ("New WiFi Password Effective June 1", "The WiFi password for all buildings will be changed on June 1. New credentials will be sent via email. Please update your devices accordingly.", "general", "normal", datetime(2026, 5, 13, 10, 0)),
            ("Elevator Maintenance Schedule", "Tower A elevator will undergo maintenance on May 22-23. Please use the stairs during this period. Tower B and C elevators will remain operational.", "maintenance", "normal", datetime(2026, 5, 11, 14, 0)),
            ("Rent Payment Reminder: Due by May 30", "This is a friendly reminder that rent payments for May 2026 are due by May 30. Please settle your bills to avoid late fees. You can pay via GCash, Maya, or bank transfer.", "billing", "important", datetime(2026, 5, 16, 8, 0)),
            ("Welcome Summer Residents!", "We welcome all new summer residents to DormTel. Orientation will be held on June 5 at 2:00 PM in the Tower A common area. Light refreshments will be served.", "event", "normal", datetime(2026, 5, 14, 12, 0)),
        ]

        for title, content, cat, priority, published in announcement_data:
            aid = str(uuid.uuid4())
            await session.execute(text(
                "INSERT INTO announcements (id, title, content, category, priority, is_active, published_at, created_at) VALUES (:id, :title, :content, :cat, :pri, :active, :published, :created)"
            ), {
                "id": aid, "title": title, "content": content,
                "cat": cat, "pri": priority, "active": True,
                "published": published, "created": published,
            })

        await session.commit()
        print("SEED COMPLETE!")
        print(f"  Rooms: {len(rooms)}")
        print(f"  Residents: {len(resident_data)}")
        print(f"  Inquiries: {len(inquiry_data)}")
        print(f"  Billings: {len(billing_ids)} + {len(hist_billing_data)} historical")
        print(f"  Payments: {len(payment_data)} + {len(hist_payment_data)} historical")
        print(f"  Move-outs: {len(moveout_data)}")
        print(f"  Meter readings: {len(meter_data)}")
        print(f"  Service requests: {len(service_request_data)}")
        print(f"  Announcements: {len(announcement_data)}")

asyncio.run(seed())
