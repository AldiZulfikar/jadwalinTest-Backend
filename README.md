# JadwalinTest – Backend API Service

> **Slogan**: *Jadwal Terkendali, Aplikasi Siap Berlari!*

Production-ready, high-performance RESTful API backend for **JadwalinTest** (Performance Test Booking System / PTRSV) built with **FastAPI**, **SQLAlchemy 2.0 (Async)**, **Alembic**, **Pydantic v2**, **Local IAM & RBAC**, and **Jinja2 HTML Notification Engine**.

---

## 📋 Table of Contents

- [Architecture & Tech Stack](#-architecture--tech-stack)
- [Key Features](#-key-features)
- [Project Directory Structure](#-project-directory-structure)
- [Environment Configuration](#-environment-configuration)
- [Database Migrations (Alembic)](#-database-migrations-alembic)
- [API Endpoints Reference](#-api-endpoints-reference)
- [Local Installation & Setup](#-local-installation--setup)
- [Automated Testing Suite](#-automated-testing-suite)
- [Security & Observability Hardening](#-security--observability-hardening)
- [Docker & OpenShift Deployment](#-docker--openshift-deployment)

---

## 🚀 Architecture & Tech Stack

The service strictly adheres to **Clean Architecture** principles, decoupling API routes, business service logic, data repositories, domain models, and external notifications.

| Technology | Purpose |
| :--- | :--- |
| **Python 3.10+** | Core programming language |
| **FastAPI** | High-performance asynchronous web framework |
| **SQLAlchemy 2.0 (Async)** | Async ORM for PostgreSQL (`asyncpg`) & SQLite (`aiosqlite`) |
| **Alembic** | Executable database schema migration management |
| **Pydantic v2** | Data validation, serialization, and settings management |
| **PyJWT & Passlib (bcrypt)** | Authentication, JWT token signing, and secure password hashing |
| **Jinja2 & Standard SMTP** | Reusable HTML email templates, exponential retry, and notification audit logs |
| **Pytest & HTTPX AsyncClient** | End-to-end integration and unit testing framework (41 tests, 100% pass) |
| **Docker & OpenShift (OCP)** | Containerization and enterprise Kubernetes deployment readiness |

---

## ✨ Key Features

### 1. Booking Lifecycle Management & Overlap Prevention
- **Automatic Duration Calculation**: Calculates reservation duration in minutes based on start and end times.
- **Overlap Prevention Algorithm**: Validates overlapping reservations on the same performance testing environment before saving.
- **Booking Numbering**: Generates sequential human-readable booking numbers (e.g. `BK-20260830-0001`).
- **State Machine Lifecycle**: Handles status transitions (`Pending` $\rightarrow$ `Approved` / `Rejected` $\rightarrow$ `InProgress` $\rightarrow$ `Completed` / `Cancelled`).
- **Soft Delete**: Cancelling a booking performs a soft delete to maintain audit history.

### 2. Local Identity & Access Management (IAM) & RBAC
- **Role-Based Access Control**:
  - `QA`: Access to approval queues, test execution status, and system user management.
  - `Requester`: Access to schedule calendars, booking submission, and personal reservations.
- **JWT Token Authentication**: Access Tokens (60 mins expiry) and Refresh Tokens (7 days expiry).
- **Default Seed Accounts**:
  - `qa` (`ChangeMe123!`)
  - `requester` (`ChangeMe123!`)

### 3. Operational User Management (QA Only)
- **RESTful User Administration**: QA users can list, search, filter, create, edit, toggle account active status, and reset user passwords via API.
- **Safety Rule 1 (Self-Deactivation Prevention)**: Users cannot deactivate their own account.
- **Safety Rule 2 (At Least One Active QA Rule)**: System prevents deactivating or re-roleing the last remaining active QA user.
- **Safety Rule 3 (Inactive Account Lockout)**: Deactivated accounts (`is_active = False`) are blocked from authenticating (`HTTP 401 Unauthorized`).

### 4. Production Email Notification System
- **HTML Email Templates**: Reusable Jinja2 HTML templates (`base_email.html`, `booking_created.html`, `booking_approved.html`, `booking_rejected.html`, `booking_started.html`, `booking_completed.html`, `booking_cancelled.html`).
- **Recipient Routing Matrix**:
  - `Created`: Sent to `QA_NOTIFICATION_EMAIL`.
  - `Approved / Rejected / Started / Completed`: Sent to Requester (`pic_email`).
  - `Cancelled`: Sent to PIC email and QA team.
- **Transaction Isolation**: Database transactions commit **BEFORE** email delivery. SMTP failures do **NOT** rollback database transactions or crash client API requests.
- **Notification Audit Log**: All notification attempts (Sent, Failed, Simulated) are persisted in the `notification_logs` database table.

---

## 📁 Project Directory Structure

```text
backend/
├── alembic/                      # Database Migration Scripts
│   ├── versions/                 # Executable migration versions (001 - 008)
│   │   ├── 001_create_booking_table.py
│   │   ├── 002_architecture_hardening.py
│   │   ├── 003_foundation_enhancement.py
│   │   ├── 004_booking_lifecycle.py
│   │   ├── 005_update_environments.py
│   │   ├── 006_user_management.py
│   │   ├── 007_seed_iam_users.py
│   │   └── 008_notification_logs.py
│   ├── env.py
│   └── script.py.mako
├── app/                          # Core Application Package
│   ├── api/                      # API Layer (Controllers & Dependencies)
│   │   ├── deps.py               # Dependency injection (Auth, DB, Services)
│   │   └── v1/
│   │       ├── endpoints/        # Endpoint handlers (auth, bookings, environments, health, users)
│   │       └── router.py         # API v1 Router Aggregator
│   ├── core/                     # Core Engine Configuration
│   │   ├── auth_provider.py      # Abstract Authentication Provider Interface
│   │   ├── config.py             # Pydantic Settings & Environment Variables
│   │   ├── exceptions.py         # Custom Application Domain Exceptions
│   │   ├── handlers.py           # Global Exception Handlers (Standardized JSON Envelopes)
│   │   ├── logging.py            # Structured Logger Setup
│   │   └── security.py           # Password Hashing (bcrypt) & JWT Utilities
│   ├── db/                       # Database Setup
│   │   ├── base.py               # Declarative Base
│   │   └── session.py            # Async Engine & Sessionmaker
│   ├── models/                   # SQLAlchemy ORM Models
│   │   ├── booking.py            # Booking Model
│   │   ├── enums.py              # BookingStatus, TestType, UserRole Enums
│   │   ├── environment.py        # Environment Master Model
│   │   ├── notification.py       # NotificationLog Model
│   │   └── user.py               # User Account Model
│   ├── repository/               # Data Access Layer (Repository Pattern)
│   │   ├── base_repository.py    # Generic Async Repository Base
│   │   ├── booking_repository.py
│   │   ├── environment_repository.py
│   │   └── user_repository.py
│   ├── schemas/                  # Pydantic Schemas & DTOs
│   │   ├── auth.py
│   │   ├── booking.py
│   │   ├── common.py             # Standard API Response Envelope & Pagination
│   │   ├── environment.py
│   │   └── user.py
│   ├── services/                 # Business Logic Layer
│   │   ├── booking_service.py    # Overlap validation & Lifecycle state transitions
│   │   ├── email_service.py      # SMTP & Graph API service with retry loop
│   │   ├── environment_service.py
│   │   └── user_service.py       # Safety rules enforcement
│   ├── templates/                # Notification Templates & Renderer
│   │   ├── email/                # Jinja2 HTML Templates
│   │   │   └── base_email.html
│   │   └── render.py             # Jinja2 Template Renderer
│   ├── utils/                    # Shared Helpers
│   │   └── timezone.py           # UTC Datetime Utilities
│   └── main.py                   # FastAPI Application Entrypoint & Middleware
├── tests/                        # Automated Pytest Suite
│   ├── conftest.py               # Test fixtures (DB session, async_client, seed headers)
│   ├── test_auth.py
│   ├── test_booking.py
│   ├── test_email_notifications.py
│   ├── test_environments.py
│   ├── test_health.py
│   ├── test_rbac.py
│   ├── test_security_hardening.py
│   └── test_user_management.py
├── .dockerignore
├── .env.example
├── .gitignore
├── alembic.ini
├── Dockerfile
├── requirements.txt
└── README.md
```

---

## ⚙️ Environment Configuration

Copy `.env.example` to `.env` in the `backend/` directory:

```bash
cp .env.example .env
```

### Key Environment Variables

| Variable | Description | Default / Example |
| :--- | :--- | :--- |
| `APP_NAME` | Application name displayed in headers & logs | `JadwalinTest` |
| `APP_ENV` | Application environment (`development` / `production`) | `development` |
| `DEBUG` | Enable debug logs and hot reload | `true` |
| `PORT` | Uvicorn server port | `8000` |
| `CORS_ALLOWED_ORIGINS` | Comma-separated list of allowed CORS origins | `http://localhost:3000,http://127.0.0.1:3000` |
| `DATABASE_URL` | Async SQLAlchemy database URL | `sqlite+aiosqlite:///./booking.db` |
| `JWT_SECRET_KEY` | Secret key used for signing JWT tokens | *Set secure random string in production* |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Access Token TTL (minutes) | `60` |
| `REFRESH_TOKEN_EXPIRE_DAYS` | Refresh Token TTL (days) | `7` |
| `EMAIL_ENABLED` | Master toggle for email notifications | `true` |
| `EMAIL_PROVIDER` | Email provider (`smtp` or `graph`) | `smtp` |
| `SMTP_HOST` | SMTP server hostname | `smtp.gmail.com` |
| `SMTP_PORT` | SMTP port | `587` |
| `SMTP_USERNAME` | SMTP authentication username | `your-email@gmail.com` |
| `SMTP_PASSWORD` | SMTP authentication password / App Key | `your-app-password` |
| `SMTP_FROM_EMAIL` | Sender email address | `no-reply@example.com` |
| `QA_NOTIFICATION_EMAIL` | Target email for QA team booking notifications | `qa-team@example.com` |

---

## 🗄️ Database Migrations (Alembic)

The database schema is managed via **Alembic**. All migrations are executable and idempotent.

### List of Migration Revisions
1. `001_create_booking_table`: Initial bookings table creation.
2. `002_architecture_hardening`: Normalized environments master table & relationships.
3. `003_foundation_enhancement`: Added booking duration, rejection reasons, and audit fields.
4. `004_booking_lifecycle`: Approval lifecycle timestamps and status columns.
5. `005_update_environments`: Active environment flags and indexes.
6. `006_user_management`: IAM `users` table and `user_id` foreign key.
7. `007_seed_iam_users`: Default seed accounts (`qa` & `requester`).
8. `008_notification_logs`: Notification audit logs table (`notification_logs`).
9. `009_must_change_password`: Added `must_change_password` column to `users` table for mandatory password changes.

### Migration Commands

Run all pending migrations to bring the database schema to latest:
```bash
python3 -m alembic upgrade head
```

Rollback the last applied migration:
```bash
python3 -m alembic downgrade -1
```

Create a new migration revision:
```bash
python3 -m alembic revision -m "your_migration_description"
```

---

## 📌 API Endpoints Reference

All versioned API endpoints are exposed under `/api/v1/...`.

### 🔑 Authentication (`/api/v1/auth`)

| Method | Endpoint | Description | Role Required |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/v1/auth/login` | Authenticate username/password & return JWT access/refresh tokens | Public |
| `POST` | `/api/v1/auth/refresh` | Exchange valid refresh token for a new access token | Public |
| `GET` | `/api/v1/auth/me` | Retrieve authenticated user profile | Authenticated |
| `POST` | `/api/v1/auth/change-password` | Update current user password | Authenticated |

### 📅 Bookings (`/api/v1/bookings` & `/bookings`)

| Method | Endpoint | Description | Role Required |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/bookings` | List paginated bookings with date, status, and environment filters | Authenticated |
| `POST` | `/api/v1/bookings` | Submit new performance test booking with overlap validation | Authenticated |
| `GET` | `/api/v1/bookings/{id}` | Get detailed booking info by UUID | Authenticated |
| `DELETE` | `/api/v1/bookings/{id}` | Cancel booking and perform soft delete | Authenticated |
| `POST` | `/api/v1/bookings/{id}/approve` | Approve pending booking reservation | **QA Only** |
| `POST` | `/api/v1/bookings/{id}/reject` | Reject pending booking reservation with mandatory reason | **QA Only** |
| `POST` | `/api/v1/bookings/{id}/start` | Transition approved booking state to `InProgress` | **QA Only** |
| `POST` | `/api/v1/bookings/{id}/complete` | Transition `InProgress` booking state to `Completed` | **QA Only** |

### 🖥️ Environments (`/api/v1/environments` & `/environments`)

| Method | Endpoint | Description | Role Required |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/environments` | List all active performance testing environments | Authenticated |
| `GET` | `/api/v1/environments/{id}` | Get environment detail by UUID | Authenticated |

### 👥 User Management (`/api/v1/users`)

| Method | Endpoint | Description | Role Required |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/users` | List paginated users with `role`, `is_active`, and `search` filters | **QA Only** |
| `POST` | `/api/v1/users` | Create new system user account | **QA Only** |
| `GET` | `/api/v1/users/{id}` | Get user detail by UUID | **QA Only** |
| `PUT` | `/api/v1/users/{id}` | Edit full name, email, role, and active status | **QA Only** |
| `PATCH` | `/api/v1/users/{id}/status` | Toggle user active status (`is_active: true/false`) | **QA Only** |
| `POST` | `/api/v1/users/{id}/reset-password` | Reset target user password | **QA Only** |

### 🩺 Health & Readiness Probes (`/health`)

| Method | Endpoint | Description | Usage |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/health` | Overall system health status (DB, Email, Version) | Monitoring |
| `GET` | `/api/v1/health/live` | OpenShift Liveness Probe (process vitality check) | Liveness Probe |
| `GET` | `/api/v1/health/ready` | OpenShift Readiness Probe (DB & Email readiness check) | Readiness Probe |

---

## 🛠️ Local Installation & Setup

### 1. Prerequisites
- Python 3.10 or higher
- `pip` and `virtualenv`

### 2. Clone & Setup Virtual Environment
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Configure Environment File
```bash
cp .env.example .env
```

### 5. Run Database Migrations
```bash
python3 -m alembic upgrade head
```

### 6. Launch Backend Server
```bash
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Server will be running at:
- **API Base URL**: `http://localhost:8000`
- **Interactive Swagger Docs**: `http://localhost:8000/docs`
- **ReDoc Docs**: `http://localhost:8000/redoc`

---

## 🧪 Automated Testing Suite

The project features a comprehensive test suite using **Pytest** and **HTTPX AsyncClient**.

```bash
python3 -m pytest -v
```

### Test Suite Summary (`41/41 Passed`)
- `test_auth.py`: Login credentials, JWT validation, token refresh, password change.
- `test_booking.py`: Booking creation, sequence numbers, duration calculation, schedule overlap prevention, soft delete, state transitions.
- `test_email_notifications.py`: HTML template rendering, email disabled mode, email failure transaction isolation (DB commits even if SMTP fails).
- `test_environments.py`: Environment master list retrieval.
- `test_health.py`: Health endpoints, version checks, liveness & readiness probes.
- `test_rbac.py`: Authorization checks for QA vs Requester roles.
- `test_security_hardening.py`: `X-Request-ID` correlation middleware, Security Headers, CORS.
- `test_user_management.py`: User CRUD, safety rules (cannot deactivate self, at least 1 active QA rule).

---

## 🛡️ Security & Observability Hardening

1. **Request Correlation ID (`X-Request-ID`)**: Attaches a unique request UUID to response headers and structured HTTP request logs.
2. **HTTP Security Response Headers**:
   - `X-Content-Type-Options: nosniff`
   - `X-Frame-Options: DENY`
   - `Referrer-Policy: strict-origin-when-cross-origin`
   - `X-XSS-Protection: 1; mode=block`
3. **Password Security**: Passwords are hashed with bcrypt (`passlib`). Plaintext passwords and `password_hash` strings are **never** logged, exposed in API responses, or returned in schemas.
4. **CORS Restrictions**: Allowed origins configured via `CORS_ALLOWED_ORIGINS` instead of `*` in production.
5. **Production JWT Secret Validation**: Startup check validates that production environments do not use default development secret keys.

---

## 🐳 Docker & OpenShift Deployment

### Building and Running Docker Image
```bash
docker build -t jadwalintest-backend:latest .
docker run -d -p 8000:8000 --env-file .env --name backend jadwalintest-backend:latest
```

### OpenShift Readiness
Deployment manifests located in `../deployment/backend/`:
- Configured with `ConfigMap` (`booking-backend-config`) and `Secret` (`booking-backend-secret`).
- Non-root container security context (`runAsNonRoot: true`, `runAsUser: 1001`).
- CPU & Memory resource requests/limits (`100m`/`256Mi` requests, `500m`/`512Mi` limits).
- Validated Liveness (`/api/v1/health/live`) and Readiness (`/api/v1/health/ready`) probes.

---

## 📄 License

Internal Operational Tool for **JadwalinTest Performance QA Team**. All rights reserved.
