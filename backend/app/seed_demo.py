"""
Dormtel Comprehensive Demo Seed
Generates realistic demo data for stakeholder presentations.
Run inside API container: python -m app.seed_demo
"""

import asyncio
import uuid
from datetime import datetime, date, timedelta
from decimal import Decimal

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import sessionmaker

from app.database import engine, Base
from app.auth import get_password_hash
from app.models import (
    Room, Bed, Resident, Inquiry, Billing, Payment, MoveOut,
    Faq, Announcement, MeterReading, ServiceRequest, Staff, Checkpoint, LedgerEntry
)


# ─────────────────────────────────────────────
# DEMO DATA
# ─────────────────────────────────────────────

# (room_number, property_code, building, capacity)
ROOMS_DATA = [
    ("101", "DT01", "Tower A", 2),
    ("102", "DT01", "Tower A", 4),
    ("103", "DT01", "Tower A", 4),
    ("104", "DT01", "Tower A", 6),
    ("105", "DT01", "Tower A", 6),
    ("106", "DT01", "Tower A", 8),
    ("107", "DT01", "Tower A", 8),
    ("108", "DT01", "Tower A", 8),
    ("109", "DT01", "Tower A", 10),
    ("110", "DT01", "Tower A", 10),
    ("201", "DT01", "Tower B", 4),
    ("202", "DT01", "Tower B", 4),
    ("203", "DT01", "Tower B", 6),
    ("204", "DT01", "Tower B", 2),
    ("301", "DT02", "Tower C", 2),
    ("302", "DT02", "Tower C", 4),
    ("303", "DT02", "Tower C", 4),
    ("304", "DT02", "Tower C", 6),
    ("305", "DT02", "Tower C", 6),
    ("306", "DT02", "Tower C", 8),
    ("307", "DT02", "Tower C", 8),
    ("308", "DT02", "Tower C", 2),
    ("309", "DT02", "Tower C", 4),
]

