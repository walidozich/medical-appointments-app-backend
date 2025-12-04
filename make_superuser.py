import sys
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.modules.users.models import User, Role

def make_superuser(email: str):
    """Make a user a superuser."""
    engine = create_engine(settings.DATABASE_URL, future=True)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, future=True)

    db = SessionLocal()
    try:
        user = db.execute(select(User).where(User.email == email)).scalar_one_or_none()

        if user:
            user.is_superuser = True
            admin_role = db.execute(select(Role).where(Role.name == "ADMIN")).scalar_one_or_none()
            if not admin_role:
                admin_role = Role(name="ADMIN")
                db.add(admin_role)
                db.commit()
                db.refresh(admin_role)
            user.role_id = admin_role.id
            db.add(user)
            db.commit()
            print(f"User {email} is now a superuser.")
        else:
            print(f"User with email {email} not found.")
    finally:
        db.close()

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python make_superuser.py <email>")
        sys.exit(1)

    email = sys.argv[1]
    make_superuser(email)
