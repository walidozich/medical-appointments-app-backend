# Medical Backend (FastAPI)

Backend for a medical appointments management app, aligned to the project specification (patients, doctors, appointments, medical records, billing/insurance) with JWT auth and role-based access control.

## Features
- Auth: email/password login, refresh tokens, password reset, logout with token revocation.
- RBAC: roles table (Admin, Doctor, Patient, Staff), role guard dependency.
- Patients: profile CRUD and medical profile fields.
- Doctors: profile CRUD, specialties, availability.
- Appointments: booking, conflict checks, reschedule, cancel; statuses `SCHEDULED/COMPLETED/CANCELLED`.
- Medical Records: diagnoses, treatment plan, prescriptions; doctor/patient scoped access.
- Billing/Insurance: billing entries linked to appointments/patients, insurance policies, claims.
- API envelope: standardized `{success, data, message}` responses; centralized exception handling.

## Project Structure
```
app/
  core/            # settings, logging, security, deps, envelope, exceptions
  db/              # session, base, migrations
  modules/
    auth/          # auth routes/services/schemas
    users/         # user model/routes/services
    patients/      # patient domain
    doctors/       # doctor domain
    appointments/  # booking domain
    medical_records/
    billing/       # billing + insurance
  api_router.py    # aggregates routers under /api/v1
  main.py          # FastAPI app factory
```

## Setup
1) Create `.env` with at least:
```
DATABASE_URL=postgresql+psycopg2://user:pass@host:5432/db
JWT_SECRET_KEY=...
JWT_REFRESH_SECRET=...
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
APP_NAME=MedicalBackend
DEBUG=true
```
2) Install deps (ideally in a venv): `pip install -r requirements.txt`

## Migrations
Use the wrapper to ensure venv is used:
```
python -m alembic upgrade head
```
Requires network access to your Postgres host.

## Run the API
```
uvicorn app.main:app --reload
```
Docs at `/docs` (Swagger) and `/redoc`.

## Seed Sample Algerian Data
Seeds roles, specialties, patients, doctors, availability, and sample appointments. All seeded accounts share password `Algeria123!`.
```
./venv/bin/python seed_algeria_data.py
```
Requires network access to the configured Postgres (`DATABASE_URL` in `.env`).

## Key Endpoints (prefix `/api/v1`)
- Auth: `/auth/register`, `/auth/login`, `/auth/refresh`, `/auth/logout`, `/auth/forgot`, `/auth/reset`
- Users: `/users/me`, `/users` (admin), `/users/{id}` (admin)
- Patients: `/patients/me`, `/patients` (admin)
- Doctors: `/doctors/me/profile`, `/doctors` (public list/admin CRUD), `/doctors/{id}/availability`
- Appointments: `/appointments/me`, `/appointments/doctor/me`, `/appointments` (book), `/appointments/{id}/cancel`, `/appointments/{id}/reschedule`, `/appointments/{id}/status`
- Medical Records: `/medical-records/me`, `/medical-records/doctor/me`, `/medical-records/{id}`
- Billing: `/billing`, `/billing/{id}`, `/billing/me`, `/billing/patient/{id}`, `/billing/policies...`, `/billing/claims...`

## Roles & Access
- Admin: full access.
- Doctor: manage own profile, availability, view own appointments, manage medical records for assigned patients.
- Patient: manage own patient profile, book/cancel/reschedule appointments, view own records and billing/policies.

## Notes
- Response envelope: every JSON response is `{success, data, message}`; errors set `success=false` and `message`.
- Conflicts: appointment booking checks doctor availability and existing scheduled slots.
- Statuses: appointments use `SCHEDULED/COMPLETED/CANCELLED`.
