from sqlalchemy.orm import Session
from app.models.audit_log import AuditLog


def log_action(
    db: Session,
    user_id: int,
    action: str,
    resource_type: str = "",
    resource_id: int | None = None,
    details: str = "",
    ip_address: str = "",
):
    entry = AuditLog(
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        details=details,
        ip_address=ip_address,
    )
    db.add(entry)
    db.commit()
