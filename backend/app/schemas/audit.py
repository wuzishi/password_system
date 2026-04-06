from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class AuditLogResponse(BaseModel):
    id: int
    user_id: int
    username: str
    action: str
    resource_type: str
    resource_id: Optional[int] = None
    details: str
    ip_address: str
    timestamp: Optional[datetime] = None

    class Config:
        from_attributes = True
