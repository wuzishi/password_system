from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List
from app.database import get_db
from app.models.user import User
from app.models.role_permission import RolePermission, ALL_PERMISSIONS
from app.api.deps import get_current_user, require_role
from app.core.security import Role
from app.services.audit_service import log_action

router = APIRouter(prefix="/api/permissions", tags=["权限管理"])


class PermissionItem(BaseModel):
    role: str
    permission_key: str
    enabled: bool


class PermissionUpdate(BaseModel):
    items: List[PermissionItem]


@router.get("/my")
def get_my_permissions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get current user's enabled permission keys."""
    role = current_user.role.value
    perms = db.query(RolePermission).filter(
        RolePermission.role == role,
        RolePermission.enabled == True,
    ).all()
    return {"permissions": [p.permission_key for p in perms]}


@router.get("")
def get_all_permissions(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(Role.ADMIN)),
):
    """Get full permission matrix for all roles."""
    all_perms = db.query(RolePermission).all()
    # Build matrix: { role: { permission_key: enabled } }
    matrix = {}
    for p in all_perms:
        if p.role not in matrix:
            matrix[p.role] = {}
        matrix[p.role][p.permission_key] = p.enabled

    return {
        "roles": ["admin", "product", "developer"],
        "permissions": [{"key": k, "label": v} for k, v in ALL_PERMISSIONS],
        "matrix": matrix,
    }


@router.put("")
def update_permissions(
    req: PermissionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(Role.ADMIN)),
):
    """Batch update permissions."""
    for item in req.items:
        # Don't allow disabling admin permissions
        if item.role == "admin":
            continue
        perm = db.query(RolePermission).filter(
            RolePermission.role == item.role,
            RolePermission.permission_key == item.permission_key,
        ).first()
        if perm:
            perm.enabled = item.enabled
        else:
            perm = RolePermission(
                role=item.role,
                permission_key=item.permission_key,
                enabled=item.enabled,
            )
            db.add(perm)
    db.commit()
    log_action(db, current_user.id, "permission.update", "permission", 0, "更新角色权限配置")
    return {"message": "权限已更新"}
