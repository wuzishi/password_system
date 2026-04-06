from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class TeamCreate(BaseModel):
    name: str
    description: str = ""


class TeamUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class TeamMemberAdd(BaseModel):
    user_id: int


class TeamMemberResponse(BaseModel):
    id: int
    user_id: int
    username: str
    email: str
    role: str
    joined_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TeamResponse(BaseModel):
    id: int
    name: str
    description: str
    created_by: int
    created_at: Optional[datetime] = None
    member_count: int = 0

    class Config:
        from_attributes = True


class TeamDetailResponse(TeamResponse):
    members: List[TeamMemberResponse] = []
