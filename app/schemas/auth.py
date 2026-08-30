from pydantic import BaseModel, Field
from app.schemas.user import UserResponse


class LoginPayload(BaseModel):
    username: str = Field(..., min_length=1)
    password: str = Field(..., min_length=1)


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse


class RefreshTokenPayload(BaseModel):
    refresh_token: str


class PasswordChangePayload(BaseModel):
    current_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8)
