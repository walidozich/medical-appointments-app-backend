from datetime import datetime
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from uuid import UUID


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserRead(BaseModel):
    id: UUID
    email: EmailStr
    is_active: bool
    is_superuser: bool
    created_at: datetime

    model_config = {
        "from_attributes": True
    }


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    sub: str
    exp: int
    type: str
