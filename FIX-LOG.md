# Dormtel Automation -- Fix Log

> Historical record of all codebase fixes, organized by deployment milestone.
> Each entry documents **what** was broken, **why** it mattered, and **how** it was resolved.

---

## FIX-001: Pre-Deployment Health Check Fixes

**Date:** 2025-05-16
**Milestone:** Pilot Deployment Preparation (Hostinger VPS)
**Triggered By:** Codebase health check prior to first production deployment
**Total Issues Found:** 7 critical, 2 security concerns
**Status:** All Resolved

---

### FIX-001-01: Missing `created_at` Column on `Billing` Model

**Severity:** Critical
**Category:** Data Model / Schema Mismatch

**What was broken:**
The `Billing` SQLAlchemy model in `backend/app/models.py` did not have a `created_at` column, but the Pydantic response schema `BillingOut` in `backend/app/schemas.py` declared `created_at: datetime` as a required output field. This mismatch meant every billing response would fail serialization unless a workaround was in place.

**Why it needed to be fixed:**
- The API contract (OpenAPI schema) promised a `created_at` field to consumers, but the database never stored one.
- A fragile workaround function `_ensure_created_at()` in `backend/app/routers/billing.py` was monkey-patching the object at runtime to inject a fabricated timestamp. This meant billing records returned inconsistent, non-persisted timestamps that changed on every request.
- Any downstream system relying on `created_at` for billing audit trails (BIR compliance, invoicing history) would receive unreliable data.

**What was changed:**
- **`backend/app/models.py`** -- Added `created_at = Column(DateTime, nullable=False, default=datetime.utcnow)` to the `Billing` model class.
- **`backend/app/routers/billing.py`** -- Removed the `_ensure_created_at()` function and all 4 call sites where it was invoked (`generate_billings`, `approve_billing`, `distribute_billing`, `list_billings`).

**Files modified:**
- `backend/app/models.py` (line 87: added column)
- `backend/app/routers/billing.py` (removed function definition and 4 call sites)

---

### FIX-001-02: Missing `created_at` Column on `Payment` Model

**Severity:** Critical
**Category:** Data Model / Schema Mismatch

**What was broken:**
The `Payment` SQLAlchemy model in `backend/app/models.py` did not have a `created_at` column, but the Pydantic response schema `PaymentOut` in `backend/app/schemas.py` declared `created_at: datetime` as a required output field.

**Why it needed to be fixed:**
- A workaround function `_serialize_payment()` in `backend/app/routers/payments.py` manually constructed `PaymentOut` objects, using `payment.matched_at or datetime.utcnow()` as a fallback for the missing `created_at`. This meant:
  - Payments that were never matched (status `pending` or `unreconciled`) would receive a new fabricated timestamp on every API call.
  - The `created_at` value was never persisted, making payment audit trails unreliable.
- Daily Sales Reports (DSR) and BIR-compliant reconciliation depend on accurate payment timestamps.

**What was changed:**
- **`backend/app/models.py`** -- Added `created_at = Column(DateTime, nullable=False, default=datetime.utcnow)` to the `Payment` model class.
- **`backend/app/routers/payments.py`** -- Removed the `_serialize_payment()` function entirely. All 4 endpoints that used it (`payment_webhook`, `list_unmatched`, `match_payment`) now return the Payment model object directly, relying on Pydantic's `from_attributes = True` for serialization.

**Files modified:**
- `backend/app/models.py` (line 101: added column)
- `backend/app/routers/payments.py` (removed function definition and 3 call sites)

---

### FIX-001-03: Missing Tailwind CSS Configuration

**Severity:** Critical
**Category:** Frontend Build / Styling

**What was broken:**
The frontend used Tailwind CSS utility classes extensively throughout all components (e.g., `bg-gray-50`, `text-xl`, `font-bold`, `grid-cols-3`, `space-y-6`, `rounded`, `shadow`, etc.) but had:
- No `tailwind.config.js` file
- No `postcss.config.js` file
- No CSS file with `@tailwind` directives (`@tailwind base; @tailwind components; @tailwind utilities;`)
- No CSS import in `index.js`
- Missing `autoprefixer` and `postcss` dependencies in `package.json`

**Why it needed to be fixed:**
- Without these configuration files, Tailwind CSS classes are never processed during the build. The entire UI renders as unstyled HTML -- no colors, no spacing, no grid layouts, no shadows. The application would be completely unusable visually.
- `react-scripts` (CRA) looks for `tailwind.config.js` and PostCSS config to enable Tailwind processing during `npm run build`.

**What was changed:**
- **Created `frontend/tailwind.config.js`** -- Configured content paths to scan `./src/**/*.{js,jsx,ts,tsx}` and `./public/index.html` for class usage.
- **Created `frontend/src/index.css`** -- Added the three required Tailwind directives (`@tailwind base`, `@tailwind components`, `@tailwind utilities`).
- **`frontend/src/index.js`** -- Added `import './index.css';` to ensure styles are loaded.
- **`frontend/package.json`** -- Added `autoprefixer` (^10.4.0) and `postcss` (^8.4.0) as dependencies required by Tailwind CSS.

**Files created:**
- `frontend/tailwind.config.js`
- `frontend/src/index.css`

**Files modified:**
- `frontend/src/index.js` (added CSS import)
- `frontend/package.json` (added 2 dependencies)

---

### FIX-001-04: Frontend Dockerfile Served Development Server in Production