# Bed definitions per room: (room_index, bed_number, bed_type, rate_per_bed, status)
BEDS_DATA = [
    # 101 - 2 beds (loft)
    (0, 1, "loft_type", 6500, "occupied"),
    (0, 2, "loft_type", 6500, "available"),
    # 102 - 4 beds (lower/upper)
    (1, 1, "lower_bunk", 5500, "occupied"),
    (1, 2, "lower_bunk", 5500, "occupied"),
    (1, 3, "upper_bunk", 5300, "available"),
    (1, 4, "upper_bunk", 5300, "available"),
    # 103 - 4 beds
    (2, 1, "upper_bunk", 5300, "occupied"),
    (2, 2, "upper_bunk", 5300, "available"),
    (2, 3, "lower_bunk", 5500, "available"),
    (2, 4, "lower_bunk", 5500, "available"),
    # 104 - 6 beds (loft)
    (3, 1, "loft_type", 4500, "occupied"),
    (3, 2, "loft_type", 4500, "available"),
    (3, 3, "loft_type", 4500, "available"),
    (3, 4, "loft_type", 4500, "available"),
    (3, 5, "loft_type", 4500, "available"),
    (3, 6, "loft_type", 4500, "available"),
    # 105 - 6 beds (full)
    (4, 1, "loft_type", 4500, "occupied"),
    (4, 2, "loft_type", 4500, "occupied"),
    (4, 3, "loft_type", 4500, "occupied"),
    (4, 4, "loft_type", 4500, "occupied"),
    (4, 5, "loft_type", 4500, "occupied"),
    (4, 6, "loft_type", 4500, "occupied"),
    # 106 - 8 beds (lower/upper/loft)
    (5, 1, "lower_bunk", 4000, "occupied"),
    (5, 2, "lower_bunk", 4000, "occupied"),
    (5, 3, "lower_bunk", 4000, "occupied"),
    (5, 4, "lower_bunk", 4000, "available"),
    (5, 5, "upper_bunk", 3800, "occupied"),
    (5, 6, "upper_bunk", 3800, "available"),
    (5, 7, "loft_type", 4100, "available"),
    (5, 8, "loft_type", 4100, "available"),
    # 107 - 8 beds
    (6, 1, "upper_bunk", 3800, "occupied"),
    (6, 2, "upper_bunk", 3800, "occupied"),
    (6, 3, "upper_bunk", 3800, "available"),
    (6, 4, "upper_bunk", 3800, "available"),
    (6, 5, "lower_bunk", 4000, "available"),
    (6, 6, "lower_bunk", 4000, "available"),
    (6, 7, "loft_type", 4100, "available"),
    (6, 8, "loft_type", 4100, "available"),
    # 108 - 8 beds
    (7, 1, "loft_type", 4100, "occupied"),
    (7, 2, "loft_type", 4100, "available"),
    (7, 3, "loft_type", 4100, "available"),
    (7, 4, "loft_type", 4100, "available"),
    (7, 5, "lower_bunk", 4000, "available"),
    (7, 6, "lower_bunk", 4000, "available"),
    (7, 7, "upper_bunk", 3800, "available"),
    (7, 8, "upper_bunk", 3800, "available"),
    # 109 - 10 beds
    (8, 1, "lower_bunk", 3600, "occupied"),
    (8, 2, "lower_bunk", 3600, "occupied"),
    (8, 3, "lower_bunk", 3600, "occupied"),
    (8, 4, "lower_bunk", 3600, "occupied"),
    (8, 5, "lower_bunk", 3600, "available"),
    (8, 6, "lower_bunk", 3600, "available"),
    (8, 7, "upper_bunk", 3500, "occupied"),
    (8, 8, "upper_bunk", 3500, "occupied"),
    (8, 9, "upper_bunk", 3500, "available"),
    (8, 10, "upper_bunk", 3500, "available"),
    # 110 - 10 beds (full)
    (9, 1, "lower_bunk", 3600, "occupied"),
    (9, 2, "lower_bunk", 3600, "occupied"),
    (9, 3, "lower_bunk", 3600, "occupied"),
    (9, 4, "lower_bunk", 3600, "occupied"),
    (9, 5, "lower_bunk", 3600, "occupied"),
    (9, 6, "upper_bunk", 3500, "occupied"),
    (9, 7, "upper_bunk", 3500, "occupied"),
    (9, 8, "upper_bunk", 3500, "occupied"),
    (9, 9, "upper_bunk", 3500, "occupied"),
    (9, 10, "upper_bunk", 3500, "occupied"),
    # 201 - 4 beds (full)
    (10, 1, "lower_bunk", 5500, "occupied"),
    (10, 2, "lower_bunk", 5500, "occupied"),
    (10, 3, "upper_bunk", 5300, "occupied"),
    (10, 4, "upper_bunk", 5300, "occupied"),
    # 202 - 4 beds
    (11, 1, "upper_bunk", 5300, "occupied"),
    (11, 2, "upper_bunk", 5300, "occupied"),
    (11, 3, "lower_bunk", 5500, "available"),
    (11, 4, "lower_bunk", 5500, "available"),
    # 203 - 6 beds
    (12, 1, "loft_type", 4500, "occupied"),
    (12, 2, "loft_type", 4500, "occupied"),
    (12, 3, "loft_type", 4500, "available"),
    (12, 4, "loft_type", 4500, "available"),
    (12, 5, "loft_type", 4500, "available"),
    (12, 6, "loft_type", 4500, "available"),
    # 204 - 2 beds
    (13, 1, "loft_type", 6500, "available"),
    (13, 2, "loft_type", 6500, "available"),
    # 301 - 2 beds (full)
    (14, 1, "loft_type", 6000, "occupied"),
    (14, 2, "loft_type", 6000, "occupied"),
    # 302 - 4 beds
    (15, 1, "lower_bunk", 5400, "occupied"),
    (15, 2, "lower_bunk", 5400, "occupied"),
    (15, 3, "lower_bunk", 5400, "available"),
    (15, 4, "upper_bunk", 5200, "available"),
    # 303 - 4 beds
    (16, 1, "upper_bunk", 5200, "occupied"),
    (16, 2, "upper_bunk", 5200, "available"),
    (16, 3, "lower_bunk", 5400, "available"),
    (16, 4, "lower_bunk", 5400, "available"),
    # 304 - 6 beds
    (17, 1, "loft_type", 4300, "occupied"),
    (17, 2, "loft_type", 4300, "occupied"),
    (17, 3, "loft_type", 4300, "available"),
    (17, 4, "loft_type", 4300, "available"),
    (17, 5, "loft_type", 4300, "available"),
    (17, 6, "loft_type", 4300, "available"),
    # 305 - 6 beds (full)
    (18, 1, "loft_type", 4300, "occupied"),
    (18, 2, "loft_type", 4300, "occupied"),
    (18, 3, "loft_type", 4300, "occupied"),
    (18, 4, "loft_type", 4300, "occupied"),
    (18, 5, "loft_type", 4300, "occupied"),
    (18, 6, "loft_type", 4300, "occupied"),
    # 306 - 8 beds
    (19, 1, "loft_type", 4100, "occupied"),
    (19, 2, "loft_type", 4100, "occupied"),
    (19, 3, "loft_type", 4100, "occupied"),
    (19, 4, "loft_type", 4100, "available"),
    (19, 5, "loft_type", 4100, "available"),
    (19, 6, "loft_type", 4100, "available"),
    (19, 7, "loft_type", 4100, "available"),
    (19, 8, "loft_type", 4100, "available"),
    # 307 - 8 beds
    (20, 1, "loft_type", 4100, "occupied"),
    (20, 2, "loft_type", 4100, "occupied"),
    (20, 3, "loft_type", 4100, "occupied"),
    (20, 4, "loft_type", 4100, "available"),
    (20, 5, "loft_type", 4100, "available"),
    (20, 6, "loft_type", 4100, "available"),
    (20, 7, "loft_type", 4100, "available"),
    (20, 8, "loft_type", 4100, "available"),
    # 308 - 2 beds
    (21, 1, "loft_type", 6000, "available"),
    (21, 2, "loft_type", 6000, "available"),
    # 309 - 4 beds
    (22, 1, "lower_bunk", 5400, "occupied"),
    (22, 2, "lower_bunk", 5400, "available"),
    (22, 3, "upper_bunk", 5200, "available"),
    (22, 4, "upper_bunk", 5200, "available"),
]

