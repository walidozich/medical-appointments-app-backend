# Medical Backend (FastAPI)

Backend for a medical appointments management app, aligned to the project specification (patients, doctors, appointments, medical records, billing/insurance) with JWT auth and role-based access control.

## Features
- Auth: email/password login, refresh tokens, password reset, logout with token revocation.
- RBAC: roles table (Admin, Doctor, Patient, Staff), role guard dependency.
- Patients: profile CRUD and medical profile fields.
- Doctors: profile CRUD, specialties, availability, search/filters, favorites, reviews.
- Appointments: booking, conflict checks, reschedule, cancel; statuses `SCHEDULED/COMPLETED/CANCELLED`; availability slot generation.
- Medical Records: diagnoses, treatment plan, prescriptions; doctor/patient scoped access.
- Billing/Insurance: billing entries linked to appointments/patients, insurance policies, claims.
- Chat: threads, lifecycle (open/closed), per-user archive, messages, read receipts, attachments (png/jpg/pdf up to 10MB), WebSocket real-time delivery, notifications on thread creation/message sent/message read.
- Notifications: in-app notifications with filters, mark-read, mark-all-read, delete, plus WebSocket stream for live updates; chat events auto-generate notifications.
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

## Key Routes (prefix `/api/v1`) and what they do
- Auth:
  - `POST /auth/register` — create account (email/password).
  - `POST /auth/login` — get access/refresh tokens.
  - `POST /auth/refresh` — rotate tokens.
  - `POST /auth/logout` — revoke refresh token.
  - `POST /auth/forgot` / `POST /auth/reset` — password reset flows.
- Users:
  - `GET /users/me` — current user info.
  - `GET/POST/PATCH/DELETE /users` — admin user management.
- Patients:
  - `GET/POST/PATCH /patients/me` — manage your patient profile.
  - `GET/POST/PATCH/DELETE /patients` — admin management.
- Doctors:
  - `GET/POST/PATCH /doctors/me/profile` — manage your doctor profile.
  - `GET /doctors` — public search/filter (name/specialty/city/rating).
  - `GET/POST/PATCH/DELETE /doctors/{id}` — admin CRUD.
  - `GET/POST/PATCH/DELETE /doctors/{id}/availability` — manage time slots.
  - `GET /doctors/{id}/availability/slots` — calendar-friendly available slots.
  - Favorites: `POST/DELETE /doctors/{id}/favorite`, `GET /doctors/me/favorites`.
  - Reviews: `GET/POST /doctors/{id}/reviews`.
- Appointments:
  - `POST /appointments` — book.
  - `GET /appointments/me` — patient view.
  - `GET /appointments/doctor/me` — doctor view.
  - `PATCH /appointments/{id}/status` — update status.
  - `POST /appointments/{id}/cancel` — cancel.
  - `PATCH /appointments/{id}/reschedule` — reschedule.
- Medical Records:
  - `GET/POST /medical-records/me` — patient.
  - `GET /medical-records/doctor/me` — doctor’s assigned.
  - `GET/POST/PATCH/DELETE /medical-records/{id}` — manage records.
- Billing/Insurance:
  - `GET/POST /billing` — billing entries.
  - `GET /billing/me` — patient billing.
  - `GET /billing/patient/{id}` — admin/doctor view.
  - Policies/claims: `/billing/policies...`, `/billing/claims...`.
- Chat:
  - `GET/POST /chat/threads` — list/create thread (patient+doctor).
  - `PATCH /chat/threads/{id}/status` — update thread status (`open/closed` global, `archived` per-user).
  - `GET /chat/threads/unread-count` — total unread messages for current user.
  - `GET /chat/threads` params: `search` (by message content), `sort=recent`, `status=open|closed`, `include_archived` (false excludes your archived).
  - `GET/POST /chat/threads/{id}/messages` — list/send messages.
  - `GET /chat/threads/{id}/messages/search?query=...` — search messages in a thread.
  - `PATCH /chat/messages/{message_id}/read` — mark read (recipient only).
  - `POST /chat/threads/{id}/attachments` — upload attachment (png/jpg/pdf <=10MB) with optional caption.
  - WebSocket messaging: `ws://.../api/v1/chat/ws/chat/{thread_id}` with Bearer token (header or `?token`) for real-time messages/read receipts.
- Notifications:
  - `GET /notifications` — list (supports `is_read`, `type` filters).
  - `PATCH /notifications/{id}/read` — mark one read.
  - `PATCH /notifications/read-all` — mark all read.
  - `DELETE /notifications/{id}` — delete.
  - WebSocket stream: `ws://.../api/v1/notifications/ws?token=<access-token>` (polling push for new notifications).

### WebSockets note
- WebSocket routes are implemented but intentionally absent from Swagger/OpenAPI (OpenAPI documents HTTP only).
  - Chat messaging WS: `ws://.../api/v1/chat/ws/chat/{thread_id}` (Bearer token via header or `?token`).
  - Notifications WS: `ws://.../api/v1/notifications/ws?token=<access-token>`.

### Realtime strategy (MVP vs. push)
- Current: lightweight WebSocket polling for MVP, ok for modest traffic.
- Switch to true push (FCM/APNs/WebPush) if:
  - Active chat needs <500ms delivery
  - Instant appointment change updates are required
  - You plan for 10k+ concurrent clients
  - Mobile apps where polling/WebSockets would drain battery

## Roles & Access
- Admin: full access.
- Doctor: manage own profile, availability, view own appointments, manage medical records for assigned patients.
- Patient: manage own patient profile, book/cancel/reschedule appointments, view own records and billing/policies.

## Notes
- Response envelope: every JSON response is `{success, data, message}`; errors set `success=false` and `message`.
- Conflicts: appointment booking checks doctor availability and existing scheduled slots.
- Statuses: appointments use `SCHEDULED/COMPLETED/CANCELLED`.
