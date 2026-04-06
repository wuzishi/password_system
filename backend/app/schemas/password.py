from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class PasswordCreate(BaseModel):
    title: str
    category: str = "website"  # website / server
    username: str = ""
    password: str
    notes: str = ""
    url: str = ""
    host: str = ""
    port: Optional[int] = None
    team_id: Optional[int] = None
    is_personal: bool = False
    security_level: str = "low"  # personal/high/medium/low
    expire_days: int = 0  # 0=never, 90=3 months


class PasswordUpdate(BaseModel):
    title: Optional[str] = None
    category: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    notes: Optional[str] = None
    url: Optional[str] = None
    host: Optional[str] = None
    port: Optional[int] = None
    expire_days: Optional[int] = None
    security_level: Optional[str] = None


class PasswordResponse(BaseModel):
    id: int
    title: str
    category: str
    security_level: str
    username: str
    url: str
    host: str
    port: Optional[int] = None
    team_id: Optional[int] = None
    team_name: Optional[str] = None
    is_personal: bool
    created_by: int
    creator_name: Optional[str] = None
    expire_days: int
    password_changed_at: Optional[datetime] = None
    expire_status: str = "normal"  # normal / warning / expired
    expire_remaining_days: Optional[int] = None
    verify_status: str = "unknown"  # unknown / valid / invalid / error
    last_verified_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class DecryptRequest(BaseModel):
    password_confirm: Optional[str] = None
    decrypt_token: Optional[str] = None


class PasswordDecryptResponse(BaseModel):
    id: int
    title: str
    username: str
    password: str
    notes: str
    url: str
    host: str
    port: Optional[int] = None
    decrypt_token: Optional[str] = None


class ShareCreate(BaseModel):
    shared_with_user_id: int
    permission: str = "view"


class ShareResponse(BaseModel):
    id: int
    password_entry_id: int
    shared_with_user_id: int
    shared_with_username: str
    shared_by: int
    permission: str
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True
