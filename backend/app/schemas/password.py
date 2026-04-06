from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class PasswordCreate(BaseModel):
    title: str
    category: str = "website"  # website/server/database/api_key/other
    username: str = ""
    password: str
    notes: str = ""
    url: str = ""
    host: str = ""
    port: Optional[int] = None
    db_type: str = ""
    db_name: str = ""
    api_provider: str = ""
    api_endpoint: str = ""
    team_id: Optional[int] = None
    is_personal: bool = False
    security_level: str = "low"
    expire_days: int = 0


class PasswordUpdate(BaseModel):
    title: Optional[str] = None
    category: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    notes: Optional[str] = None
    url: Optional[str] = None
    host: Optional[str] = None
    port: Optional[int] = None
    db_type: Optional[str] = None
    db_name: Optional[str] = None
    api_provider: Optional[str] = None
    api_endpoint: Optional[str] = None
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
    db_type: str = ""
    db_name: str = ""
    api_provider: str = ""
    api_endpoint: str = ""
    team_id: Optional[int] = None
    team_name: Optional[str] = None
    is_personal: bool
    created_by: int
    creator_name: Optional[str] = None
    expire_days: int
    password_changed_at: Optional[datetime] = None
    expire_status: str = "normal"
    expire_remaining_days: Optional[int] = None
    verify_status: str = "unknown"
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
    db_type: str = ""
    db_name: str = ""
    api_provider: str = ""
    api_endpoint: str = ""
    decrypt_token: Optional[str] = None


class ShareCreate(BaseModel):
    shared_with_user_id: int
    permission: str = "view"  # view / edit


class ShareResponse(BaseModel):
    id: int
    password_entry_id: int
    shared_with_user_id: int
    shared_with_username: str
    shared_by: int
    shared_by_name: str = ""
    permission: str
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True