**Severity:** Critical
**Category:** Infrastructure / Deployment

**What was broken:**
The original `frontend/Dockerfile` ran `CMD ["npm", "start"]`, which executes `react-scripts start` -- the CRA development server. This server:
- Is not optimized for production (no minification, no caching headers)
- Includes hot-reload, source maps, and verbose error overlays
- Has known memory leaks under sustained traffic
- Is explicitly warned against by React documentation for production use

**Why it needed to be fixed:**
- A development server in production is a security and performance risk. It exposes source maps, internal error details, and runs unoptimized code.
- Production frontend should be a static build served by a proper web server (nginx) with SPA routing support (`try_files $uri /index.html`).

**What was changed:**
- **`frontend/Dockerfile`** -- Complete rewrite to a multi-stage build:
  - **Stage 1 (`build`):** Uses `node:20-alpine` to `npm install` and `npm run build`, producing optimized static files in `/app/build`.
  - **Stage 2 (`production`):** Uses `nginx:alpine` to serve the built files from `/usr/share/nginx/html` with a custom nginx config.
- **Created `frontend/nginx.conf`** -- Configured nginx to listen on port 3000, serve static files, and route all non-file requests to `index.html` for SPA client-side routing.

**Files modified:**
- `frontend/Dockerfile` (complete rewrite)

**Files created:**
- `frontend/nginx.conf`

---

### FIX-001-05: No Environment Variable Configuration Files

**Severity:** Critical
**Category:** Configuration Management / Security

**What was broken:**
The project had zero `.env` files or `.env.example` templates. All configuration values were hardcoded:
- Database credentials (`postgres:postgres`) hardcoded in `docker-compose.yml`
- No mechanism to configure CORS origins, API keys, or secrets per environment
- No documentation of what environment variables the application expects

**Why it needed to be fixed:**
- Hardcoded credentials in version-controlled files are a security risk. Anyone with repo access has database credentials.
- Different environments (development, staging, production) require different configuration values. Without env files, there is no standard way to configure the application.
- New developers or deployment operators have no reference for what variables are needed.

**What was changed:**
- **Created `backend/.env.example`** -- Documents all backend environment variables: `DATABASE_URL`, `REDIS_URL`, `CORS_ORIGINS`, `SECRET_KEY`, and placeholders for payment gateway and notification service keys.
- **Created `frontend/.env.example`** -- Documents the `REACT_APP_API_URL` variable.
- **Created `.env.production.example`** -- Production-specific template with `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`, `SECRET_KEY`, `CORS_ORIGINS`, and `REACT_APP_API_URL`. Includes instructions for generating a strong secret key.

**Files created:**
- `backend/.env.example`
- `frontend/.env.example`
- `.env.production.example`

---

### FIX-001-06: No Alembic Database Migration System

**Severity:** Critical
**Category:** Database Schema Management

**What was broken:**
The `requirements.txt` listed `alembic==1.13.1` as a dependency, but the project had:
- No `alembic.ini` configuration file
- No `alembic/` directory with migration scripts
- No `env.py` for async database engine configuration
- No migration script template (`script.py.mako`)
- No way to create or evolve the database schema

The test suite used `Base.metadata.create_all()` to create tables directly, but this approach:
- Cannot handle schema changes (adding/removing columns, renaming tables)
- Provides no migration history or rollback capability
- Is unsuitable for production where data must be preserved across schema changes

**Why it needed to be fixed:**
- Without migrations, deploying schema changes to production requires manual SQL or dropping and recreating all tables (losing all data).
- The Billing and Payment model fixes (FIX-001-01, FIX-001-02) added new columns that need to be created in the database via migration.
- BIR compliance and data integrity require a traceable history of schema changes.

**What was changed:**
- **Created `backend/alembic.ini`** -- Alembic configuration pointing to the `alembic/` directory with async PostgreSQL connection string.
- **Created `backend/alembic/env.py`** -- Configured for async SQLAlchemy engine (`async_engine_from_config`), imports all models to ensure `Base.metadata` is fully populated, reads `DATABASE_URL` from environment.
- **Created `backend/alembic/script.py.mako`** -- Migration script template.
- **Created `backend/alembic/versions/001_initial_schema.py`** -- Initial migration that creates all 11 tables (`staff`, `rooms`, `residents`, `inquiries`, `meter_readings`, `billings`, `payments`, `ledger_entries`, `checkpoints`, `audit_logs`, `move_outs`) with all 14 enum types, foreign keys, and constraints. Includes full `downgrade()` for rollback.
- **Created `backend/entrypoint.sh`** -- Container entrypoint that runs `alembic upgrade head` before starting uvicorn, ensuring migrations are applied on every deployment.
- **Updated `backend/Dockerfile`** -- Now copies `alembic.ini`, `alembic/` directory, and `entrypoint.sh` into the image. Uses `entrypoint.sh` as the container command.

**Files created:**
- `backend/alembic.ini`
- `backend/alembic/env.py`
- `backend/alembic/script.py.mako`
- `backend/alembic/versions/001_initial_schema.py`
- `backend/entrypoint.sh`

**Files modified:**
- `backend/Dockerfile` (added COPY steps for alembic files, changed CMD to entrypoint)

---

### FIX-001-07: No `.gitignore` File

**Severity:** Critical
**Category:** Source Control Hygiene

