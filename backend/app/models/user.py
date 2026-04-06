from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.database import Base
from app.core.security import Role


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(200), nullable=False)
    role = Column(Enum(Role), default=Role.DEVELOPER, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    team_memberships = relationship("TeamMember", back_populates="user", cascade="all, delete-orphan")
    created_passwords = relationship("PasswordEntry", back_populates="creator", foreign_keys="PasswordEntry.created_by")
    audit_logs = relationship("AuditLog", back_populates="user")
