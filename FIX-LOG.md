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

*This log should be updated with each subsequent fix or deployment milestone.*
