from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from pydantic import BaseModel
from app.database import get_db
from app.models.user import User
from app.models.invitation import Invitation
from app.schemas.auth import LoginRequest, Token
from app.schemas.user import UserResponse
from app.services.auth_service import hash_password, verify_password, create_access_token
from app.core.security import Role

router = APIRouter(prefix="/api/auth", tags=["认证"])


@router.post("/login", response_model=Token)
def login(req: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == req.username).first()
    if not user or not verify_password(req.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户名或密码错误")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="账号已被禁用")
    token = create_access_token({"sub": str(user.id), "role": user.role.value})
    return Token(
        access_token=token,
        role=user.role.value,
        username=user.username,
        user_id=user.id,
    )


# --- Invitation-based registration ---

class InviteInfoResponse(BaseModel):
    email: str
    role: str
    inviter_name: str


class AcceptInviteRequest(BaseModel):
    token: str
    username: str
    password: str


@router.get("/invite-info")
def get_invite_info(token: str, db: Session = Depends(get_db)):
    """Public endpoint: validate invite token and return info."""
    inv = db.query(Invitation).filter(Invitation.token == token).first()
    if not inv:
        raise HTTPException(status_code=404, detail="邀请链接无效")
    if inv.status != "pending":
        raise HTTPException(status_code=400, detail="该邀请已使用或已过期")
    expires = inv.expires_at.replace(tzinfo=timezone.utc) if inv.expires_at.tzinfo is None else inv.expires_at
    if datetime.now(timezone.utc) > expires:
        inv.status = "expired"
        db.commit()
        raise HTTPException(status_code=400, detail="邀请已过期")
    inviter = db.query(User).filter(User.id == inv.invited_by).first()
    return InviteInfoResponse(
        email=inv.email,
        role=inv.role,
        inviter_name=inviter.username if inviter else "",
    )


@router.post("/accept-invite", response_model=Token)
def accept_invite(req: AcceptInviteRequest, db: Session = Depends(get_db)):
    """Public endpoint: accept invitation and create account."""
    inv = db.query(Invitation).filter(Invitation.token == req.token).first()
    if not inv:
        raise HTTPException(status_code=404, detail="邀请链接无效")
    if inv.status != "pending":
        raise HTTPException(status_code=400, detail="该邀请已使用或已过期")
    expires = inv.expires_at.replace(tzinfo=timezone.utc) if inv.expires_at.tzinfo is None else inv.expires_at
    if datetime.now(timezone.utc) > expires:
        inv.status = "expired"
        db.commit()
        raise HTTPException(status_code=400, detail="邀请已过期")

    if db.query(User).filter(User.username == req.username).first():
        raise HTTPException(status_code=400, detail="用户名已存在")
    if db.query(User).filter(User.email == inv.email).first():
        raise HTTPException(status_code=400, detail="该邮箱已注册")

    role = Role(inv.role) if inv.role in [r.value for r in Role] else Role.DEVELOPER
    user = User(
        username=req.username,
        email=inv.email,
        hashed_password=hash_password(req.password),
        role=role,
    )
    db.add(user)
    inv.status = "accepted"
    db.commit()
    db.refresh(user)

    token = create_access_token({"sub": str(user.id), "role": user.role.value})
    return Token(
        access_token=token,
        role=user.role.value,
        username=user.username,
        user_id=user.id,
    )
