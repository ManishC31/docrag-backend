import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr

from app.core.constants import UserRole


class UserBase(BaseModel):
    email: EmailStr
    full_name: str | None = None
    avatar_url: str | None = None


class UserResponse(UserBase):
    id: uuid.UUID
    role: UserRole
    is_active: bool
    google_id: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class UserUpdate(BaseModel):
    full_name: str | None = None
    avatar_url: str | None = None


class UserAdminView(UserResponse):
    updated_at: datetime | None = None
