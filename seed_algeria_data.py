from __future__ import annotations

from datetime import date, datetime, time, timedelta, timezone

from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.core.security import get_password_hash
from app.db.session import SessionLocal
from app.modules.appointments.models import Appointment
from app.modules.doctors.models import Doctor, DoctorAvailability, Specialty, FavoriteDoctor, Review
from app.modules.patients.models import Patient
from app.modules.users.models import Role, User
from app.modules.chat.models import ChatThread, ChatMessage

DEFAULT_PASSWORD = "Algeria123!"
_fallback_bcrypt_used = False

SPECIALTIES = [
    ("Cardiologie", "Cardiologie, hypertension, suivi cardiovasculaire"),
    ("Dermatologie", "Peau, allergie, dermatoses courantes"),
    ("Pédiatrie", "Suivi enfant et adolescent"),
    ("Gynécologie", "Santé de la femme, suivi grossesse"),
    ("ORL", "Oto-rhino-laryngologie, sinusite, audition"),
    ("Médecine interne", "Médecine générale et maladies chroniques"),
    ("Ophtalmologie", "Vision, lunettes, dépistage"),
    ("Neurologie", "Migraine, troubles neurologiques"),
    ("Orthopédie", "Traumatologie, articulations"),
    ("Diabétologie", "Suivi diabète et nutrition"),
]

PATIENTS = [
    {
        "email": "amina.benali@example.dz",
        "first_name": "Amina",
        "last_name": "Benali",
        "phone": "+213555123456",
        "date_of_birth": date(1992, 6, 12),
        "gender": "Female",
        "city": "Alger",
        "country": "Algérie",
    },
    {
        "email": "sofiane.rahmani@example.dz",
        "first_name": "Sofiane",
        "last_name": "Rahmani",
        "phone": "+213554887766",
        "date_of_birth": date(1987, 11, 2),
        "gender": "Male",
        "city": "Oran",
        "country": "Algérie",
    },
    {
        "email": "sara.bouzid@example.dz",
        "first_name": "Sara",
        "last_name": "Bouzid",
        "phone": "+213557998877",
        "date_of_birth": date(1995, 4, 25),
        "gender": "Female",
        "city": "Tizi Ouzou",
        "country": "Algérie",
    },
    {
        "email": "hakim.cheriet@example.dz",
        "first_name": "Hakim",
        "last_name": "Cheriet",
        "phone": "+213553445566",
        "date_of_birth": date(1983, 9, 14),
        "gender": "Male",
        "city": "Constantine",
        "country": "Algérie",
    },
]

DOCTORS = [
    {
        "email": "samir.bensalah@example.dz",
        "first_name": "Samir",
        "last_name": "Bensalah",
        "phone": "+213661112233",
        "bio": "Cardiologue à Oran, suivi HTA et prévention.",
        "years_experience": 12,
        "clinic_address": "23 Rue Emir Abdelkader",
        "city": "Oran",
        "country": "Algérie",
        "specialties": ["Cardiologie"],
        "availability": [("Mon", time(9, 0), time(13, 0)), ("Wed", time(14, 0), time(18, 0))],
    },
    {
        "email": "nadia.khellaf@example.dz",
        "first_name": "Nadia",
        "last_name": "Khellaf",
        "phone": "+213662223344",
        "bio": "Dermatologue à Alger, dermatoses et esthétique légère.",
        "years_experience": 8,
        "clinic_address": "12 Boulevard Didouche Mourad",
        "city": "Alger",
        "country": "Algérie",
        "specialties": ["Dermatologie"],
        "availability": [("Tue", time(10, 0), time(15, 0)), ("Thu", time(9, 0), time(12, 30))],
    },
    {
        "email": "yacine.chekkal@example.dz",
        "first_name": "Yacine",
        "last_name": "Chekkal",
        "phone": "+213663334455",
        "bio": "Pédiatre à Constantine, suivi nourrisson et ado.",
        "years_experience": 10,
        "clinic_address": "4 Avenue Aouati Mostefa",
        "city": "Constantine",
        "country": "Algérie",
        "specialties": ["Pédiatrie"],
        "availability": [("Mon", time(15, 0), time(19, 0)), ("Sat", time(9, 0), time(13, 0))],
    },
    {
        "email": "lila.hamdani@example.dz",
        "first_name": "Lila",
        "last_name": "Hamdani",
        "phone": "+213664445566",
        "bio": "Gynécologue-obstétricienne à Blida.",
        "years_experience": 9,
        "clinic_address": "7 Rue des Frères Bouadou",
        "city": "Blida",
        "country": "Algérie",
        "specialties": ["Gynécologie"],
        "availability": [("Wed", time(9, 30), time(13, 30)), ("Fri", time(9, 0), time(12, 0))],
    },
    {
        "email": "mourad.aitali@example.dz",
        "first_name": "Mourad",
        "last_name": "Ait Ali",
        "phone": "+213665556677",
        "bio": "ORL à Tizi Ouzou, ORL adulte et enfant.",
        "years_experience": 11,
        "clinic_address": "15 Rue Mouloud Feraoun",
        "city": "Tizi Ouzou",
        "country": "Algérie",
        "specialties": ["ORL"],
        "availability": [("Tue", time(14, 0), time(18, 0)), ("Thu", time(14, 0), time(18, 0))],
    },
]

