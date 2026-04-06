from pydantic import BaseModel, field_validator, Field
from typing import Optional, List, Literal
from datetime import datetime

VALID_CATEGORIES = ("website", "server", "database", "api_key", "other")
VALID_SECURITY_LEVELS = ("personal", "high", "medium", "low")
VALID_PERMISSIONS = ("view", "edit")


class PasswordCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    category: Literal["website", "server", "database", "api_key", "other"] = "website"
    username: str = Field("", max_length=200)
    password: str = Field(..., min_length=1, max_length=2000)
    notes: str = Field("", max_length=5000)
    url: str = Field("", max_length=500)
    host: str = Field("", max_length=200)
    port: Optional[int] = Field(None, ge=1, le=65535)
    db_type: str = Field("", max_length=50)
    db_name: str = Field("", max_length=200)
    api_provider: str = Field("", max_length=100)
    api_endpoint: str = Field("", max_length=500)
    team_id: Optional[int] = None
    is_personal: bool = False
    security_level: Literal["personal", "high", "medium", "low"] = "low"
    expire_days: int = Field(0, ge=0, le=3650)


class PasswordUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    category: Optional[Literal["website", "server", "database", "api_key", "other"]] = None
    username: Optional[str] = Field(None, max_length=200)
    password: Optional[str] = Field(None, min_length=1, max_length=2000)
    notes: Optional[str] = Field(None, max_length=5000)
    url: Optional[str] = Field(None, max_length=500)
    host: Optional[str] = Field(None, max_length=200)
    port: Optional[int] = Field(None, ge=1, le=65535)
    db_type: Optional[str] = Field(None, max_length=50)
    db_name: Optional[str] = Field(None, max_length=200)
    api_provider: Optional[str] = Field(None, max_length=100)
    api_endpoint: Optional[str] = Field(None, max_length=500)
    expire_days: Optional[int] = Field(None, ge=0, le=3650)
    security_level: Optional[Literal["personal", "high", "medium", "low"]] = None


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
    has_permission: bool = False

    class Config:
        from_attributes = True


class DecryptRequest(BaseModel):
    password_confirm: Optional[str] = Field(None, max_length=200)
    decrypt_token: Optional[str] = Field(None, max_length=500)


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
    permission: Literal["view", "edit"] = "view"


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