**What was broken:**
The project had no `.gitignore` file, meaning every file in the project tree would be tracked by git, including:
- `node_modules/` (hundreds of MB of npm packages)
- `__pycache__/` (Python bytecode cache)
- `.env` files (containing secrets and credentials)
- `frontend/build/` (generated build artifacts)
- IDE configuration files (`.vscode/`, `.idea/`)
- OS-specific files (`Thumbs.db`, `.DS_Store`)
- Test coverage artifacts (`.coverage`, `htmlcov/`)

**Why it needed to be fixed:**
- Committing `node_modules/` bloats the repository by hundreds of megabytes and causes merge conflicts.
- Committing `.env` files with production credentials is a critical security vulnerability.
- Committing `__pycache__/` and build artifacts creates unnecessary noise in diffs and can cause cross-platform issues.
- Standard practice for any production project is to have a comprehensive `.gitignore` from the start.

**What was changed:**
- **Created `.gitignore`** -- Comprehensive ignore rules covering Python (`__pycache__/`, `*.py[cod]`, `.venv/`), Node (`node_modules/`, `npm-debug.log*`), build output (`frontend/build/`), environment files (`.env`, `.env.local`, `.env.production`), IDE files (`.vscode/`, `.idea/`), OS files (`.DS_Store`, `Thumbs.db`), Docker volumes (`postgres_data/`), and test coverage (`.coverage`, `.pytest_cache/`).

**Files created:**
- `.gitignore`

---

## Security Hardening (Applied with FIX-001)

### SEC-001-01: CORS Wildcard with Credentials

**Severity:** High
**Category:** Security / API Configuration

**What was broken:**
`backend/app/main.py` had `allow_origins=["*"]` combined with `allow_credentials=True`. This configuration:
- Allows any website on the internet to make credentialed requests to the API
- Browsers will include cookies/auth headers in cross-origin requests from any origin
- Violates OWASP CORS misconfiguration guidelines

**What was changed:**
- **`backend/app/main.py`** -- CORS origins now read from `CORS_ORIGINS` environment variable (comma-separated list), defaulting to `http://localhost:3000` for development. Added `import os` for env var access.

### SEC-001-02: Mock Webhook Signature Verification

**Severity:** Medium
**Category:** Security / Payment Integration

**What exists:**
`backend/app/routers/payments.py` contains `mock_verify_signature()` which always returns `True`. This is acceptable for the current pilot/demo phase but must be replaced with real Xendit/PayMongo HMAC signature verification before processing live payments.

**Status:** Documented for future fix. Acceptable for pilot deployment with test/sandbox payment gateway credentials only.

---

## Infrastructure Additions (Applied with FIX-001)

These are not bug fixes but new infrastructure required for production deployment:

| Addition | Purpose |
|---|---|
| `docker-compose.prod.yml` | Production compose with healthchecks, nginx reverse proxy, env-var-driven config |
| `nginx/default.conf` | Reverse proxy routing `/` to frontend, `/api/` to backend on port 80 |
| `docker-compose.yml` (updated) | Dev compose with healthchecks and `depends_on` conditions |
| `deploy.sh` | VPS deployment script with `setup`, `deploy`, `status`, `logs`, `stop` commands |

---

## Verification Results

All fixes were verified by building and running the full Docker Compose stack locally:

| Check | Result |
|---|---|
| `docker compose build` | Both images built successfully |
| Alembic migration `001` | Ran successfully, all 11 tables created |
| `GET /health` | `{"status":"ok","service":"dormtel-api"}` |
| `POST /api/v1/inquiries/` | 201 Created with `created_at`, `sentiment_score`, `lead_score` |
| `POST /api/v1/inquiries/{id}/respond` | Auto-response generated based on sentiment |
| `GET /api/v1/billings/` | 200 OK, empty list (no active residents) |
| `GET /api/v1/payments/dsr` | DSR report with zero totals |
| `GET /api/v1/moveouts/` | 200 OK |
| `GET /api/v1/onboarding/rooms` | 200 OK |
| OpenAPI spec | 25 endpoints registered |
| Frontend build | Compiled successfully (70.97 kB JS, 2.16 kB CSS gzip) |
| Frontend serving | nginx serving SPA on port 3000 |
| Tailwind CSS | Styles applied correctly in production build |

---

## DEPLOY-001: Pilot Production Deployment to Hostinger VPS

**Date:** 2026-05-16
**Milestone:** First Production Deployment
**Target:** Hostinger VPS (72.60.104.187) -- `dormtel.quriosity.cloud`
**Status:** Deployed & Verified

---

### Environment

| Component | Detail |
|---|---|
| Server OS | Ubuntu 24.04 (kernel 6.8.0-111-generic) |
| Docker | v29.4.0 with Compose v5.1.2 |
| SSL | Let's Encrypt via Certbot (auto-managed) |
| Reverse Proxy | Host-level nginx (shared with other apps) |
| Domain | `dormtel.quriosity.cloud` |

### Architecture Decisions

**Host nginx integration (not Docker nginx):**
The VPS runs a host-level nginx as a shared reverse proxy for 10+ applications (GoalTracker, eSangguni, LEAP100, etc.), each with its own SSL certificate via Certbot. Instead of deploying a separate Docker nginx container (which would conflict on port 80), the DormTel deployment integrates with the existing host nginx by exposing container ports to localhost:
- Frontend: `127.0.0.1:3090` -> container port 3000 (nginx + React SPA)
- API: `127.0.0.1:8090` -> container port 8000 (uvicorn + FastAPI)