APPOINTMENTS = [
    {
        "patient_email": "amina.benali@example.dz",
        "doctor_email": "samir.bensalah@example.dz",
        "days_from_now": 2,
        "hour": 10,
        "minute": 0,
        "duration_minutes": 30,
        "reason": "Contrôle tension et ECG",
    },
    {
        "patient_email": "sofiane.rahmani@example.dz",
        "doctor_email": "nadia.khellaf@example.dz",
        "days_from_now": 5,
        "hour": 11,
        "minute": 30,
        "duration_minutes": 30,
        "reason": "Dermatite atopique",
    },
    {
        "patient_email": "sara.bouzid@example.dz",
        "doctor_email": "yacine.chekkal@example.dz",
        "days_from_now": -7,
        "hour": 16,
        "minute": 0,
        "duration_minutes": 30,
        "reason": "Suivi post-vaccination",
    },
    {
        "patient_email": "hakim.cheriet@example.dz",
        "doctor_email": "mourad.aitali@example.dz",
        "days_from_now": 3,
        "hour": 15,
        "minute": 30,
        "duration_minutes": 30,
        "reason": "Sinusite chronique",
    },
]

FAVORITES = [
    ("amina.benali@example.dz", "samir.bensalah@example.dz"),
    ("sofiane.rahmani@example.dz", "nadia.khellaf@example.dz"),
    ("sara.bouzid@example.dz", "yacine.chekkal@example.dz"),
    ("hakim.cheriet@example.dz", "mourad.aitali@example.dz"),
]

REVIEWS = [
    ("amina.benali@example.dz", "samir.bensalah@example.dz", 5, "Très bon suivi, explications claires."),
    ("sofiane.rahmani@example.dz", "nadia.khellaf@example.dz", 4, "Consultation rapide, traitement efficace."),
    ("sara.bouzid@example.dz", "yacine.chekkal@example.dz", 5, "Excellent avec les enfants, très patient."),
    ("hakim.cheriet@example.dz", "mourad.aitali@example.dz", 4, "Bon diagnostic et conseils pratiques."),
]

CHAT_THREADS = FAVORITES  # reuse patient->doctor pairs
CHAT_MESSAGES = [
    ("amina.benali@example.dz", "samir.bensalah@example.dz", "Bonjour docteur, j'ai reçu mes analyses."),
    ("samir.bensalah@example.dz", "amina.benali@example.dz", "Bonjour Amina, envoyez-les moi et on vérifie."),
    ("sara.bouzid@example.dz", "yacine.chekkal@example.dz", "Docteur, mon fils tousse encore."),
    ("yacine.chekkal@example.dz", "sara.bouzid@example.dz", "Surveillez la fièvre, sinon passez demain."),
]


def hash_password(raw_password: str) -> str:
    """Hash password using the main security helper, with bcrypt fallback if passlib fails."""
    global _fallback_bcrypt_used
    try:
        return get_password_hash(raw_password)
    except Exception:
        import bcrypt

        _fallback_bcrypt_used = True
        hashed = bcrypt.hashpw(raw_password.encode("utf-8"), bcrypt.gensalt())
        return hashed.decode("utf-8")