STAFF_DATA = [
    ("Super Admin", "onipace@gmail.com", "manager", "09171234567", "IamDORMTEL-2026#"),
    ("Juan Reyes", "juan@dormtel.ph", "admin", "09171234568", None),
    ("Ana dela Cruz", "ana@dormtel.ph", "dm", "09171234569", None),
]

# (name, email, phone, status, bed_idx, rate, move_in, move_out, school, course, review_center, exam_date, is_first)
RESIDENTS_DATA = [
    ("Juan dela Cruz", "juan.delacruz@email.com", "09171111001", "active", 0, 6500, date(2025, 6, 1), None, "UE Manila", "Nursing", None, None, True),
    ("Ana Marie Reyes", "ana.reyes@email.com", "09171111002", "active", 2, 5500, date(2025, 6, 15), None, "PUP", "Engineering", None, None, True),
    ("Carlo Miguel Santos", "carlo.santos@email.com", "09171111003", "active", 3, 5500, date(2025, 7, 1), None, "UST", "Architecture", None, None, False),
    ("Patricia Mae Garcia", "patricia.garcia@email.com", "09171111004", "active", 8, 5300, date(2025, 7, 15), None, "UE", "Business", None, None, True),
    ("Jose Rizal Jr.", "jose.rizal@email.com", "09171111005", "active", 16, 4500, date(2025, 8, 1), None, "PUP", "Education", "CBRC", date(2026, 6, 1), True),
    ("Maria Clara Bautista", "maria.clara@email.com", "09171111006", "active", 22, 4500, date(2025, 8, 15), None, "UST", "Medicine", None, None, True),
    ("Andrew James Tan", "andrew.tan@email.com", "09171111007", "active", 32, 4000, date(2025, 9, 1), None, "FEU", "IT", None, None, False),
    ("Sofia Isabel Cruz", "sofia.cruz@email.com", "09171111008", "active", 40, 3800, date(2025, 9, 15), None, "UE", "Psychology", None, None, True),
    ("Miguel Angelo Ramos", "miguel.ramos@email.com", "09171111009", "active", 48, 4100, date(2025, 10, 1), None, "PUP", "Engineering", None, None, True),
    ("Bianca Joy Mendoza", "bianca.mendoza@email.com", "09171111010", "active", 56, 3600, date(2025, 10, 15), None, "UST", "Nursing", "SRG", date(2026, 5, 15), True),
    ("Gabriel Lim", "gabriel.lim@email.com", "09171111011", "active", 64, 3500, date(2025, 11, 1), None, "FEU", "Business", None, None, False),
    ("Isabelle Rose Torres", "isabelle.torres@email.com", "09171111012", "active", 70, 6000, date(2025, 11, 15), None, "UE", "Architecture", None, None, True),
    ("Rafael Martin Aquino", "rafael.aquino@email.com", "09171111013", "active", 76, 5400, date(2025, 12, 1), None, "PUP", "IT", "CBRC", date(2026, 7, 1), True),
    ("Camille Anne Villanueva", "camille.villanueva@email.com", "09171111014", "active", 80, 5200, date(2025, 12, 15), None, "UST", "Education", None, None, True),
    ("Daniel Patrick Ong", "daniel.ong@email.com", "09171111015", "active", 86, 4300, date(2026, 1, 1), None, "FEU", "Psychology", None, None, True),
    ("Katherine May Sy", "katherine.sy@email.com", "09171111016", "reserved", 88, 4300, None, None, "UE", "Nursing", None, None, True),
    ("Mark Joseph Rivera", "mark.rivera@email.com", "09171111017", "reserved", 96, 4100, None, None, "PUP", "Engineering", "SRG", date(2026, 6, 1), False),
    ("Nicole Anne Chua", "nicole.chua@email.com", "09171111018", "moved_out", 4, 4500, date(2025, 3, 1), date(2026, 3, 31), "UST", "Business", None, None, True),
    ("Jerome Kyle Lee", "jerome.lee@email.com", "09171111019", "moved_out", 9, 5300, date(2025, 4, 1), date(2026, 4, 30), "FEU", "IT", None, None, True),
]

