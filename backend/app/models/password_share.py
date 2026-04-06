from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.database import Base


class PasswordShare(Base):
    __tablename__ = "password_shares"

    id = Column(Integer, primary_key=True, index=True)
    password_entry_id = Column(Integer, ForeignKey("password_entries.id"), nullable=False)
    shared_with_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    shared_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    permission = Column(String(20), default="view")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    password_entry = relationship("PasswordEntry", back_populates="shares")
    shared_with_user = relationship("User", foreign_keys=[shared_with_user_id])
    shared_by_user = relationship("User", foreign_keys=[shared_by])
