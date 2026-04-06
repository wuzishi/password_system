from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from typing import List
from datetime import datetime, timezone, timedelta
from app.database import get_db
from app.models.user import User
from app.models.password_entry import PasswordEntry
from app.models.password_share import PasswordShare
from app.models.approval import ApprovalRequest
from app.schemas.approval import ApprovalCreate, ApprovalReject, ApprovalResponse
from app.services.audit_service import log_action
from app.api.deps import get_current_user, require_role
from app.core.security import Role

router = APIRouter(prefix="/api/approvals", tags=["审批管理"])


def _to_response(a: ApprovalRequest) -> dict:
    return {
        "id": a.id,
        "requester_id": a.requester_id,
        "requester_name": a.requester.username if a.requester else "",
        "approver_id": a.approver_id,
        "approver_name": a.approver.username if a.approver else None,
        "password_entry_id": a.password_entry_id,
        "password_title": a.password_entry.title if a.password_entry else "",
        "request_type": a.request_type,
        "share_target_user_id": a.share_target_user_id,
        "share_target_username": a.share_target_user.username if a.share_target_user else None,
        "status": a.status,
        "reason": a.reason or "",
        "reject_reason": a.reject_reason or "",
        "expires_at": a.expires_at,
        "created_at": a.created_at,
        "updated_at": a.updated_at,
    }


@router.post("", response_model=ApprovalResponse)
def create_approval(
    req: ApprovalCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    entry = db.query(PasswordEntry).filter(PasswordEntry.id == req.password_entry_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="密码条目不存在")

    # Personal passwords can't be shared
    if entry.security_level == "personal":
        raise HTTPException(status_code=400, detail="个人密码不支持申请")
    if req.request_type == "share" and not req.share_target_user_id:
        raise HTTPException(status_code=400, detail="分享审批需要指定目标用户")

    approval = ApprovalRequest(
        requester_id=current_user.id,
        password_entry_id=req.password_entry_id,
        request_type=req.request_type,
        share_target_user_id=req.share_target_user_id,
        reason=req.reason,
        status="pending",
    )
    db.add(approval)
    db.commit()
    db.refresh(approval)

    log_action(db, current_user.id, "approval.create", "approval", approval.id,
               f"发起{req.request_type}审批 - {entry.title}")

    return _to_response(approval)


@router.get("", response_model=List[ApprovalResponse])
def list_approvals(
    status: str | None = None,
    page: int = 1,
    page_size: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    page_size = min(max(page_size, 1), 200)
    page = max(page, 1)
    query = db.query(ApprovalRequest).options(
        joinedload(ApprovalRequest.requester),
        joinedload(ApprovalRequest.approver),
        joinedload(ApprovalRequest.password_entry),
        joinedload(ApprovalRequest.share_target_user),
    )
    if current_user.role != Role.ADMIN:
        query = query.filter(ApprovalRequest.requester_id == current_user.id)
    if status:
        query = query.filter(ApprovalRequest.status == status)
    results = query.order_by(ApprovalRequest.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return [_to_response(a) for a in results]


@router.get("/pending-count")
def pending_count(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role == Role.ADMIN:
        # Admin sees total pending count
        count = db.query(ApprovalRequest).filter(ApprovalRequest.status == "pending").count()
    else:
        # Non-admin sees their own pending count
        count = db.query(ApprovalRequest).filter(
            ApprovalRequest.requester_id == current_user.id,
            ApprovalRequest.status == "pending",
        ).count()
    return {"count": count}


@router.put("/{approval_id}/approve")
def approve_request(
    approval_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(Role.ADMIN)),
):
    approval = db.query(ApprovalRequest).filter(ApprovalRequest.id == approval_id).first()
    if not approval:
        raise HTTPException(status_code=404, detail="审批请求不存在")
    if approval.status != "pending":
        raise HTTPException(status_code=400, detail="该请求已处理")

    approval.status = "approved"
    approval.approver_id = current_user.id

    entry = db.query(PasswordEntry).filter(PasswordEntry.id == approval.password_entry_id).first()

    if approval.request_type == "view":
        # Grant access: create PasswordShare for the requester
        target_uid = approval.requester_id
        existing_share = db.query(PasswordShare).filter(
            PasswordShare.password_entry_id == approval.password_entry_id,
            PasswordShare.shared_with_user_id == target_uid,
        ).first()
        if not existing_share:
            share = PasswordShare(
                password_entry_id=approval.password_entry_id,
                shared_with_user_id=target_uid,
                shared_by=current_user.id,
                permission="view",
            )
            db.add(share)
        # High security: also set 5-minute time window
        if entry and entry.security_level == "high":
            approval.expires_at = datetime.now(timezone.utc) + timedelta(minutes=5)

    if approval.request_type == "share" and approval.share_target_user_id:
        # Share to another user
        existing_share = db.query(PasswordShare).filter(
            PasswordShare.password_entry_id == approval.password_entry_id,
            PasswordShare.shared_with_user_id == approval.share_target_user_id,
        ).first()
        if not existing_share:
            share = PasswordShare(
                password_entry_id=approval.password_entry_id,
                shared_with_user_id=approval.share_target_user_id,
                shared_by=current_user.id,
                permission="readwrite",
            )
            db.add(share)

    db.commit()

    log_action(db, current_user.id, "approval.approve", "approval", approval.id,
               f"批准{approval.request_type}审批 - {entry.title if entry else ''}")

    return {"message": "已批准"}


@router.put("/{approval_id}/reject")
def reject_request(
    approval_id: int,
    req: ApprovalReject,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(Role.ADMIN)),
):
    approval = db.query(ApprovalRequest).filter(ApprovalRequest.id == approval_id).first()
    if not approval:
        raise HTTPException(status_code=404, detail="审批请求不存在")
    if approval.status != "pending":
        raise HTTPException(status_code=400, detail="该请求已处理")

    approval.status = "rejected"
    approval.approver_id = current_user.id
    approval.reject_reason = req.reject_reason
    db.commit()

    entry = db.query(PasswordEntry).filter(PasswordEntry.id == approval.password_entry_id).first()
    log_action(db, current_user.id, "approval.reject", "approval", approval.id,
               f"拒绝{approval.request_type}审批 - {entry.title if entry else ''}")

    return {"message": "已拒绝"}


@router.get("/check-access/{password_id}")
def check_access(
    password_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Check if user has valid approval for a high-security password."""
    entry = db.query(PasswordEntry).filter(PasswordEntry.id == password_id).first()
    if not entry:
        return {"has_access": False}

    if entry.security_level != "high":
        return {"has_access": True}

    if entry.created_by == current_user.id:
        return {"has_access": True}

    now = datetime.now(timezone.utc)
    approval = db.query(ApprovalRequest).filter(
        ApprovalRequest.requester_id == current_user.id,
        ApprovalRequest.password_entry_id == password_id,
        ApprovalRequest.request_type == "view",
        ApprovalRequest.status == "approved",
        ApprovalRequest.expires_at > now,
    ).first()

    pending = db.query(ApprovalRequest).filter(
        ApprovalRequest.requester_id == current_user.id,
        ApprovalRequest.password_entry_id == password_id,
        ApprovalRequest.request_type == "view",
        ApprovalRequest.status == "pending",
    ).first()

    return {
        "has_access": approval is not None,
        "pending": pending is not None,
        "expires_at": approval.expires_at.isoformat() if approval else None,
    }