INQUIRIES_DATA = [
    ("facebook", "Hi! I saw your ad. How much is a bed space in Tower A?", "new", 0.85, 78, "Juan Cruz", "09171111001", "juan@email.com", "UE", "Nursing", None, None, True, None, date(2026, 6, 1), "1_year"),
    ("instagram", "Is there available room for 2 students near UST? Move in June.", "new", 0.90, 85, "Ana Reyes", "09171111002", "ana@email.com", "UST", "Engineering", None, None, True, None, date(2026, 6, 1), "1_year"),
    ("tiktok", "Saw your TikTok tour video! Do you accept short-term stays?", "new", 0.72, 60, "Carlo Santos", "09171111003", "carlo@email.com", "PUP", "Architecture", None, None, False, "DormZone", date(2026, 5, 30), "3_months"),
    ("walkin", "Walk-in inquiry about Tower C premium rooms. Very interested.", "responded", 0.95, 92, "Pat Garcia", "09171111004", "pat@email.com", "UE", "Business", None, None, True, None, date(2026, 6, 1), "1_year"),
    ("facebook", "How do I reserve a bed? Can I pay via GCash?", "responded", 0.88, 80, "Jose Rizal", "09171111005", "jose@email.com", "PUP", "Education", "CBRC", date(2026, 6, 1), True, None, date(2026, 6, 1), "indefinite"),
    ("phone", "Parent calling to inquire about safety features and visiting hours.", "responded", 0.82, 75, "Maria Bautista", "09171111006", "maria@email.com", "UST", "Medicine", None, None, True, None, date(2026, 7, 1), "1_year"),
    ("instagram", "Looking for a room near my workplace. Budget is 7k.", "escalated", 0.65, 55, "Andrew Tan", "09171111007", "andrew@email.com", "FEU", "IT", None, None, False, "CityDorm", date(2026, 6, 1), "6_months"),
    ("walkin", "Group of 3 friends looking for beds in same room. Tower B preferred.", "new", 0.92, 88, "Sofia Cruz", "09171111008", "sofia@email.com", "UE", "Psychology", None, None, True, None, date(2026, 6, 1), "1_year"),
    ("referral", "My friend recommended DormTel. Is there parking for motorcycles?", "converted", 0.78, 70, "Miguel Ramos", "09171111009", "miguel@email.com", "PUP", "Engineering", None, None, True, None, date(2026, 5, 20), "1_year"),
    ("tiktok", "Love the amenities! When is the next available slot?", "new", 0.88, 82, "Bianca Mendoza", "09171111010", "bianca@email.com", "UST", "Nursing", "SRG", date(2026, 5, 15), True, None, date(2026, 6, 1), "indefinite"),
    ("website", "Asking about refund policy if I move out early.", "closed", 0.30, 20, "Gabriel Lim", "09171111011", "gabriel@email.com", "FEU", "Business", None, None, False, "OldDorm", date(2026, 5, 15), "3_months"),
    ("walkin", "Student transferee from province. Needs bed ASAP.", "new", 0.95, 90, "Isabelle Torres", "09171111012", "isabelle@email.com", "UE", "Architecture", None, None, True, None, date(2026, 5, 25), "1_year"),
    ("facebook", "Do you have aircon in all rooms? What about WiFi speed?", "new", 0.80, 72, "Rafael Aquino", "09171111013", "rafael@email.com", "PUP", "IT", "CBRC", date(2026, 7, 1), True, None, date(2026, 6, 1), "indefinite"),
    ("phone", "Company-sponsored dormer. Need official receipt for reimbursement.", "responded", 0.75, 68, "Camille Villanueva", "09171111014", "camille@email.com", "UST", "Education", None, None, True, None, date(2026, 6, 1), "1_year"),
    ("referral", "Reviewee looking for quiet study environment near review center.", "new", 0.93, 87, "Daniel Ong", "09171111015", "daniel@email.com", "FEU", "Psychology", None, None, True, None, date(2026, 6, 1), "6_months"),
]

BILLING_STATUSES = ["approved", "distributed", "distributed", "pending_review", "pending_review",
                    "distributed", "approved", "distributed", "paid", "paid",
                    "distributed", "pending_review", "distributed", "distributed", "pending_review"]

