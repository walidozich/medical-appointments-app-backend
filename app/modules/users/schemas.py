from datetime import datetime
from pydantic import BaseModel, EmailStr
from uuid import UUID

class UserRead(BaseModel):
    id: UUID
    email: EmailStr
    is_active: bool
    is_superuser: bool
    created_at: datetime

    model_config = {
        "from_attributes": True
    }

class UserUpdate(BaseModel):
    email: EmailStr | None = None
    password: str | None = None
    is_active: bool | None = None
    is_superuser: bool | None = None
