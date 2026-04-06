import secrets
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, timezone, timedelta
from pydantic import BaseModel
from app.database import get_db
from app.config import settings
from app.models.user import User
from app.models.invitation import Invitation
from app.schemas.user import UserResponse, UserUpdate, ChangePassword
from app.services.auth_service import hash_password, verify_password
from app.services.email_service import send_invitation_email
from app.services.audit_service import log_action
from app.api.deps import get_current_user, require_role
from app.core.security import Role

router = APIRouter(prefix="/api/users", tags=["用户管理"])


# --- Invitation schemas ---

class InviteRequest(BaseModel):
    email: str
    role: str = "developer"


class InvitationResponse(BaseModel):
    id: int
    email: str
    role: str
    status: str
    invited_by_name: str
    expires_at: datetime | None = None
    created_at: datetime | None = None

    class Config:
        from_attributes = True


# --- Invite endpoints ---

@router.post("/invite")
def invite_user(
    req: InviteRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(Role.ADMIN)),
):
    """Admin sends an email invitation to a new user."""
    if db.query(User).filter(User.email == req.email).first():
        raise HTTPException(status_code=400, detail="该邮箱已注册")

    # Check for existing pending invite
    existing = db.query(Invitation).filter(
        Invitation.email == req.email,
        Invitation.status == "pending",
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="该邮箱已有待接受的邀请")

    token = secrets.token_urlsafe(32)
    invitation = Invitation(
        email=req.email,
        role=req.role,
        token=token,
        invited_by=current_user.id,
        expires_at=datetime.now(timezone.utc) + timedelta(hours=settings.INVITE_EXPIRE_HOURS),
    )
    db.add(invitation)
    db.commit()
    db.refresh(invitation)

    sent = send_invitation_email(req.email, token, req.role, current_user.username)

    log_action(db, current_user.id, "user.invite", "invitation", invitation.id,
               f"邀请 {req.email} 加入, 角色: {req.role}")

    invite_url = f"{settings.SITE_URL}/accept-invite?token={token}"
    return {
        "message": "邀请已发送" if sent else "邮件发送失败，但邀请链接已生成",
        "invite_url": invite_url if not settings.SMTP_HOST else None,
    }


@router.get("/invitations", response_model=List[InvitationResponse])
def list_invitations(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(Role.ADMIN)),
):
    invites = db.query(Invitation).order_by(Invitation.created_at.desc()).all()
    result = []
    for inv in invites:
        # Auto-expire
        if inv.status == "pending" and inv.expires_at and datetime.now(timezone.utc) > inv.expires_at.replace(tzinfo=timezone.utc) if inv.expires_at.tzinfo is None else inv.expires_at:
            inv.status = "expired"
            db.commit()
        inviter = db.query(User).filter(User.id == inv.invited_by).first()
        result.append(InvitationResponse(
            id=inv.id,
            email=inv.email,
            role=inv.role,
            status=inv.status,
            invited_by_name=inviter.username if inviter else "",
            expires_at=inv.expires_at,
            created_at=inv.created_at,
        ))
    return result


@router.post("/invitations/{invite_id}/resend")
def resend_invitation(
    invite_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(Role.ADMIN)),
):
    inv = db.query(Invitation).filter(Invitation.id == invite_id).first()
    if not inv:
        raise HTTPException(status_code=404, detail="邀请不存在")

    # Refresh token and expiry
    inv.token = secrets.token_urlsafe(32)
    inv.expires_at = datetime.now(timezone.utc) + timedelta(hours=settings.INVITE_EXPIRE_HOURS)
    inv.status = "pending"
    db.commit()

    sent = send_invitation_email(inv.email, inv.token, inv.role, current_user.username)
    invite_url = f"{settings.SITE_URL}/accept-invite?token={inv.token}"
    return {
        "message": "邀请已重新发送" if sent else "邮件发送失败",
        "invite_url": invite_url if not settings.SMTP_HOST else None,
    }


@router.delete("/invitations/{invite_id}")
def delete_invitation(
    invite_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(Role.ADMIN)),
):
    inv = db.query(Invitation).filter(Invitation.id == invite_id).first()
    if not inv:
        raise HTTPException(status_code=404, detail="邀请不存在")
    db.delete(inv)
    db.commit()
    return {"message": "已删除"}


# --- User management ---

@router.get("", response_model=List[UserResponse])
def list_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(Role.ADMIN)),
):
    return db.query(User).all()


@router.put("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    req: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(Role.ADMIN)),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    if req.email is not None:
        user.email = req.email
    if req.role is not None:
        user.role = req.role
    if req.is_active is not None:
        user.is_active = req.is_active
    if req.password is not None:
        user.hashed_password = hash_password(req.password)
    db.commit()
    db.refresh(user)
    log_action(db, current_user.id, "user.update", "user", user.id, f"更新用户 {user.username}")
    return user


@router.delete("/{user_id}")
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(Role.ADMIN)),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    if user.id == current_user.id:
        raise HTTPException(status_code=400, detail="不能删除自己")
    log_action(db, current_user.id, "user.delete", "user", user.id, f"删除用户 {user.username}")
    db.delete(user)
    db.commit()
    return {"message": "已删除"}


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.put("/me/password")
def change_my_password(
    req: ChangePassword,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not verify_password(req.old_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="原密码错误")
    current_user.hashed_password = hash_password(req.new_password)
    db.commit()
    return {"message": "密码已更新"}


@router.get("/all", response_model=List[UserResponse])
def list_all_users_simple(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return db.query(User).filter(User.is_active == True).all()