The host nginx config at `/etc/nginx/sites-available/dormtel` routes:
- `/api/`, `/docs`, `/openapi.json`, `/health` -> `http://127.0.0.1:8090` (API)
- `/` (catch-all) -> `http://127.0.0.1:3090` (Frontend)

**Old containers replaced:**
Previous deployment containers (`dormtel-backend`, `dormtel-postgres`) were stopped and removed, replaced by the new 4-container stack (api, frontend, db, redis).

### Deployment Steps Executed

1. Generated SSH key and installed on VPS for automated access
2. Uploaded 30 project files to `/opt/dormtel/` via SFTP
3. Created production `.env` with secure database credentials and CORS config
4. Removed Docker nginx service from `docker-compose.prod.yml` (host nginx used instead)
5. Built Docker images on VPS (backend + multi-stage frontend)
6. Updated host nginx config to proxy API routes alongside frontend
7. Stopped old containers, started new stack with `--remove-orphans`
8. Reloaded host nginx, verified all endpoints

### Production Verification

| Check | Result |
|---|---|
| `https://dormtel.quriosity.cloud/health` | `{"status":"ok","service":"dormtel-api"}` |
| `https://dormtel.quriosity.cloud/api/v1/inquiries/` | `200 OK` -- `[]` |
| `https://dormtel.quriosity.cloud/docs` | `HTTP 200` -- Swagger UI |
| `https://dormtel.quriosity.cloud/` | `HTTP 200` -- React SPA |
| HTTP -> HTTPS redirect | `301` -> `https://dormtel.quriosity.cloud/` |
| Alembic migration | Ran successfully on startup |
| Container health | db: healthy, redis: healthy, api: up, frontend: up |
| SSL certificate | Valid (Let's Encrypt, Certbot-managed) |

### Files Modified for Deployment

| File | Change |
|---|---|
| `docker-compose.prod.yml` | Removed nginx service, exposed ports 3090/8090, updated CORS |
| `frontend/Dockerfile` | Added `REACT_APP_API_URL` build arg for production |
| `frontend/src/components/Dashboard.js` | Changed API URL default to relative (same-origin) |
| `/etc/nginx/sites-available/dormtel` (VPS) | Added API proxy routes (`/api/`, `/docs`, `/health`) |

### Containers Running

```
dormtel-api-1        8090->8000/tcp   FastAPI + Uvicorn
dormtel-frontend-1   3090->3000/tcp   nginx + React SPA build
dormtel-db-1         (internal)       PostgreSQL 15
dormtel-redis-1      (internal)       Redis 7
```

---

## FIX-002: Onboarding "Create Reservation" 500 — Deposits Cross-Schema FK

**Date:** 2026-07-20
**Milestone:** Pre-UAT Production Hardening (Alibaba Cloud ECS)
**Triggered By:** Staff bug report — Create Reservation failing with "Request failed with status code 500" whenever deposits were entered
**Status:** Resolved (verified end-to-end on production)

---

### FIX-002-01: `deposits` Table Lived Only in `public` With an Unsatisfiable FK

**Severity:** Critical (blocked all reservations with deposits — the standard booking flow)
**Category:** Data Model / Multi-Schema Architecture

**What was broken:**
The `deposits` table existed only in the `public` schema, and its DB-level constraint `deposits_resident_id_fkey` referenced `public.residents`. Tenant residents, however, live in `demo.residents` / `pilot.residents` (resolved at runtime via `SET search_path TO <schema>, public`). Every deposit INSERT therefore failed with `ForeignKeyViolationError: Key (resident_id)=… is not present in table "residents"` and surfaced as a 500. Reservations *without* deposits succeeded, which is why the bug only fired in the normal flow where advance/security/utility deposits are recorded.

**Why it needed to be fixed:**
- Staff could not book any resident with the standard deposit entries (advance, security, utility + PR numbers), blocking the core onboarding workflow ahead of final UAT.
- The legacy `public` copies of entity tables (residents, beds, billings…) are all shadowed by tenant-schema copies and never receive runtime writes — `deposits` was the only tenant-entity table missing its tenant copies, so it silently fell through to the broken public one. A full FK audit confirmed no other table has this defect.

**What was changed:**
- **`backend/migrations/002_deposits_tenant_tables.sql`** (new, idempotent) — creates `demo.deposits` and `pilot.deposits` with FKs to their own schema's `residents(id)` `ON DELETE CASCADE` (matching the model's `ondelete="CASCADE"`), indexes on `resident_id`, and drops the unsatisfiable `deposits_resident_id_fkey` from the legacy `public.deposits` (0 rows; now permanently shadowed).
- **`.github/workflows/deploy.yml`** — added the same migration block so CI/CD deploys self-migrate.
- **`backend/app/routers/onboarding.py`** — `create_reservation` now commits once (resident + deposits + inquiry conversion in a single transaction). Previously it committed the resident first, so a deposit failure left an orphaned "reserved" resident holding a locked bed that staff could not reassign.

**Verification:**
- Reservation with 3 deposits → `201`; rows landed in `pilot.deposits` (`advance 4300`, `security 4300`, `utility 1000`, all `paid`, receipt numbers intact); `public.deposits` stayed at 0 rows.
- Full model-vs-DB column audit across both schemas: no remaining drift; all other public-only tables (`staff`, `faqs`, `announcements`, `audit_logs`, `password_resets`, `verification_codes`) are legitimately shared with valid FKs.
- All test rows cleaned; affected bed restored to `available`.

