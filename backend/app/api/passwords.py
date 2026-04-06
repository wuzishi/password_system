from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, timezone
from app.database import get_db
from app.models.user import User
from app.models.password_entry import PasswordEntry
from app.models.password_share import PasswordShare
from app.models.team_member import TeamMember
from app.schemas.password import (
    PasswordCreate, PasswordUpdate, PasswordResponse,
    PasswordDecryptResponse, DecryptRequest, ShareCreate, ShareResponse,
)
from app.services.crypto_service import encrypt, decrypt, migrate_if_needed
from app.services.auth_service import verify_password, create_decrypt_token, verify_decrypt_token
from app.models.approval import ApprovalRequest
from app.services.audit_service import log_action
from app.api.deps import get_current_user, require_role
from app.core.security import Role, SecurityLevel, has_permission

router = APIRouter(prefix="/api/passwords", tags=["密码管理"])


def _can_access(user: User, entry: PasswordEntry, db: Session) -> bool:
    """Check if user can see this entry in the list (not decrypt)."""
    level = entry.security_level or "low"

    # Personal: only creator, nobody else including admin
    if level == "personal":
        return entry.created_by == user.id

    # Creator always has access
    if entry.created_by == user.id:
        return True

    # Admin has access to all non-personal entries
    if user.role == Role.ADMIN:
        return True

    # High: team members can see it in list (but decrypt requires approval)
    # Medium: team members + shared users
    # Low: team members + shared users
    if entry.team_id:
        is_member = db.query(TeamMember).filter(
            TeamMember.team_id == entry.team_id, TeamMember.user_id == user.id
        ).first()
        if is_member:
            return True

    shared = db.query(PasswordShare).filter(
        PasswordShare.password_entry_id == entry.id,
        PasswordShare.shared_with_user_id == user.id,
    ).first()
    return shared is not None


def _can_decrypt(user: User, entry: PasswordEntry, db: Session) -> tuple[bool, str]:
    """Check if user can decrypt this password. Returns (allowed, reason)."""
    level = entry.security_level or "low"

    # Personal: only creator
    if level == "personal":
        if entry.created_by == user.id:
            return True, ""
        return False, "个人密码仅本人可查看"

    # Creator always ok
    if entry.created_by == user.id:
        return True, ""

    # High: needs approved & unexpired approval
    if level == "high":
        if user.role == Role.ADMIN:
            return True, ""
        now = datetime.now(timezone.utc)
        approval = db.query(ApprovalRequest).filter(
            ApprovalRequest.requester_id == user.id,
            ApprovalRequest.password_entry_id == entry.id,
            ApprovalRequest.request_type == "view",
            ApprovalRequest.status == "approved",
            ApprovalRequest.expires_at > now,
        ).first()
        if approval:
            return True, ""
        return False, "高安全密码需要Admin审批后才能查看"

    # Medium/Low: standard access check
    if user.role == Role.ADMIN:
        return True, ""
    if not _can_access(user, entry, db):
        return False, "无权访问"
    return True, ""


def _calc_expire_status(entry: PasswordEntry) -> tuple[str, int | None]:
    """Returns (status, remaining_days). Status: normal/warning/expired."""
    if not entry.expire_days or entry.expire_days <= 0:
        return "normal", None
    changed_at = entry.password_changed_at or entry.created_at
    if not changed_at:
        return "normal", None
    now = datetime.now(timezone.utc)
    if changed_at.tzinfo is None:
        from datetime import timezone as tz
        changed_at = changed_at.replace(tzinfo=tz.utc)
    elapsed = (now - changed_at).days
    remaining = entry.expire_days - elapsed
    if remaining <= 0:
        return "expired", remaining
    elif remaining <= 15:
        return "warning", remaining
    else:
        return "normal", remaining


