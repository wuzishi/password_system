from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models.user import User
from app.schemas.user import UserResponse, UserUpdate, UserCreate, ChangePassword
from app.services.auth_service import hash_password, verify_password
from app.services.audit_service import log_action
from app.api.deps import get_current_user, require_role
from app.core.security import Role

router = APIRouter(prefix="/api/users", tags=["用户管理"])


@router.get("", response_model=List[UserResponse])
def list_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(Role.ADMIN)),
):
    return db.query(User).all()


@router.post("", response_model=UserResponse)
def create_user(
    req: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(Role.ADMIN)),
):
    if db.query(User).filter(User.username == req.username).first():
        raise HTTPException(status_code=400, detail="用户名已存在")
    if db.query(User).filter(User.email == req.email).first():
        raise HTTPException(status_code=400, detail="邮箱已存在")
    user = User(
        username=req.username,
        email=req.email,
        hashed_password=hash_password(req.password),
        role=req.role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    log_action(db, current_user.id, "user.create", "user", user.id, f"创建用户 {user.username}")
    return user


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
    """All authenticated users can get a simple user list (for sharing)."""
    return db.query(User).filter(User.is_active == True).all()