**Files modified:**
- `backend/migrations/002_deposits_tenant_tables.sql` (new)
- `backend/app/routers/onboarding.py` (single-transaction commit)
- `.github/workflows/deploy.yml` (deposits migration block)

---

## FIX-003: `payment_method` Enum Drift — `salary_deduction` Rejected + Unvalidated `method` Input

**Date:** 2026-07-20
**Milestone:** Pre-UAT Production Hardening (Alibaba Cloud ECS)
**Triggered By:** Pre-UAT sweep — cross-audit of model `Enum()` vs PG `pg_enum` vs frontend constants
**Status:** Resolved (verified end-to-end on production)

---

### FIX-003-01: UI/API Could Submit `salary_deduction`, DB Enum Rejected It

**Severity:** Medium (latent — the admin `PAYMENT_METHODS` constant offering it is currently unimported dead code and the tenant portal offers only the four valid methods, but the API accepted arbitrary `method` strings, so any API consumer or future UI hitting it got a 500)
**Category:** Data Model / Enum Drift + Input Validation

**What was broken:**
`frontend/src/utils/constants.js` `PAYMENT_METHODS` includes `salary_deduction`, but the PG `payment_method` enum and the model `Enum` only had `{gcash, maya, bank_transfer, cash}`. Worse, `schemas.py` declared `method: str` with no validation on both `PaymentBase` and `TenantPayRequest`, so *any* string (e.g. `bitcoin`) passed pydantic and died at the DB layer as `invalid input value for enum payment_method` → HTTP 500 instead of a clean 422.

**What was changed:**
- **Production PG** — `ALTER TYPE payment_method ADD VALUE IF NOT EXISTS 'salary_deduction';` applied standalone (idempotent; PG enum types live in the shared `public` schema).
- **`backend/migrations/003_payment_method_salary_deduction.sql`** (new) — records the same statement for fresh environments.
- **`.github/workflows/deploy.yml`** — added the same standalone `ALTER TYPE` step (mirrors the existing `inquiry_source` email pattern) so CI/CD deploys self-migrate.
- **`backend/app/models.py`** — `Payment.method` Enum extended with `salary_deduction` (kept in lockstep with PG, per project convention).
- **`backend/app/schemas.py`** — `PaymentBase.method` and `TenantPayRequest.method` changed from `str` to `Literal["gcash", "maya", "bank_transfer", "cash", "salary_deduction"]`, so invalid values now fail fast as 422 validation errors.

**Verification:**
- `pg_enum` now reads `gcash,maya,bank_transfer,cash,salary_deduction`.
- Tenant pay with `method=salary_deduction` → `200`, row persisted and returned by the payments list.
- Tenant pay with `method=bitcoin` → `422` with a clear `literal_error` (previously 500).

**Files modified:**
- `backend/app/models.py`, `backend/app/schemas.py`
- `backend/migrations/003_payment_method_salary_deduction.sql` (new)
- `.github/workflows/deploy.yml`

---

## FIX-004: Inquiry Escalation 500 — `checkpoint_id` Overflows `VARCHAR(20)`

**Date:** 2026-07-20
**Milestone:** Pre-UAT Production Hardening (Alibaba Cloud ECS)
**Triggered By:** Pre-UAT write-flow test — `POST /inquiries/{id}/escalate` returned 500
**Status:** Resolved (verified end-to-end on production)

---

### FIX-004-01: Escalate Wrote a 42-Char Checkpoint ID Into a 20-Char Column

**Severity:** High (100% reproduction — every escalation from the Inquiries page failed with a 500)
**Category:** Data Model / Column Length

**What was broken:**
`escalate_inquiry` built `checkpoint_id = f"CP-01-{inquiry_id}"` (or `CP-02-…`) with the full 36-char UUID — 42 characters — but `checkpoints.checkpoint_id` is `VARCHAR(20)` in every schema (and `String(20)` in the model). Every escalate INSERT died with `StringDataRightTruncationError: value too long for type character varying(20)`. The move-out flow already used the fitting house pattern `CP-11-{uuid[:8]}` (14 chars); inquiries was the outlier.

**What was changed:**
- **`backend/app/routers/inquiries.py`** — checkpoint IDs now truncate the UUID to 8 chars (`CP-01-{str(inquiry_id)[:8]}` / `CP-02-…`), matching `moveouts.py`. 14 chars fit the column; the `CP-01`/`CP-02` prefixes asserted by the backend tests are preserved; the existing duplicate-checkpoint guard turns the astronomically rare 8-char collision into a clean 409. No migration needed.

**Verification:**
- Escalate → `200` with `checkpoint_id=CP-01-11335bcc` (14 chars), inquiry status `escalated`.
- Re-escalate same inquiry → `409 Checkpoint already exists` (duplicate guard intact).
- All probe rows (incl. the checkpoint) cleaned after the test.

**Files modified:**
- `backend/app/routers/inquiries.py`

---

## FIX-005: `create_staff` Split Commit — Staff Row Could Persist Without a Login Path

**Date:** 2026-07-20
**Milestone:** Pre-UAT Production Hardening (Alibaba Cloud ECS)
**Triggered By:** Pre-UAT atomicity audit (multi-commit endpoint scan)
**Status:** Resolved (deployed; behavior structurally identical on the happy path)

