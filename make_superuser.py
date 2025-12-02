import asyncio
import sys
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.modules.users.models import User

async def make_superuser(email: str):
    """Make a user a superuser."""
    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    async with SessionLocal() as db:
        user = await db.execute(select(User).where(User.email == email))
        user = user.scalar_one_or_none()

        if user:
            user.is_superuser = True
            await db.commit()
            print(f"User {email} is now a superuser.")
        else:
            print(f"User with email {email} not found.")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python make_superuser.py <email>")
        sys.exit(1)

    email = sys.argv[1]
    asyncio.run(make_superuser(email))
