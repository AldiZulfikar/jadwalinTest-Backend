from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.enums import UserRole


class UserResponse(BaseModel):
    id: UUID
    username: str
    full_name: str
    email: str
    role: UserRole
    is_active: bool
    must_change_password: bool = False
    last_login: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserCreatePayload(BaseModel):
    username: str = Field(..., min_length=2, max_length=50)
    password: str = Field(..., min_length=8)
    full_name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    role: UserRole = UserRole.REQUESTER
    is_active: bool = True


class UserUpdatePayload(BaseModel):
    full_name: Optional[str] = Field(None, min_length=2, max_length=100)
    email: Optional[EmailStr] = None
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None


class UserStatusPayload(BaseModel):
    is_active: bool


class ResetPasswordPayload(BaseModel):
    new_password: str = Field(..., min_length=8, description="New password for target user (minimum 8 characters)")
