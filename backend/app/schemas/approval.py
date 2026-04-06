from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class ApprovalCreate(BaseModel):
    password_entry_id: int
    request_type: str  # view / share
    reason: str = ""
    share_target_user_id: Optional[int] = None


class ApprovalReject(BaseModel):
    reject_reason: str = ""


class ApprovalResponse(BaseModel):
    id: int
    requester_id: int
    requester_name: str
    approver_id: Optional[int] = None
    approver_name: Optional[str] = None
    password_entry_id: int
    password_title: str
    request_type: str
    share_target_user_id: Optional[int] = None
    share_target_username: Optional[str] = None
    status: str
    reason: str
    reject_reason: str
    expires_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
