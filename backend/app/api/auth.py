from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from pydantic import BaseModel, Field, field_validator
from slowapi import Limiter
from slowapi.util import get_remote_address
from app.database import get_db
from app.schemas.auth import validate_strong_password
from app.models.user import User
from app.models.invitation import Invitation
from app.schemas.auth import LoginRequest, Token
from app.schemas.user import UserResponse
from app.services.auth_service import (
    hash_password, verify_password, create_access_token,
    create_refresh_token, decode_token, revoke_token,
)
from app.api.deps import get_current_user
from app.core.security import Role

router = APIRouter(prefix="/api/auth", tags=["认证"])
limiter = Limiter(key_func=get_remote_address)


@router.post("/login", response_model=Token)
@limiter.limit("10/minute")
def login(request: Request, req: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == req.username).first()
    if not user or not verify_password(req.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户名或密码错误")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="账号已被禁用")
    token_data = {"sub": str(user.id), "role": user.role.value}
    access = create_access_token(token_data)
    refresh = create_refresh_token(token_data)
    return Token(
        access_token=access,
        refresh_token=refresh,
        role=user.role.value,
        username=user.username,
        user_id=user.id,
    )


@router.post("/refresh", response_model=Token)
@limiter.limit("30/minute")
def refresh_token(request: Request, db: Session = Depends(get_db)):
    """用 refresh_token 换取新的 access_token。"""
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="缺少认证信息")
    old_token = auth_header[7:]
    payload = decode_token(old_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="无效的刷新令牌")
    user_id = payload.get("sub")
    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="用户不存在或已禁用")
    # 废弃旧 refresh token
    revoke_token(old_token)
    token_data = {"sub": str(user.id), "role": user.role.value}
    new_access = create_access_token(token_data)
    new_refresh = create_refresh_token(token_data)
    return Token(
        access_token=new_access,
        refresh_token=new_refresh,
        role=user.role.value,
        username=user.username,
        user_id=user.id,
    )


@router.post("/logout")
def logout(request: Request, current_user: User = Depends(get_current_user)):
    """登出：废弃当前 access token。"""
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        revoke_token(auth_header[7:])
    return {"message": "已登出"}


# --- Invitation-based registration ---

class InviteInfoResponse(BaseModel):
    email: str
    role: str
    inviter_name: str


class AcceptInviteRequest(BaseModel):
    token: str = Field(..., max_length=200)
    username: str = Field(..., min_length=2, max_length=50)
    password: str = Field(..., min_length=8, max_length=200)

    @field_validator("password")
    @classmethod
    def check_password(cls, v):
        return validate_strong_password(v)


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
@limiter.limit("5/minute")
def accept_invite(request: Request, req: AcceptInviteRequest, db: Session = Depends(get_db)):
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

    token_data = {"sub": str(user.id), "role": user.role.value}
    access = create_access_token(token_data)
    refresh = create_refresh_token(token_data)
    return Token(
        access_token=access,
        refresh_token=refresh,
        role=user.role.value,
        username=user.username,
        user_id=user.id,
    )