def _to_response(entry: PasswordEntry, db: Session) -> dict:
    team_name = entry.team.name if entry.team else None
    creator_name = entry.creator.username if entry.creator else None
    expire_status, expire_remaining = _calc_expire_status(entry)
    return {
        "id": entry.id,
        "title": entry.title,
        "category": entry.category or "website",
        "security_level": entry.security_level or "low",
        "username": entry.username,
        "url": entry.url,
        "host": entry.host or "",
        "port": entry.port,
        "db_type": entry.db_type or "",
        "db_name": entry.db_name or "",
        "api_provider": entry.api_provider or "",
        "api_endpoint": entry.api_endpoint or "",
        "team_id": entry.team_id,
        "team_name": team_name,
        "is_personal": entry.is_personal,
        "created_by": entry.created_by,
        "creator_name": creator_name,
        "expire_days": entry.expire_days or 0,
        "password_changed_at": entry.password_changed_at,
        "expire_status": expire_status,
        "expire_remaining_days": expire_remaining,
        "verify_status": entry.verify_status or "unknown",
        "last_verified_at": entry.last_verified_at,
        "created_at": entry.created_at,
        "updated_at": entry.updated_at,
    }


@router.get("", response_model=List[PasswordResponse])
def list_passwords(
    team_id: int | None = None,
    is_personal: bool | None = None,
    keyword: str | None = None,
    category: str | None = None,
    expire_status: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(PasswordEntry)
    if team_id is not None:
        query = query.filter(PasswordEntry.team_id == team_id)
    if is_personal is not None:
        query = query.filter(PasswordEntry.is_personal == is_personal)
    if category:
        query = query.filter(PasswordEntry.category == category)
    if keyword:
        query = query.filter(
            PasswordEntry.title.contains(keyword) | PasswordEntry.username.contains(keyword) | PasswordEntry.url.contains(keyword) | PasswordEntry.host.contains(keyword)
        )
    entries = query.order_by(PasswordEntry.updated_at.desc()).all()
    results = [_to_response(e, db) for e in entries if _can_access(current_user, e, db)]
    if expire_status:
        results = [r for r in results if r["expire_status"] == expire_status]
    return results


@router.get("/expiring", response_model=List[PasswordResponse])
def list_expiring_passwords(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get passwords that are expired or expiring within 15 days."""
    entries = db.query(PasswordEntry).filter(PasswordEntry.expire_days > 0).all()
    results = []
    for e in entries:
        if not _can_access(current_user, e, db):
            continue
        resp = _to_response(e, db)
        if resp["expire_status"] in ("expired", "warning"):
            results.append(resp)
    results.sort(key=lambda r: r["expire_remaining_days"] or -9999)
    return results


@router.post("", response_model=PasswordResponse)
def create_password(
    req: PasswordCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if req.is_personal:
        if not has_permission(current_user.role, "password.create_personal"):
            raise HTTPException(status_code=403, detail="权限不足")
    else:
        if not has_permission(current_user.role, "password.create_team"):
            raise HTTPException(status_code=403, detail="权限不足")
        if req.team_id:
            if current_user.role != Role.ADMIN:
                is_member = db.query(TeamMember).filter(
                    TeamMember.team_id == req.team_id, TeamMember.user_id == current_user.id
                ).first()
                if not is_member:
                    raise HTTPException(status_code=403, detail="不是该团队成员")
    # Server passwords default to 90-day expiry
    expire_days = req.expire_days
    if req.category == "server" and expire_days == 0:
        expire_days = 90
    sl = req.security_level
    if sl == "personal":
        req.is_personal = True
    CATEGORY_LABELS = {"website": "网站", "server": "服务器", "database": "数据库", "api_key": "API密钥", "other": "其他"}
    entry = PasswordEntry(
        title=req.title,
        category=req.category,
        security_level=sl,
        username=req.username,
        encrypted_password=encrypt(req.password),
        encrypted_notes=encrypt(req.notes) if req.notes else "",
        url=req.url,
        host=req.host,
        port=req.port,
        db_type=req.db_type,
        db_name=req.db_name,
        api_provider=req.api_provider,
        api_endpoint=req.api_endpoint,
        team_id=req.team_id if not req.is_personal else None,
        created_by=current_user.id,
        is_personal=req.is_personal,
        expire_days=expire_days,
        password_changed_at=datetime.now(timezone.utc),
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    log_action(db, current_user.id, "password.create", "password", entry.id,
               f"创建{CATEGORY_LABELS.get(req.category, '')}密码 {entry.title}")
    return _to_response(entry, db)


@router.post("/{password_id}/decrypt", response_model=PasswordDecryptResponse)
def decrypt_password(
    password_id: int,
    req: DecryptRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # --- 二次验证 ---
    new_token = None
    if req.decrypt_token:
        if not verify_decrypt_token(req.decrypt_token, current_user.id):
            raise HTTPException(status_code=401, detail="解密令牌已过期，请重新验证")
    elif req.password_confirm:
        if not verify_password(req.password_confirm, current_user.hashed_password):
            raise HTTPException(status_code=403, detail="密码验证失败")
        new_token = create_decrypt_token(current_user.id)
    else:
        raise HTTPException(status_code=400, detail="需要密码验证")

    # --- 访问控制（按安全等级） ---
    entry = db.query(PasswordEntry).filter(PasswordEntry.id == password_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="密码不存在")
    can, reason = _can_decrypt(current_user, entry, db)
    if not can:
        raise HTTPException(status_code=403, detail=reason)

    # --- 解密 + 懒迁移 ---
    plaintext_password = decrypt(entry.encrypted_password)
    plaintext_notes = decrypt(entry.encrypted_notes) if entry.encrypted_notes else ""

    new_pw, pw_migrated = migrate_if_needed(entry.encrypted_password)
    new_notes, notes_migrated = migrate_if_needed(entry.encrypted_notes) if entry.encrypted_notes else (entry.encrypted_notes, False)
    if pw_migrated or notes_migrated:
        if pw_migrated:
            entry.encrypted_password = new_pw
        if notes_migrated:
            entry.encrypted_notes = new_notes
        db.commit()

    # --- 审计日志 ---
    ip = request.client.host if request.client else ""
    log_action(db, current_user.id, "password.decrypt", "password", entry.id,
               f"查看密码 {entry.title}", ip)

    return PasswordDecryptResponse(
        id=entry.id,
        title=entry.title,
        username=entry.username,
        password=plaintext_password,
        notes=plaintext_notes,
        url=entry.url,
        host=entry.host or "",
        port=entry.port,
        db_type=entry.db_type or "",
        db_name=entry.db_name or "",
        api_provider=entry.api_provider or "",
        api_endpoint=entry.api_endpoint or "",
        decrypt_token=new_token,
    )


@router.put("/{password_id}", response_model=PasswordResponse)
def update_password(
    password_id: int,
    req: PasswordUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    entry = db.query(PasswordEntry).filter(PasswordEntry.id == password_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="密码不存在")
    if current_user.role == Role.ADMIN:
        pass
    elif entry.created_by == current_user.id and has_permission(current_user.role, "password.edit_team"):
        pass
    else:
        raise HTTPException(status_code=403, detail="权限不足")
    if req.title is not None:
        entry.title = req.title
    if req.category is not None:
        entry.category = req.category
    if req.username is not None:
        entry.username = req.username
    if req.password is not None:
        entry.encrypted_password = encrypt(req.password)
        entry.password_changed_at = datetime.now(timezone.utc)  # reset expiry timer
    if req.notes is not None:
        entry.encrypted_notes = encrypt(req.notes)
    if req.url is not None:
        entry.url = req.url
    if req.host is not None:
        entry.host = req.host
    if req.port is not None:
        entry.port = req.port
    if req.db_type is not None:
        entry.db_type = req.db_type
    if req.db_name is not None:
        entry.db_name = req.db_name
    if req.api_provider is not None:
        entry.api_provider = req.api_provider
    if req.api_endpoint is not None:
        entry.api_endpoint = req.api_endpoint
    if req.expire_days is not None:
        entry.expire_days = req.expire_days
    if req.security_level is not None:
        entry.security_level = req.security_level
        entry.is_personal = (req.security_level == "personal")
    db.commit()
    db.refresh(entry)
    log_action(db, current_user.id, "password.update", "password", entry.id,
               f"更新密码 {entry.title}")
    return _to_response(entry, db)


@router.delete("/{password_id}")
def delete_password(
    password_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    entry = db.query(PasswordEntry).filter(PasswordEntry.id == password_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="密码不存在")
    if current_user.role != Role.ADMIN and entry.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="权限不足")
    log_action(db, current_user.id, "password.delete", "password", entry.id,
               f"删除密码 {entry.title}")
    db.delete(entry)
    db.commit()
    return {"message": "已删除"}


# --- Server password verification ---

@router.post("/{password_id}/verify-server")
def verify_server_password(
    password_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """SSH connect to the server to verify the password is still valid."""
    import paramiko

    entry = db.query(PasswordEntry).filter(PasswordEntry.id == password_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="密码不存在")
    if entry.category != "server":
        raise HTTPException(status_code=400, detail="仅支持服务器类型密码")
    if not _can_access(current_user, entry, db):
        raise HTTPException(status_code=403, detail="无权访问")
    if not entry.host:
        raise HTTPException(status_code=400, detail="未配置主机地址")

    plaintext_password = decrypt(entry.encrypted_password)
    port = entry.port or 22
    username = entry.username or "root"

    now = datetime.now(timezone.utc)
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(
            hostname=entry.host,
            port=port,
            username=username,
            password=plaintext_password,
            timeout=10,
            look_for_keys=False,
            allow_agent=False,
        )
        client.close()
        entry.verify_status = "valid"
        entry.last_verified_at = now
        db.commit()
        log_action(db, current_user.id, "password.verify", "password", entry.id,
                   f"验证服务器密码 {entry.title} - 有效")
        return {"status": "valid", "message": "密码有效，连接成功"}
    except paramiko.AuthenticationException:
        entry.verify_status = "invalid"
        entry.last_verified_at = now
        db.commit()
        log_action(db, current_user.id, "password.verify", "password", entry.id,
                   f"验证服务器密码 {entry.title} - 已失效")
        return {"status": "invalid", "message": "密码已失效，认证失败"}
    except Exception as e:
        entry.verify_status = "error"
        entry.last_verified_at = now
        db.commit()
        return {"status": "error", "message": f"连接失败: {str(e)}"}
    finally:
        client.close()


# --- Sharing ---

@router.post("/{password_id}/share", response_model=ShareResponse)
def share_password(
    password_id: int,
    req: ShareCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    entry = db.query(PasswordEntry).filter(PasswordEntry.id == password_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="密码不存在")
    level = entry.security_level or "low"
    if level == "personal":
        raise HTTPException(status_code=403, detail="个人密码不允许分享")
    if level == "high":
        raise HTTPException(status_code=403, detail="高安全密码不允许分享")
    if level == "medium" and current_user.role != Role.ADMIN:
        raise HTTPException(status_code=403, detail="中安全密码仅Admin可分享，请发起审批")
    if level == "low":
        if not has_permission(current_user.role, "password.share"):
            raise HTTPException(status_code=403, detail="权限不足")
    if current_user.role != Role.ADMIN and entry.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="只能分享自己创建的密码")
    existing = db.query(PasswordShare).filter(
        PasswordShare.password_entry_id == password_id,
        PasswordShare.shared_with_user_id == req.shared_with_user_id,
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="已分享给该用户")
    target_user = db.query(User).filter(User.id == req.shared_with_user_id).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="目标用户不存在")
    share = PasswordShare(
        password_entry_id=password_id,
        shared_with_user_id=req.shared_with_user_id,
        shared_by=current_user.id,
        permission=req.permission,
    )
    db.add(share)
    db.commit()
    db.refresh(share)
    log_action(db, current_user.id, "password.share", "password", password_id,
               f"分享密码 {entry.title} 给 {target_user.username}")
    return ShareResponse(
        id=share.id,
        password_entry_id=share.password_entry_id,
        shared_with_user_id=share.shared_with_user_id,
        shared_with_username=target_user.username,
        shared_by=share.shared_by,
        permission=share.permission,
        created_at=share.created_at,
    )


@router.get("/{password_id}/shares", response_model=List[ShareResponse])
def list_shares(
    password_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    entry = db.query(PasswordEntry).filter(PasswordEntry.id == password_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="密码不存在")
    if not _can_access(current_user, entry, db):
        raise HTTPException(status_code=403, detail="无权访问")
    shares = db.query(PasswordShare).filter(PasswordShare.password_entry_id == password_id).all()
    result = []
    for s in shares:
        target = db.query(User).filter(User.id == s.shared_with_user_id).first()
        sharer = db.query(User).filter(User.id == s.shared_by).first()
        result.append(ShareResponse(
            id=s.id,
            password_entry_id=s.password_entry_id,
            shared_with_user_id=s.shared_with_user_id,
            shared_with_username=target.username if target else "",
            shared_by=s.shared_by,
            shared_by_name=sharer.username if sharer else "",
            permission=s.permission,
            created_at=s.created_at,
        ))
    return result


@router.delete("/{password_id}/share/{share_id}")
def revoke_share(
    password_id: int,
    share_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    share = db.query(PasswordShare).filter(
        PasswordShare.id == share_id, PasswordShare.password_entry_id == password_id
    ).first()
    if not share:
        raise HTTPException(status_code=404, detail="分享记录不存在")
    if current_user.role != Role.ADMIN and share.shared_by != current_user.id:
        raise HTTPException(status_code=403, detail="权限不足")
    db.delete(share)
    db.commit()
    return {"message": "已撤销"}


@router.post("/{password_id}/grant", response_model=ShareResponse)
def grant_access(
    password_id: int,
    req: ShareCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(Role.ADMIN)),
):
    """Admin grants a user access to any password (regardless of security level)."""
    entry = db.query(PasswordEntry).filter(PasswordEntry.id == password_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="密码不存在")
    if entry.security_level == "personal":
        raise HTTPException(status_code=403, detail="个人密码不允许赋权")
    target_user = db.query(User).filter(User.id == req.shared_with_user_id).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="目标用户不存在")
    existing = db.query(PasswordShare).filter(
        PasswordShare.password_entry_id == password_id,
        PasswordShare.shared_with_user_id == req.shared_with_user_id,
    ).first()
    if existing:
        existing.permission = req.permission
        db.commit()
        db.refresh(existing)
        log_action(db, current_user.id, "password.grant", "password", password_id,
                   f"更新 {target_user.username} 对 {entry.title} 的权限为 {req.permission}")
        return ShareResponse(
            id=existing.id, password_entry_id=existing.password_entry_id,
            shared_with_user_id=existing.shared_with_user_id,
            shared_with_username=target_user.username,
            shared_by=existing.shared_by, shared_by_name=current_user.username,
            permission=existing.permission, created_at=existing.created_at,
        )
    share = PasswordShare(
        password_entry_id=password_id,
        shared_with_user_id=req.shared_with_user_id,
        shared_by=current_user.id,
        permission=req.permission,
    )
    db.add(share)
    db.commit()
    db.refresh(share)
    log_action(db, current_user.id, "password.grant", "password", password_id,
               f"授权 {target_user.username} {req.permission} 权限 - {entry.title}")
    return ShareResponse(
        id=share.id, password_entry_id=share.password_entry_id,
        shared_with_user_id=share.shared_with_user_id,
        shared_with_username=target_user.username,
        shared_by=share.shared_by, shared_by_name=current_user.username,
        permission=share.permission, created_at=share.created_at,
    )
