from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.database import Base


class ApprovalRequest(Base):
    __tablename__ = "approval_requests"

    id = Column(Integer, primary_key=True, index=True)
    requester_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    approver_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    password_entry_id = Column(Integer, ForeignKey("password_entries.id"), nullable=False)
    request_type = Column(String(20), nullable=False)  # view / share
    share_target_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    status = Column(String(20), default="pending")  # pending / approved / rejected
    reason = Column(Text, default="")
    reject_reason = Column(Text, default="")
    expires_at = Column(DateTime, nullable=True)  # for high-security view approval
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    requester = relationship("User", foreign_keys=[requester_id])
    approver = relationship("User", foreign_keys=[approver_id])
    password_entry = relationship("PasswordEntry")
    share_target_user = relationship("User", foreign_keys=[share_target_user_id])
