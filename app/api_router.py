from fastapi import APIRouter

from app.modules.auth.routes import router as auth_router
from app.modules.users.routes import router as users_router
from app.modules.patients.routes import router as patients_router
from app.modules.doctors.routes import router as doctors_router
from app.modules.appointments.routes import router as appointments_router
from app.modules.medical_records.routes import router as medical_records_router
from app.modules.billing.routes import router as billing_router
from app.modules.chat.routes import router as chat_router
from app.modules.notifications.routes import router as notifications_router
from app.modules.admin.routes import router as admin_router

api_router = APIRouter()

api_router.include_router(auth_router, prefix="/auth", tags=["Auth"])
api_router.include_router(users_router, prefix="/users", tags=["Users"])
api_router.include_router(patients_router, prefix="/patients", tags=["Patients"])
api_router.include_router(doctors_router, prefix="/doctors", tags=["Doctors"])
api_router.include_router(appointments_router, prefix="/appointments", tags=["Appointments"])
api_router.include_router(medical_records_router, prefix="/medical-records", tags=["Medical Records"])
api_router.include_router(billing_router, prefix="/billing", tags=["Billing"])
api_router.include_router(chat_router, prefix="/chat", tags=["Chat"])
api_router.include_router(notifications_router, prefix="/notifications", tags=["Notifications"])
api_router.include_router(admin_router, prefix="/admin", tags=["Admin"])


@api_router.get("/health", tags=["Meta"])
def health_check():
    return {"status": "ok"}
