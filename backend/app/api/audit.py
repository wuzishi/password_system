from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models.user import User
from app.models.audit_log import AuditLog
from app.schemas.audit import AuditLogResponse
from app.api.deps import require_role
from app.core.security import Role

router = APIRouter(prefix="/api/audit", tags=["审计日志"])


@router.get("", response_model=List[AuditLogResponse])
def list_audit_logs(
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=200),
    action: str | None = None,
    user_id: int | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(Role.ADMIN)),
):
    query = db.query(AuditLog)
    if action:
        query = query.filter(AuditLog.action.contains(action))
    if user_id:
        query = query.filter(AuditLog.user_id == user_id)
    total = query.count()
    logs = query.order_by(AuditLog.timestamp.desc()).offset((page - 1) * size).limit(size).all()
    result = []
    for log in logs:
        user = db.query(User).filter(User.id == log.user_id).first()
        result.append(AuditLogResponse(
            id=log.id,
            user_id=log.user_id,
            username=user.username if user else "已删除",
            action=log.action,
            resource_type=log.resource_type,
            resource_id=log.resource_id,
            details=log.details,
            ip_address=log.ip_address,
            timestamp=log.timestamp,
        ))
    return result
