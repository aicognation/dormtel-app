# Dormtel Automation

End-to-end dormitory operations automation built with the C.R.E.A.T.E. Framework, synthesizing 22 B.U.I.L.D. artifacts into a production-grade FastAPI + React application.

## Quick Start

```bash
docker-compose up --build
```

- API: http://localhost:8000
- Frontend: http://localhost:3000
- API docs: http://localhost:8000/docs

## Features

1. **Smart Inquiry Hub** — Multi-channel auto-response, lead scoring, CRM logging
2. **Digital Onboarding** — Reservation, e-signature, payment links, resident activation
3. **Auto-Billing Engine** — Meter ingestion, anomaly detection, batch distribution
4. **Payment Gateway & Reconciliation** — Digital-first payments, auto-reconcile, DSR
5. **Move-Out Settlement** — Clearance, final billing, refund compilation, tracking

## Tech Stack

- Backend: Python 3.12 + FastAPI + SQLAlchemy (async)
- Frontend: React 18 + Tailwind CSS
- Database: PostgreSQL 15
- Cache/Queue: Redis + Celery
- Payment: Xendit / PayMongo
- Email/SMS: SendGrid / Semaphore
- E-Signature: DocuSign / HelloSign

## Project Structure

```
dormtel-app/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── models.py
│   │   ├── schemas.py
│   │   ├── database.py
│   │   ├── routers/
│   │   │   ├── inquiries.py
│   │   │   ├── onboarding.py
│   │   │   ├── billing.py
│   │   │   ├── payments.py
│   │   │   └── moveouts.py
│   │   └── tests/
│   │       ├── conftest.py
│   │       ├── test_inquiries.py
│   │       ├── test_onboarding.py
│   │       ├── test_billing.py
│   │       ├── test_payments.py
│   │       └── test_moveouts.py
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── App.js
│   │   └── components/
│   │       └── Dashboard.js
│   ├── public/
│   ├── Dockerfile
│   └── package.json
├── docker-compose.yml
└── README.md
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| DATABASE_URL | postgresql+asyncpg://postgres:postgres@db:5432/dormtel | PostgreSQL connection |
| REDIS_URL | redis://redis:6379/0 | Redis connection |

## Compliance

- BIR sequential invoicing
- Data Privacy Act RA 10173
- E-Commerce Act RA 8792

## License

Proprietary — Dormtel Operations
