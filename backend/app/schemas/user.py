from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
from app.core.security import Role


class UserCreate(BaseModel):
    username: str
    email: str
    password: str
    role: Role = Role.DEVELOPER


class UserUpdate(BaseModel):
    email: Optional[str] = None
    role: Optional[Role] = None
    is_active: Optional[bool] = None
    password: Optional[str] = None


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
    old_password: str
    new_password: str