PAYMENT_DATA = [
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

MOVEOUT_DATA = [
    (7, date(2026, 6, 1), "Graduating and moving back to province", "09189990001", "requested"),
    (9, date(2026, 5, 30), "Transferring to another dormitory closer to work", "09189990002", "clearance"),
    (4, date(2026, 6, 15), "End of internship period", "09189990003", "requested"),
    (14, date(2026, 7, 1), "Family moving to a condo nearby", "09189990004", "refund_pending"),
]

FAQ_DATA = [
    ("What types of rooms are available?", "For Recto we have rooms for 2, 4, 6, 8 & 10.\nFor Sta. Mesa we have rooms for 2, 4, 6, & 8.", "rooms", 1),
    ("How much is the monthly rent?", "FOR RECTO BRANCH\nRoom for 2 (Loft Type): PHP 6,500\nRoom for 4 (Lower Bunk): PHP 5,500 | (Upper Bunk): PHP 5,300\nRoom for 6 (Loft Type): PHP 4,500\nRoom for 8 (Lower Bunk): PHP 4,000 | (Upper Bunk): PHP 3,800 | (Loft Type): PHP 4,100\nRoom for 10 (Lower Bunk): PHP 3,600 | (Upper Bunk): PHP 3,500\n\nFOR STA. MESA BRANCH\nRoom for 2 (Loft Type): PHP 6,000\nRoom for 4 (Lower Bunk): PHP 5,400 | (Upper Bunk): PHP 5,200\nRoom for 6 (Loft Type): PHP 4,300\nRoom for 8 (Loft Type): PHP 4,100", "rooms", 2),
    ("Are utilities included in the rent?", "Utilities are excluded from the rent.\n\nFor electricity, charges will be based on your actual consumption at a rate of PHP 14.56 per kWh, with a sub-meter provided.\n\nFor water, the charge will be based on the monthly cubic meter (cu.m) rate.", "utilities", 1),
    ("Is there a minimum stay requirement?", "Yes, 1 month.", "policies", 1),
    ("Is the dormitory exclusive for male or female tenants?", "The dorm accepts both male and female tenants, with rooms segregated by gender. Mixed-gender room arrangements are also allowed, provided that each dormer submits a parental consent form.", "policies", 2),
    ("How many occupants are allowed per room?", "For Recto we have rooms for 2, 4, 6, 8 & 10.\nFor Sta. Mesa we have rooms for 2, 4, 6 & 8.", "rooms", 3),
    ("Is the dormitory open to students only?", "No. We also accept reviewees, working professionals, backpackers & travellers.", "policies", 3),
    ("How can I reserve a room?", "You may walk in at the admin office & pay cash or pay via online payment. Admin to provide bank details.", "rooms", 4),
    ("Is there a reservation fee or security deposit?", "Yes, we collect the following:\n1 month advance, 1 month security deposit. Utility deposit & pro-rate rental if needed.", "payments", 1),
    ("What payment methods are accepted?", "Cash payment or bank transfer.", "payments", 2),
    ("When is the monthly due date for rent?", "Every 5th of the month.", "payments", 3),
    ("Are late payment penalties applied?", "Yes, 5% penalty shall be applied for late payments.", "payments", 4),
    ("Is the deposit refundable?", "Yes, security deposit is refundable after deductions of consumed water & electricity on the last month of stay.", "payments", 5),
    ("Is Wi-Fi available?", "Yes, free Wi-Fi at the lobby area.", "amenities", 1),
    ("Are rooms fully furnished?", "No, the dorm is a bare unit but provides mattress for bed.", "amenities", 2),
    ("Is air conditioning included?", "Air-conditioned rooms are included (window/Split type).", "amenities", 3),
    ("Is there a study area or lounge?", "Yes, at the lobby area we provide tables & chairs for dormers.", "amenities", 4),
    ("Are cooking and laundry allowed?", "Yes, we have tie-up laundry shops & dormers can also do DIY laundry. Cooking using rice cooker is currently allowed.", "amenities", 5),
    ("Is parking available for tenants?", "For Recto Branch, none. Street parking provided by the cityhall only and with pay.\nFor Sta. Mesa, we have motorcycle parking at PHP 1,500 monthly & PHP 2,500 for small cars.", "amenities", 6),
    ("Are visitors allowed inside the dormitory?", "Visitors are allowed at the lobby.", "policies", 4),
    ("What are the dormitory curfew hours?", "Visitors are only permitted in the lobby area from 8:00 AM to 8:00 PM.", "policies", 5),
    ("Are pets allowed?", "Pets are not allowed.", "policies", 6),
    ("Is smoking or drinking prohibited?", "Smoking & drinking inside the dorm premises are not allowed.", "policies", 7),
    ("What happens if a tenant violates dormitory rules?", "Guidelines are provided to all tenants upon move-in, including the rules, regulations, and corresponding penalties.", "policies", 8),
    ("Can tenants transfer to another room?", "Tenants are not allowed on room hopping. Room transfers shall be done with admin's assistance.", "policies", 9),
    ("Is the dormitory secured 24/7?", "We have CCTV Monitors 24/7, admin on duty from 8am to 5pm. Housekeeping from 11am to 8pm & Security Guard on duty from 8pm to 8am.", "safety", 1),
    ("Are CCTV cameras installed?", "Yes, we have CCTV monitors inside the dorm.", "safety", 2),
    ("Is there a guard or staff on duty?", "Yes, from 8pm to 8am.", "safety", 3),
    ("What should tenants do during emergencies?", "We have emergency hotline numbers posted at the back of each room door that tenants can call during emergencies. They may also immediately inform the admin or other staff members for a faster response. Additionally, all dormers are given a tour of the building during move-in, including the location of the fire exits and emergency escape routes.", "safety", 4),
    ("How do I report maintenance issues?", "Dormers may personally visit the admin office to report concerns, or they may contact the admin through text message, Viber, or the Facebook page. During move-in, tenants are also provided with the admin's contact details for easier communication regarding any concerns or inquiries.", "amenities", 7),
    ("How long does maintenance usually take?", "Maintenance response time depends on the type of concern. Minor repairs, such as faucet issues or clogged sinks, are usually resolved within a few hours, while major repairs, including air conditioning concerns, may take more than two days depending on the issue and parts availability. Rest assured that our team always exerts its best efforts to address and resolve maintenance concerns as quickly as possible.", "amenities", 8),
    ("What documents are required before moving in?", "1 copy of 2x2 photos, 2 valid IDs.", "moveout", 1),
    ("What items should tenants bring?", "Own pillow, bed cover, blanket & personal items. Appliances such as electric fan, rice cooker & kettle are allowed.", "amenities", 9),
    ("What is the move-out process?", "The dormer shall need to secure move-out clearance, where they will be able to know whether they will be getting a refund or have to pay additional amount for the last month's consumption.", "moveout", 2),
    ("How long does it take to receive the deposit refund after move-out?", "Refund will be processed within 60 working days upon move-out.", "moveout", 3),
    ("Can tenants check billing statements online?", "Billing statement will be sent to dormers' provided email.", "payments", 6),
    ("Is there an online announcement or notification system?", "Currently we post on walls near elevators for dormers to see.", "amenities", 10),
]

ANNOUNCEMENT_DATA = [
    ("Water Supply Interruption - May 20", "Scheduled water maintenance from 10:00 AM to 2:00 PM on May 20. Please store enough water for the duration. We apologize for the inconvenience.", "maintenance", "important"),
    ("Monthly Fire Drill - May 25 at 10:00 AM", "All residents are required to participate in the monthly fire drill. Please proceed to your designated assembly area when the alarm sounds.", "event", "normal"),
    ("New WiFi Password Effective June 1", "The WiFi password for all buildings will be changed on June 1. New credentials will be sent via email. Please update your devices accordingly.", "general", "normal"),
    ("Elevator Maintenance Schedule", "Tower A elevator will undergo maintenance on May 22-23. Please use the stairs during this period. Tower B and C elevators will remain operational.", "maintenance", "normal"),
    ("Rent Payment Reminder: Due by May 30", "This is a friendly reminder that rent payments for May 2026 are due by May 30. Please settle your bills to avoid late fees. You can pay via GCash, Maya, or bank transfer.", "billing", "important"),
    ("Welcome Summer Residents!", "We welcome all new summer residents to DormTel. Orientation will be held on June 5 at 2:00 PM in the Tower A common area. Light refreshments will be served.", "event", "normal"),
]

METER_READING_DATA = [
    ("Tower A", date(2026, 5, 1), Decimal("4520.50"), Decimal("1280.30")),
    ("Tower B", date(2026, 5, 1), Decimal("3890.75"), Decimal("1050.20")),
    ("Tower C", date(2026, 5, 1), Decimal("2150.25"), Decimal("680.10")),
    ("Tower A", date(2026, 4, 1), Decimal("4180.20"), Decimal("1190.50")),
    ("Tower B", date(2026, 4, 1), Decimal("3620.40"), Decimal("980.80")),
    ("Tower C", date(2026, 4, 1), Decimal("1980.60"), Decimal("620.30")),
    ("Tower A", date(2026, 3, 1), Decimal("3850.10"), Decimal("1105.40")),
    ("Tower B", date(2026, 3, 1), Decimal("3340.20"), Decimal("905.60")),
]

SERVICE_REQUEST_DATA = [
    (0, "aircon", "Aircon not cooling properly", "Unit blows warm air even at lowest temperature setting. Started 2 days ago.", "Room 101", "high", "resolved", datetime(2026, 5, 13, 8, 0), "Replaced aircon filter and recharged refrigerant. Unit tested and confirmed working."),
    (0, "plumbing", "Bathroom faucet leaking", "The faucet in the bathroom drips continuously even when fully closed.", "Room 101, bathroom", "medium", "in_progress", datetime(2026, 5, 16, 14, 30), None),
    (1, "wifi", "WiFi connection keeps dropping", "Internet connection drops every 30 minutes. Need to reconnect manually each time.", "Room 102", "high", "acknowledged", datetime(2026, 5, 17, 9, 0), None),
    (2, "electrical", "Power outlet not working near desk", "The outlet closest to my study desk stopped working yesterday.", "Room 103, near window", "medium", "submitted", datetime(2026, 5, 18, 6, 0), None),
    (3, "pest_control", "Cockroach sighting in kitchen area", "Found several cockroaches in the shared kitchen area during evening.", "Tower A, shared kitchen", "high", "resolved", datetime(2026, 5, 11, 20, 0), "Pest control treatment applied to kitchen and surrounding areas. Follow-up scheduled in 2 weeks."),
    (4, "lock_key", "Room door lock is stiff", "Room door lock is very hard to turn. Key gets stuck sometimes.", "Room 104", "medium", "in_progress", datetime(2026, 5, 14, 11, 0), None),
    (5, "water_supply", "Low water pressure in shower", "Water pressure has been very low since last week. Takes long to shower.", "Room 105, bathroom", "medium", "submitted", datetime(2026, 5, 18, 7, 30), None),
    (6, "aircon", "Aircon making loud noise", "The aircon unit makes a rattling noise when set to high fan speed.", "Room 106", "low", "acknowledged", datetime(2026, 5, 17, 15, 0), None),
    (7, "cleaning", "Common area bathroom needs deep cleaning", "The shared bathroom on 2nd floor needs thorough cleaning. Tiles are stained.", "Tower A, 2F bathroom", "medium", "resolved", datetime(2026, 5, 8, 10, 0), "Deep cleaning completed. Tiles scrubbed and sanitized. Will schedule regular weekly deep clean."),
    (8, "appliance", "Shared refrigerator not cooling", "The refrigerator in the common pantry is not maintaining cold temperature.", "Tower B, common pantry", "high", "in_progress", datetime(2026, 5, 15, 16, 0), None),
]


async def clear_existing(session: AsyncSession):
    """Clear all existing data in dependency order."""
    print("Clearing existing data...")
    await session.execute(text("DELETE FROM checkpoints"))
    await session.execute(text("DELETE FROM service_requests"))
    await session.execute(text("DELETE FROM announcements"))
    await session.execute(text("DELETE FROM faqs"))
    await session.execute(text("DELETE FROM move_outs"))
    await session.execute(text("DELETE FROM ledger_entries"))
    await session.execute(text("DELETE FROM payments"))
    await session.execute(text("DELETE FROM billings"))
    await session.execute(text("DELETE FROM inquiries"))
    await session.execute(text("DELETE FROM residents"))
    await session.execute(text("DELETE FROM beds"))
    await session.execute(text("DELETE FROM rooms"))
    await session.execute(text("DELETE FROM staff"))
    await session.execute(text("DELETE FROM meter_readings"))
    await session.commit()
    print("Cleared.")


async def seed_all():
    async with sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)() as session:
        await clear_existing(session)

        # ── STAFF ──
        staff_objs = []
        for name, email, role, phone, password in STAFF_DATA:
            s = Staff(
                id=uuid.uuid4(),
                full_name=name,
                email=email,
                role=role,
                phone=phone,
                password_hash=get_password_hash(password) if password else None,
                is_active=True,
                is_verified=True,
                email_verified_at=datetime.utcnow() if password else None,
            )
            session.add(s)
            staff_objs.append(s)
        await session.commit()
        print(f"Seeded {len(staff_objs)} staff.")

        # ── ROOMS ──
        room_objs = []
        for num, prop, bldg, cap in ROOMS_DATA:
            # Determine room status based on whether any beds will be available
            r = Room(
                id=uuid.uuid4(),
                room_number=num,
                display_room_number=f"{prop}-{num}",
                property_code=prop,
                building=bldg,
                capacity=cap,
                status="available",
            )
            session.add(r)
            room_objs.append(r)
        await session.commit()
        print(f"Seeded {len(room_objs)} rooms.")

        # ── BEDS ──
        bed_objs = []
        for room_idx, bed_num, btype, rate, status in BEDS_DATA:
            room = room_objs[room_idx]
            bed_letter = chr(64 + bed_num)  # 1->A, 2->B, etc.
            b = Bed(
                id=uuid.uuid4(),
                bed_code=f"{room.room_number}{bed_letter}",
                room_id=room.id,
                bed_number=bed_num,
                bed_type=btype,
                rate_per_bed=Decimal(str(rate)),
                status=status,
            )
            session.add(b)
            bed_objs.append(b)
        await session.commit()
        print(f"Seeded {len(bed_objs)} beds.")

        # Update room statuses based on bed availability
        for room in room_objs:
            room_beds = [b for b in bed_objs if b.room_id == room.id]
            available_count = sum(1 for b in room_beds if b.status == "available")
            if available_count == 0:
                room.status = "full"
        await session.commit()

        # ── RESIDENTS ──
        resident_objs = []
        for name, email, phone, status, bed_idx, rate, move_in, move_out, school, course, review_center, exam_date, is_first in RESIDENTS_DATA:
            r = Resident(
                id=uuid.uuid4(),
                full_name=name,
                email=email,
                phone=phone,
                status=status,
                bed_id=bed_objs[bed_idx].id if bed_idx is not None else None,
                monthly_rate=Decimal(str(rate)),
                move_in_date=move_in,
                move_out_date=move_out,
                school=school,
                course=course,
                review_center=review_center,
                exam_date=exam_date,
                is_first_time_dormer=is_first,
                id_type="national_id",
                id_number=f"PSN-{1000+len(resident_objs)}",
                created_at=datetime.utcnow(),
            )
            session.add(r)
            resident_objs.append(r)
        await session.commit()
        print(f"Seeded {len(resident_objs)} residents.")

        # ── INQUIRIES ──
        inquiry_objs = []
        for i, (source, content, status, sentiment, lead, pname, pphone, pemail, school, course, review_center, exam_date, first_time, prev_dorm, move_in_date, length) in enumerate(INQUIRIES_DATA):
            inquiry = Inquiry(
                id=uuid.uuid4(),
                source=source,
                content=content,
                status=status,
                sentiment_score=Decimal(str(sentiment)),
                lead_score=lead,
                property_code="DT01" if i % 2 == 0 else "DT02",
                prospect_name=pname,
                prospect_phone=pphone,
                prospect_email=pemail,
                school=school,
                course=course,
                review_center=review_center,
                exam_date=exam_date,
                first_time_dormer=first_time,
                previous_dorm=prev_dorm,
                desired_move_in_date=move_in_date,
                length_of_stay=length,
                created_at=datetime(2026, 5, 10) + timedelta(hours=i*6),
            )
            session.add(inquiry)
            inquiry_objs.append(inquiry)
        await session.commit()
        print(f"Seeded {len(inquiry_objs)} inquiries.")

        # ── BILLINGS ──
        billing_objs = []
        for i in range(min(15, len(resident_objs))):
            rate = RESIDENTS_DATA[i][5]
            electric = round(350 + (i * 45), 2)
            water = round(150 + (i * 20), 2)
            total = rate + electric + water
            b = Billing(
                id=uuid.uuid4(),
                resident_id=resident_objs[i].id,
                billing_period="2026-05",
                rent_amount=Decimal(str(rate)),
                electric_charge=Decimal(str(electric)),
                water_charge=Decimal(str(water)),
                other_charges=Decimal("0"),
                previous_balance=Decimal("0"),
                total_amount=Decimal(str(total)),
                status=BILLING_STATUSES[i],
                created_at=datetime(2026, 5, 1, 8, 0) + timedelta(hours=i),
            )
            session.add(b)
            billing_objs.append(b)
        await session.commit()
        print(f"Seeded {len(billing_objs)} billings.")

        # ── PAYMENTS ──
        payment_objs = []
        for res_idx, amount, method, status, ref in PAYMENT_DATA:
            p = Payment(
                id=uuid.uuid4(),
                resident_id=resident_objs[res_idx].id,
                amount=Decimal(str(amount)),
                method=method,
                status=status,
                gateway_ref=ref,
                created_at=datetime(2026, 5, 15, 9, 0) + timedelta(hours=res_idx * 2),
            )
            session.add(p)
            payment_objs.append(p)
        await session.commit()
        print(f"Seeded {len(payment_objs)} payments.")

        # ── MOVE-OUTS ──
        moveout_objs = []
        for res_idx, req_date, reason, contact, status in MOVEOUT_DATA:
            m = MoveOut(
                id=uuid.uuid4(),
                resident_id=resident_objs[res_idx].id,
                requested_date=req_date,
                reason=reason,
                forwarding_contact=contact,
                status=status,
                created_at=datetime(2026, 5, 14, 10, 0),
            )
            session.add(m)
            moveout_objs.append(m)
        await session.commit()
        print(f"Seeded {len(moveout_objs)} move-outs.")

        # ── FAQS ──
        faq_objs = []
        for question, answer, category, order in FAQ_DATA:
            f = Faq(
                id=uuid.uuid4(),
                question=question,
                answer=answer,
                category=category,
                order_index=order,
                is_active=True,
                created_at=datetime.utcnow(),
            )
            session.add(f)
            faq_objs.append(f)
        await session.commit()
        print(f"Seeded {len(faq_objs)} FAQs.")

        # ── ANNOUNCEMENTS ──
        announcement_objs = []
        for title, content, cat, priority in ANNOUNCEMENT_DATA:
            a = Announcement(
                id=uuid.uuid4(),
                title=title,
                content=content,
                category=cat,
                priority=priority,
                target_property=None,
                target_room_numbers=[],
                target_bed_types=[],
                published_at=datetime(2026, 5, 10, 8, 0) + timedelta(hours=len(announcement_objs)*12),
                created_at=datetime(2026, 5, 10, 8, 0) + timedelta(hours=len(announcement_objs)*12),
            )
            session.add(a)
            announcement_objs.append(a)
        await session.commit()
        print(f"Seeded {len(announcement_objs)} announcements.")

        # ── METER READINGS ──
        meter_objs = []
        for bldg, rdate, elec, water in METER_READING_DATA:
            m = MeterReading(
                id=uuid.uuid4(),
                building=bldg,
                reading_date=rdate,
                electric_reading=elec,
                water_reading=water,
                status="approved",
                submitted_by=staff_objs[2].id,
            )
            session.add(m)
            meter_objs.append(m)
        await session.commit()
        print(f"Seeded {len(meter_objs)} meter readings.")

        # ── SERVICE REQUESTS ──
        sr_objs = []
        for res_idx, cat, subject, desc, loc, priority, sr_status, submitted, resolution in SERVICE_REQUEST_DATA:
            resolved_at = (submitted + timedelta(days=2)) if sr_status == "resolved" else None
            sr = ServiceRequest(
                id=uuid.uuid4(),
                resident_id=resident_objs[res_idx].id,
                category=cat,
                subject=subject,
                description=desc,
                location=loc,
                priority=priority,
                status=sr_status,
                resolution_notes=resolution,
                submitted_at=submitted,
                resolved_at=resolved_at,
                created_at=submitted,
            )
            session.add(sr)
            sr_objs.append(sr)
        await session.commit()
        print(f"Seeded {len(sr_objs)} service requests.")

        # ── LEDGER ENTRIES ──
        ledger_objs = []
        for i, b in enumerate(billing_objs):
            le = LedgerEntry(
                id=uuid.uuid4(),
                resident_id=b.resident_id,
                entry_type="debit",
                amount=b.total_amount,
                description=f"May 2026 billing",
                reference_id=b.id,
                running_balance=b.total_amount,
                created_at=b.created_at,
            )
            session.add(le)
            ledger_objs.append(le)
        await session.commit()
        print(f"Seeded {len(ledger_objs)} ledger entries.")

        print("\n✅ DEMO SEED COMPLETE")
        print(f"   Rooms: {len(room_objs)}")
        print(f"   Beds: {len(bed_objs)}")
        print(f"   Residents: {len(resident_objs)}")
        print(f"   Inquiries: {len(inquiry_objs)}")
        print(f"   Billings: {len(billing_objs)}")
        print(f"   Payments: {len(payment_objs)}")
        print(f"   Move-outs: {len(moveout_objs)}")
        print(f"   FAQs: {len(faq_objs)}")
        print(f"   Announcements: {len(announcement_objs)}")
        print(f"   Meter Readings: {len(meter_objs)}")
        print(f"   Service Requests: {len(sr_objs)}")
        print(f"   Ledger Entries: {len(ledger_objs)}")


if __name__ == "__main__":
    asyncio.run(seed_all())
