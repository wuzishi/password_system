from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.database import Base


class PasswordEntry(Base):
    __tablename__ = "password_entries"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    category = Column(String(20), default="website")  # website / server
    username = Column(String(200), default="")
    encrypted_password = Column(Text, nullable=False)
    encrypted_notes = Column(Text, default="")
    url = Column(String(500), default="")
    host = Column(String(200), default="")       # server IP/hostname
    port = Column(Integer, nullable=True)         # server port (e.g. 22)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    is_personal = Column(Boolean, default=False)
    expire_days = Column(Integer, default=0)      # 0=never, 90=3 months
    password_changed_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    verify_status = Column(String(20), default="unknown")  # unknown / valid / invalid / error
    last_verified_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    creator = relationship("User", back_populates="created_passwords", foreign_keys=[created_by])
    team = relationship("Team", back_populates="passwords")
    shares = relationship("PasswordShare", back_populates="password_entry", cascade="all, delete-orphan")