def get_or_create_role(db: Session, name: str) -> Role:
    role = db.execute(select(Role).where(Role.name == name.upper())).scalar_one_or_none()
    if role:
        return role
    role = Role(name=name.upper())
    db.add(role)
    db.commit()
    db.refresh(role)
    print(f"Role created: {role.name}")
    return role


def get_or_create_user(db: Session, email: str, role_name: str) -> User:
    user = db.execute(select(User).where(User.email == email)).scalar_one_or_none()
    if user:
        return user
    role = get_or_create_role(db, role_name)
    user = User(
        email=email,
        password_hash=hash_password(DEFAULT_PASSWORD),
        role_id=role.id,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    print(f"User created: {email} [{role_name}]")
    return user


def get_or_create_patient(db: Session, user: User, data: dict) -> Patient:
    patient = db.execute(select(Patient).where(Patient.user_id == user.id)).scalar_one_or_none()
    if patient:
        return patient
    patient = Patient(
        user_id=user.id,
        first_name=data.get("first_name"),
        last_name=data.get("last_name"),
        phone=data.get("phone"),
        date_of_birth=data.get("date_of_birth"),
        gender=data.get("gender"),
        city=data.get("city"),
        country=data.get("country"),
    )
    db.add(patient)
    db.commit()
    db.refresh(patient)
    print(f"Patient profile created for: {data.get('email')}")
    return patient


def get_or_create_specialty(db: Session, name: str, description: str | None = None) -> Specialty:
    specialty = db.execute(select(Specialty).where(Specialty.name == name)).scalar_one_or_none()
    if specialty:
        return specialty
    specialty = Specialty(name=name, description=description)
    db.add(specialty)
    db.commit()
    db.refresh(specialty)
    print(f"Specialty created: {name}")
    return specialty


def get_or_create_doctor(db: Session, user: User, data: dict) -> Doctor:
    doctor = db.execute(select(Doctor).where(Doctor.user_id == user.id)).scalar_one_or_none()
    if doctor:
        return doctor
    doctor = Doctor(
        user_id=user.id,
        first_name=data.get("first_name"),
        last_name=data.get("last_name"),
        phone=data.get("phone"),
        bio=data.get("bio"),
        years_experience=data.get("years_experience"),
        clinic_address=data.get("clinic_address"),
        city=data.get("city"),
        country=data.get("country"),
    )
    db.add(doctor)
    db.commit()
    db.refresh(doctor)
    print(f"Doctor profile created for: {data.get('email')}")
    return doctor


def ensure_specialties(db: Session):
    for name, description in SPECIALTIES:
        get_or_create_specialty(db, name, description)


def ensure_doctor_specialties(db: Session, doctor: Doctor, names: list[str]):
    existing = {spec.name for spec in doctor.specialties}
    for name in names:
        if name in existing:
            continue
        specialty = get_or_create_specialty(db, name)
        doctor.specialties.append(specialty)
    db.add(doctor)
    db.commit()
    db.refresh(doctor)


def ensure_availability(db: Session, doctor: Doctor, availability_data: list[tuple[str, time, time]]):
    current = {(av.weekday, av.start_time, av.end_time) for av in doctor.availability}
    for weekday, start_time, end_time in availability_data:
        if (weekday, start_time, end_time) in current:
            continue
        slot = DoctorAvailability(
            doctor_id=doctor.id,
            weekday=weekday,
            start_time=start_time,
            end_time=end_time,
            is_active=True,
        )
        db.add(slot)
    db.commit()


def ensure_appointment(
    db: Session,
    patient_email: str,
    doctor_email: str,
    days_from_now: int,
    hour: int,
    minute: int,
    duration_minutes: int,
    reason: str,
):
    patient_user = db.execute(select(User).where(User.email == patient_email)).scalar_one_or_none()
    doctor_user = db.execute(select(User).where(User.email == doctor_email)).scalar_one_or_none()
    if not patient_user or not doctor_user:
        print(f"Skip appointment: missing patient or doctor user ({patient_email}, {doctor_email})")
        return
    patient = db.execute(select(Patient).where(Patient.user_id == patient_user.id)).scalar_one_or_none()
    doctor = db.execute(select(Doctor).where(Doctor.user_id == doctor_user.id)).scalar_one_or_none()
    if not patient or not doctor:
        print(f"Skip appointment: missing patient/doctor profile ({patient_email}, {doctor_email})")
        return

    start = datetime.now(timezone.utc).replace(hour=hour, minute=minute, second=0, microsecond=0)
    start = start + timedelta(days=days_from_now)
    end = start + timedelta(minutes=duration_minutes)

    existing = (
        db.execute(
            select(Appointment).where(
                Appointment.patient_id == patient.id,
                Appointment.doctor_id == doctor.id,
                Appointment.start_time == start,
            )
        ).scalar_one_or_none()
    )
    if existing:
        return

    appt = Appointment(
        patient_id=patient.id,
        doctor_id=doctor.id,
        start_time=start,
        end_time=end,
        status="SCHEDULED" if days_from_now >= 0 else "COMPLETED",
        reason=reason,
    )
    db.add(appt)
    db.commit()
    db.refresh(appt)
    print(f"Appointment created: {patient_email} with {doctor_email} on {start.isoformat()}")


def ensure_favorite(db: Session, patient_email: str, doctor_email: str):
    patient_user = db.execute(select(User).where(User.email == patient_email)).scalar_one_or_none()
    doctor_user = db.execute(select(User).where(User.email == doctor_email)).scalar_one_or_none()
    if not patient_user or not doctor_user:
        print(f"Skip favorite: missing user ({patient_email}, {doctor_email})")
        return
    patient = db.execute(select(Patient).where(Patient.user_id == patient_user.id)).scalar_one_or_none()
    doctor = db.execute(select(Doctor).where(Doctor.user_id == doctor_user.id)).scalar_one_or_none()
    if not patient or not doctor:
        print(f"Skip favorite: missing profile ({patient_email}, {doctor_email})")
        return
    exists = db.execute(
        select(FavoriteDoctor).where(
            FavoriteDoctor.patient_id == patient.id,
            FavoriteDoctor.doctor_id == doctor.id,
        )
    ).scalar_one_or_none()
    if exists:
        return
    fav = FavoriteDoctor(patient_id=patient.id, doctor_id=doctor.id)
    db.add(fav)
    db.commit()
    db.refresh(fav)
    print(f"Favorite added: {patient_email} -> {doctor_email}")


def ensure_review(db: Session, patient_email: str, doctor_email: str, rating: int, comment: str | None):
    patient_user = db.execute(select(User).where(User.email == patient_email)).scalar_one_or_none()
    doctor_user = db.execute(select(User).where(User.email == doctor_email)).scalar_one_or_none()
    if not patient_user or not doctor_user:
        print(f"Skip review: missing user ({patient_email}, {doctor_email})")
        return
    patient = db.execute(select(Patient).where(Patient.user_id == patient_user.id)).scalar_one_or_none()
    doctor = db.execute(select(Doctor).where(Doctor.user_id == doctor_user.id)).scalar_one_or_none()
    if not patient or not doctor:
        print(f"Skip review: missing profile ({patient_email}, {doctor_email})")
        return
    exists = db.execute(
        select(Review).where(
            Review.patient_id == patient.id,
            Review.doctor_id == doctor.id,
        )
    ).scalar_one_or_none()
    if exists:
        return
    rev = Review(patient_id=patient.id, doctor_id=doctor.id, rating=rating, comment=comment)
    db.add(rev)
    db.commit()
    db.refresh(rev)
    print(f"Review added: {patient_email} -> {doctor_email} ({rating} stars)")


def recompute_doctor_ratings(db: Session):
    doctors = db.execute(select(Doctor)).scalars().all()
    for doc in doctors:
        stats = db.execute(
            select(
                func.count(Review.id),
                func.avg(Review.rating),
            ).where(Review.doctor_id == doc.id)
        ).one()
        doc.rating_count = int(stats[0] or 0)
        doc.avg_rating = float(stats[1] or 0)
        db.add(doc)
    db.commit()


def ensure_thread(db: Session, patient_email: str, doctor_email: str) -> ChatThread | None:
    patient_user = db.execute(select(User).where(User.email == patient_email)).scalar_one_or_none()
    doctor_user = db.execute(select(User).where(User.email == doctor_email)).scalar_one_or_none()
    if not patient_user or not doctor_user:
        print(f"Skip thread: missing user ({patient_email}, {doctor_email})")
        return None
    patient = db.execute(select(Patient).where(Patient.user_id == patient_user.id)).scalar_one_or_none()
    doctor = db.execute(select(Doctor).where(Doctor.user_id == doctor_user.id)).scalar_one_or_none()
    if not patient or not doctor:
        print(f"Skip thread: missing profile ({patient_email}, {doctor_email})")
        return None
    existing = db.execute(
        select(ChatThread).where(
            ChatThread.patient_id == patient.id,
            ChatThread.doctor_id == doctor.id,
        )
    ).scalar_one_or_none()
    if existing:
        return existing
    thread = ChatThread(patient_id=patient.id, doctor_id=doctor.id)
    db.add(thread)
    db.commit()
    db.refresh(thread)
    print(f"Chat thread created: {patient_email} <-> {doctor_email}")
    return thread


def ensure_message(db: Session, sender_email: str, receiver_email: str, content: str):
    sender_user = db.execute(select(User).where(User.email == sender_email)).scalar_one_or_none()
    receiver_user = db.execute(select(User).where(User.email == receiver_email)).scalar_one_or_none()
    if not sender_user or not receiver_user:
        print(f"Skip message: missing user ({sender_email} -> {receiver_email})")
        return
    # Determine patient/doctor and thread
    sender_role = getattr(sender_user, "role_name", None)
    receiver_role = getattr(receiver_user, "role_name", None)
    if sender_role == "PATIENT":
        patient_user = sender_user
        doctor_user = receiver_user
    elif sender_role == "DOCTOR":
        patient_user = receiver_user
        doctor_user = sender_user
    else:
        print(f"Skip message: unsupported role for {sender_email}")
        return
    thread = ensure_thread(db, patient_email=patient_user.email, doctor_email=doctor_user.email)
    if not thread:
        return
    # avoid duplicate exact message
    exists = db.execute(
        select(ChatMessage).where(
            ChatMessage.thread_id == thread.id,
            ChatMessage.sender_id == sender_user.id,
            ChatMessage.content == content,
        )
    ).scalar_one_or_none()
    if exists:
        return
    msg = ChatMessage(
        thread_id=thread.id,
        sender_id=sender_user.id,
        sender_role=sender_role or "",
        content=content,
    )
    db.add(msg)
    db.commit()
    db.refresh(msg)
    print(f"Chat message added: {sender_email} -> {receiver_email}")


def seed():
    db = SessionLocal()
    try:
        # Ensure core roles
        for role_name in ["ADMIN", "DOCTOR", "PATIENT", "STAFF"]:
            get_or_create_role(db, role_name)

        ensure_specialties(db)

        for patient_data in PATIENTS:
            user = get_or_create_user(db, patient_data["email"], "PATIENT")
            get_or_create_patient(db, user, patient_data)

        for doctor_data in DOCTORS:
            user = get_or_create_user(db, doctor_data["email"], "DOCTOR")
            doctor = get_or_create_doctor(db, user, doctor_data)
            ensure_doctor_specialties(db, doctor, doctor_data.get("specialties", []))
            ensure_availability(db, doctor, doctor_data.get("availability", []))

        for appt in APPOINTMENTS:
            ensure_appointment(
                db,
                patient_email=appt["patient_email"],
                doctor_email=appt["doctor_email"],
                days_from_now=appt["days_from_now"],
                hour=appt["hour"],
                minute=appt["minute"],
                duration_minutes=appt["duration_minutes"],
                reason=appt["reason"],
            )
        for fav in FAVORITES:
            ensure_favorite(db, patient_email=fav[0], doctor_email=fav[1])

        for rev in REVIEWS:
            ensure_review(db, patient_email=rev[0], doctor_email=rev[1], rating=rev[2], comment=rev[3])

        recompute_doctor_ratings(db)

        for pt_doc in CHAT_THREADS:
            ensure_thread(db, patient_email=pt_doc[0], doctor_email=pt_doc[1])
        for msg in CHAT_MESSAGES:
            ensure_message(db, sender_email=msg[0], receiver_email=msg[1], content=msg[2])
        if _fallback_bcrypt_used:
            print("Used bcrypt fallback for password hashing (passlib backend unavailable for long-secret check).")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
    print("Seeding completed. Default password for all seeded users: Algeria123!")
