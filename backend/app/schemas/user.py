from pydantic import BaseModel, field_validator, Field
from typing import Optional
from datetime import datetime
from app.core.security import Role
from app.schemas.auth import validate_strong_password


class UserCreate(BaseModel):
    username: str = Field(..., min_length=2, max_length=50)
    email: str = Field(..., max_length=200)
    password: str = Field(..., min_length=8, max_length=200)
    role: Role = Role.DEVELOPER

    @field_validator("password")
    @classmethod
    def check_password(cls, v):
        return validate_strong_password(v)


class UserUpdate(BaseModel):
    email: Optional[str] = Field(None, max_length=200)
    role: Optional[Role] = None
    is_active: Optional[bool] = None
    password: Optional[str] = Field(None, min_length=8, max_length=200)

    @field_validator("password")
    @classmethod
    def check_password(cls, v):
        if v is not None:
            return validate_strong_password(v)
        return v


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    role: Role
    is_active: bool
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ChangePassword(BaseModel):
    old_password: str = Field(..., max_length=200)
    new_password: str = Field(..., min_length=8, max_length=200)

    @field_validator("new_password")
    @classmethod
    def check_password(cls, v):
        return validate_strong_password(v)