---

### FIX-005-01: Verification Code Committed Separately From the Staff Row

**Severity:** Low (only on second-commit failure — but then a staff row existed with no password and no verification code, and retries returned 409 "Email already registered" with no recovery path)
**Category:** Transaction Atomicity

**What was broken:**
`create_staff` committed the staff row, then — only when no password was supplied — created and committed a verification code in a second transaction. A failure between the two commits left an unusable staff row.

**What was changed:**
- **`backend/app/routers/auth.py`** — `staff.id` is client-generated (`uuid4`), so the verification-code row is now added in the same transaction and both commit once: all-or-nothing.

**Files modified:**
- `backend/app/routers/auth.py`

---

## FIX-006: Statement Batch 500 — One Bad Resident Aborted the Whole Billing Run

**Date:** 2026-07-20
**Milestone:** Pre-UAT Production Hardening (Alibaba Cloud ECS)
**Triggered By:** Pre-UAT atomicity audit (multi-commit endpoint scan)
**Status:** Resolved (happy path verified end-to-end on production)

---

### FIX-006-01: No Per-Resident Error Containment in `generate_statements`

**Severity:** Medium (a single resident's PDF/ledger/commit failure 500'd the entire batch while earlier residents were already committed — staff saw a scary error and no report of what succeeded)
**Category:** Transaction Atomicity / Batch Error Handling

**What was broken:**
The per-resident loop in `generate_statements` had no try/except: any exception (PDF render, ledger entry, commit) propagated out as a 500. Earlier iterations' commits stood, but the response carried no error report, and retries relied entirely on the existing-statement skip path.

**What was changed:**
- **`backend/app/routers/statements.py`** — each resident's work is wrapped in try/except: intentional `HTTPException`s re-raise; any other failure rolls back that resident's pending rows, appends a precise per-resident message to the existing `errors` list, and stops the batch cleanly. Earlier residents stay committed; a re-run skips them and resumes at the failed resident. (Continuing on a rolled-back async session is unsafe — expired ORM rows trigger lazy loads — so the loop breaks rather than risks corrupting later financial records. The post-email status commit was left as-is: the email side effect must not roll back generated statements.)

**Verification:**
- Single-resident generation on production → `200` with `generated=1, skipped=0, errors=[]`.
- Syntax-verified; error path is pure containment around unchanged logic.

**Files modified:**
- `backend/app/routers/statements.py`

---

### Pre-UAT Hardening Sweep — Summary of Coverage (2026-07-20)

- **Model-vs-DB column audit** across all 24 models in both `demo` and `pilot`: zero drift.
- **FK + shadowing audit** of every `public` table: `deposits` (FIX-002) was the only defect.
- **Enum audit** (model ↔ `pg_enum` ↔ frontend constants, all 24 enums): one finding (FIX-003).
- **Full-route smoke test**: all 48 GET routes from the live OpenAPI spec (85 paths) — 34 OK, 14 correctly-handled 404/422 with probe params, **0 server errors**.
- **Write-flow tests** on every critical path (reservation ± deposits, payment link, move-in activation, service-request lifecycle, statement generation, tenant payments incl. invalid-method handling, full move-out flow, inquiry lifecycle, FAQ CRUD, misc-transaction CRUD, QR campaigns): all passing after FIX-004; all probe data cleaned and verified (`residents_left=0`, beds restored).
- By-design behaviors confirmed (not bugs): move-in activation requires ID documents + cleared payment (clean 400s); misc-transaction delete requires the `manager` role tier (clean 403 for `admin` role).

---

## FIX-007: Residents Page "Email or phone already exists" — Broken Duplicate Check

**Date:** 2026-07-20
**Milestone:** Pre-UAT Production Hardening (Alibaba Cloud ECS)
**Triggered By:** Staff bug report — "cannot add new residents" on the Residents page (toast: *Failed to create resident / Email or phone already exists*)
**Status:** Resolved (verified end-to-end on production)

---

### FIX-007-01: Duplicate Check Matched Blank Fields and Gave No Clue Which Resident Matched

**Severity:** High (blocked resident creation; two independent failure modes)
**Category:** Input Normalization / Data Visibility

**What was broken:**
Two compounding problems in `POST /residents`:

1. **Blank-field matching.** The create form sends `''` (not `null`) for empty email/phone, and the duplicate check ran `WHERE email = :e OR phone = :p` unconditionally. `phone = ''` matches *every* resident stored with a blank phone, so once a single blank-phone row exists, **every** subsequent create with a blank phone returns 409. The same create endpoint also *stored* the `''` it received (as did `PATCH /residents`), so any edit could re-plant the landmine. Reproduced on production: first blank-phone create → 201 (and the row stored `phone=''`), second blank-phone create → 409.
2. **Invisible duplicates.** The check matched residents across all statuses and bed assignments, but the Residents list filters by property via an outer join on `beds`/`rooms` followed by `WHERE rooms.property_code = :pc` — which silently drops residents with **no bed** (or a bed at another property). A data survey found exactly this in pilot: 1 inactive resident with no bed (invisible in the DT02 list) plus 2 legacy duplicate emails. Staff hitting that email/phone got a generic 409 with no way to find the blocking record — a dead end. (The email comparison was also case-sensitive, while the data already contained case-variant duplicates.)

**What was changed:**
- **`backend/app/routers/residents.py` (`create_resident`)** — email/phone are normalized (`strip()`, blank → `NULL`) before checking and storing; the duplicate check runs only on provided values, email case-insensitively (`lower(email)` both sides); and the 409 now names the matched resident with location and status, e.g. `Email already registered to Juan Dela Cruz (Room 503 / DT02-503A, status: active)` or `… (no bed assigned, status: inactive)` — so staff can immediately find, reactivate, or delete the blocking record. The frontend already toasts `detail` verbatim, so no UI change was needed.
- **`backend/app/routers/residents.py` (`update_resident`)** — same blank → `NULL` normalization on email/phone so edits never re-introduce empty-string rows. (No duplicate check was added to update: legacy data contains pre-existing duplicates, and blocking unrelated edits on them ahead of UAT would do more harm than good.)

**Verification (production):**
- Two consecutive blank-phone creates → both `201` (previously the second 409'd); stored as `null`, not `''`.
- Duplicate email submitted in **uppercase** → `409 Email already registered to <name> (no bed assigned, status: active)` (case-insensitive match, actionable message).
- Duplicate phone → `409 Phone number already registered to <name> (…)`.
- `PATCH` with blank phone → `200`, value stored as `null`.
- All probe rows cleaned after the tests.

**Note for staff:** if the original resident they were trying to add still fails, the new message now tells them exactly which existing record holds that email/phone (the pilot data survey showed one inactive, bed-less resident invisible in the list — likely the original blocker). That record can be reactivated or deleted from the Residents page, then the new resident added.

**Files modified:**
- `backend/app/routers/residents.py`

---

## FIX-008: Inquiry Creation 500 — "column inquiries.campaign_id does not exist" (Recurrence of Inquiries-page 500s)

**Date:** 2026-07-21
**Milestone:** UAT Round — Production (Alibaba Cloud ECS)
**Triggered By:** UAT feedback — "Cannot create new inquiry, request failed with status code 500" on the Inquiries page (payload: Sofia Soriano / Facebook / UNCIANO / DENTISTRY / CPAR / content "NA"); reported as a recurrence of the July 16 finding
**Status:** Resolved (verified end-to-end on production, including a 30-way concurrency hammer)

---

### FIX-008-01: Post-commit Statements Could Run on a Pooled Connection With the Wrong `search_path`

**Severity:** Critical (intermittent 500 on a core UAT flow; latent wrong-schema hazard on every write endpoint)
**Category:** Multi-tenancy / Connection Pooling / Schema Drift

**Why the earlier fix didn't stop it:**
The July 16 fix (FIX-004) resolved a *different* 500 on the Inquiries page — the escalate endpoint overflowing `checkpoints.checkpoint_id` (VARCHAR(20)). This recurrence had a separate root cause, latent since the multi-schema design. It is inherently intermittent: it only fires when the connection pool is churning under concurrent use, which is why single-threaded smoke and write-flow passes never caught it.

**What was broken:**
`get_db` ran `SET search_path TO {schema}, public` on the session's **first** pooled connection. But a SQLAlchemy async session returns its connection to the pool on every `commit()` and may acquire a **different** connection for the next statement. In `create_inquiry`, the sequence is `INSERT → commit → db.refresh()`; under concurrent UAT load the refresh SELECT could land on a connection still carrying another request's `search_path`, or a fresh connection whose default is `"$user", public`. Unqualified `inquiries` then resolved to the **legacy `public.inquiries`** table, which lacked the QR-campaign columns — production DB log proof: the INSERT succeeded, and 5 ms later the refresh SELECT failed on the same backend with `ERROR: column inquiries.campaign_id does not exist` (10:49:14 and 10:49:20 UTC on 2026-07-20; a retry at 10:51:46 won the pool lottery and returned 201, which is why it looked random). The same race could silently read another tenant's rows on any post-commit statement — not just 500.

**What was changed:**
- **`backend/app/database.py` (`get_db`)** — each request is now pinned to ONE dedicated connection for its entire lifetime: `engine.connect()` → `SET search_path TO {schema}, public` → `commit()` (ends the SET's transaction; a plain SET is session-scoped and persists) → `AsyncSession(bind=conn)`. Every statement in the request, before *or* after commit, now runs on the connection that carries the correct `search_path`. The connection-swap roulette is structurally impossible.
- **`backend/migrations/004_sync_public_schema_columns.sql`** (new) — defense-in-depth: re-synced the legacy `public` tables with the three model columns that had only been added to `demo`/`pilot` (`public.inquiries.campaign_id`, `public.inquiries.campaign_title`, `public.residents.company_name`), so even a stray statement resolving to `public` can no longer 500 on a missing column. Applied to production and verified via `information_schema`.
- **`.github/workflows/deploy.yml`** — added the same three `ALTER TABLE ... ADD COLUMN IF NOT EXISTS` statements as an idempotent deploy step, so future deploys keep the public tables in sync.

**Verification (production):**
- Exact UAT payload from the screenshot (Sofia Soriano / Facebook / UNCIANO / DENTISTRY / CPAR / "NA", blank email/phone/external id) → `201`, all fields stored correctly, `property_code=DT02`.
- **Concurrency hammer: 30 parallel creates → 30 × `201`, zero 500s** (2.7 s). This is the pattern that produced the intermittent 500s before the fix.
- Regression: escalate → `CP-01-…` checkpoint created; re-escalate → `409` duplicate guard; respond → auto-response; QR campaign create + campaign-attributed inquiry (`campaign_id`/`campaign_title` stored); `status=new`, `via_qr`, and `convertible` lists all `200`.
- Post-deploy API logs: zero `UndefinedColumnError` / "does not exist" entries; admin portal, tenant portal, and `/health` all `200`.
- All 32 probe inquiries, the probe checkpoint, and the probe campaign deleted; verified `0` rows remaining.

**Files modified:**
- `backend/app/database.py`
- `backend/migrations/004_sync_public_schema_columns.sql` (new)
- `.github/workflows/deploy.yml`

---

## FIX-009: QR Inquiry Property Routing — Public Form Defaulted to DT01 Regardless of Campaign Property

**Date:** 2026-07-21
**Milestone:** UAT Round — Production (Alibaba Cloud ECS)
**Triggered By:** Architectural review — user asked "which tenant table does DT01 use?" → revealed property-level isolation bug in QR inquiry creation
**Status:** Resolved (verified end-to-end on production with empirical testing)

---

### FIX-009-01: Public QR Inquiries Filed Under Wrong Property (DT01 Instead of Campaign's Property)

**Severity:** Critical (property-level data leak + broken isolation between DT01 and DT02)
**Category:** Multi-tenancy / Property Isolation / QR Campaigns

**Why earlier fixes didn't catch it:**
Previous inquiry fixes (FIX-004 escalate checkpoint overflow, FIX-008 connection-swap race) addressed *different* code paths. This bug was latent since the QR campaigns feature was added — it only manifests when a public QR form is submitted (no auth), which hadn't been tested empirically until now.

**What was broken:**
When a QR campaign was created for DT02 and a prospect scanned the QR code and submitted the public inquiry form (no authentication, only `X-Tenant-Schema: pilot` header), the `create_inquiry` endpoint used this fallback chain:

```python
property_code=payload.property_code or property_code or "DT01"
```

- `payload.property_code` — `None` (QR forms don't send it)
- `property_code` (from JWT) — `None` (public form, no auth)
- Hardcoded fallback — `"DT01"`

The endpoint fetched the campaign to validate it exists and extract `campaign_id`/`campaign_title`, but **never extracted `campaign.property_code`**. So the inquiry was stored with `property_code='DT01'` regardless of which property the campaign belonged to.

**Production impact (verified empirically):**
- DT02 QR campaign created → public inquiry submitted → stored as `property_code='DT01'`
- DT01 staff viewing Inquiries page → **could see DT02's QR leads** (data leak)
- DT02 staff viewing Inquiries page → **could NOT see their own QR leads** (broken isolation)

This is a property-level isolation bug: both DT01 and DT02 share the same `pilot.inquiries` table, isolated by `WHERE property_code = :pc` filtering. When the filtering is wrong, you get cross-property data exposure.

**What was changed:**
- **`backend/app/routers/inquiries.py` (`create_inquiry`)** — when `campaign_id` is provided, the campaign's `property_code` is now extracted and used as the **authoritative source** for the inquiry's `property_code`. The fallback chain is now: `campaign.property_code` → `payload.property_code` → `JWT property_code` → `"DT01"`. Also added validation: if `payload.property_code` is explicitly provided alongside `campaign_id`, they must match (else 422 with clear error message).
- **`backend/migrations/005_qr_inquiry_property_validation.sql`** (new) — defense-in-depth: created database triggers on `pilot.inquiries` and `demo.inquiries` that validate `inquiry.property_code` matches `campaign.property_code` when `campaign_id` is not NULL. Even if the application code has a bug, the DB will reject mismatched inserts with `ERROR: Property mismatch: inquiry property_code (%) does not match campaign property_code (%)`. Applied to production and verified via direct SQL insert attempts.
- **`.github/workflows/deploy.yml`** — added the trigger creation as an idempotent deploy step (drops existing triggers/functions before recreating, so it's safe to run on every deploy).

**Verification (production, empirical testing):**
- **Public QR form (no auth)**: created DT02 campaign → submitted inquiry with `campaign_id` but no `property_code` in payload → stored as `property_code='DT02'` ✓ (was `'DT01'` before fix)
- **Authenticated QR submission (DT02 staff)**: inquiry stored as `property_code='DT02'` ✓
- **Property mismatch validation**: submitted inquiry with `campaign_id=DT02 campaign` and explicit `property_code='DT01'` → `422` with message `"Property mismatch: inquiry property_code 'DT01' does not match campaign property_code 'DT02'"` ✓
- **Authenticated non-QR inquiry (admin portal, no campaign)**: inquiry stored as `property_code='DT02'` (from JWT) ✓
- **DB trigger blocks mismatched inserts**: direct SQL `INSERT INTO pilot.inquiries (..., property_code='DT01', campaign_id=<DT02 campaign>)` → `ERROR: Property mismatch` ✓
- **DB trigger allows correct inserts**: direct SQL `INSERT INTO pilot.inquiries (..., property_code='DT02', campaign_id=<DT02 campaign>)` → succeeded ✓
- **Visibility isolation verified**: DT01 staff cannot see DT02's QR inquiries; DT02 staff can see their own QR inquiries ✓

**Files modified:**
- `backend/app/routers/inquiries.py`
- `backend/migrations/005_qr_inquiry_property_validation.sql` (new)
- `.github/workflows/deploy.yml`

---

*This log should be updated with each subsequent fix or deployment milestone.*
