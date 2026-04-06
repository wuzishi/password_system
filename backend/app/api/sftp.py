"""SFTP 文件管理 API — 列目录/上传/下载/删除/重命名/创建目录。"""
import asyncio
import logging
import posixpath
import stat
from datetime import datetime, timezone
from io import BytesIO

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.models.password_entry import PasswordEntry
from app.models.password_share import PasswordShare
from app.models.team_member import TeamMember
from app.schemas.sftp import FileItem, FileListResponse, MkdirRequest, RenameRequest
from app.services.crypto_service import decrypt
from app.services.audit_service import log_action
from app.api.deps import get_current_user
from app.api.ws import _get_ssh_client, _ssh_connect
from app.core.security import Role

router = APIRouter(prefix="/api/sftp", tags=["SFTP文件管理"])
logger = logging.getLogger(__name__)

MAX_UPLOAD_SIZE = 100 * 1024 * 1024  # 100MB


def _validate_path(path: str) -> str:
    """校验并规范化远程路径。"""
    if not path or "\x00" in path:
        raise HTTPException(status_code=400, detail="无效路径")
    normalized = posixpath.normpath(path)
    if not normalized.startswith("/"):
        normalized = "/" + normalized
    return normalized


def _has_permission(user: User, entry: PasswordEntry, db: Session) -> bool:
    if entry.created_by == user.id:
        return True
    if user.role == Role.ADMIN:
        return True
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


def _get_entry(password_id: int, user: User, db: Session) -> PasswordEntry:
    entry = db.query(PasswordEntry).filter(PasswordEntry.id == password_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="条目不存在")
    if entry.category != "server":
        raise HTTPException(status_code=400, detail="仅支持服务器类型")
    if not entry.host:
        raise HTTPException(status_code=400, detail="未配置主机地址")
    if not _has_permission(user, entry, db):
        raise HTTPException(status_code=403, detail="无操作权限")
    return entry


def _open_sftp(entry: PasswordEntry):
    """建立 SSH 连接并返回 (sftp, client)。"""
    password = decrypt(entry.encrypted_password)
    client = _get_ssh_client()
    _ssh_connect(client, entry.host, entry.port or 22, entry.username or "root", password)
    sftp = client.open_sftp()
    return sftp, client


def _format_permissions(mode: int) -> str:
    """将 st_mode 转为 rwx 字符串。"""
    perms = ""
    for who in range(2, -1, -1):
        for bit, char in [(4, "r"), (2, "w"), (1, "x")]:
            perms += char if mode & (bit << (who * 3)) else "-"
    return perms


def _format_mtime(ts: float) -> str:
    return datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


# ---- 列目录 ----

@router.get("/{password_id}/list", response_model=FileListResponse)
async def list_directory(
    password_id: int,
    path: str = Query("/", max_length=4096),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    entry = _get_entry(password_id, current_user, db)
    safe_path = _validate_path(path)

    def _list():
        sftp, client = _open_sftp(entry)
        try:
            items = []
            for attr in sftp.listdir_attr(safe_path):
                is_dir = stat.S_ISDIR(attr.st_mode) if attr.st_mode else False
                items.append(FileItem(
                    name=attr.filename,
                    is_dir=is_dir,
                    size=attr.st_size or 0,
                    mtime=_format_mtime(attr.st_mtime) if attr.st_mtime else "",
                    permissions=_format_permissions(attr.st_mode) if attr.st_mode else "",
                ))
            # 目录在前，按名称排序
            items.sort(key=lambda x: (not x.is_dir, x.name.lower()))
            return items
        finally:
            sftp.close()
            client.close()

    loop = asyncio.get_event_loop()
    files = await loop.run_in_executor(None, _list)
    return FileListResponse(path=safe_path, files=files)


# ---- 创建目录 ----

@router.post("/{password_id}/mkdir")
async def make_directory(
    password_id: int,
    req: MkdirRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    entry = _get_entry(password_id, current_user, db)
    safe_path = _validate_path(req.path)

    def _mkdir():
        sftp, client = _open_sftp(entry)
        try:
            sftp.mkdir(safe_path)
        finally:
            sftp.close()
            client.close()

    await asyncio.get_event_loop().run_in_executor(None, _mkdir)
    log_action(db, current_user.id, "sftp.mkdir", "password", password_id, f"创建目录 {safe_path}")
    return {"success": True}


# ---- 重命名 ----

@router.post("/{password_id}/rename")
async def rename_file(
    password_id: int,
    req: RenameRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    entry = _get_entry(password_id, current_user, db)
    old = _validate_path(req.old_path)
    new = _validate_path(req.new_path)

    def _rename():
        sftp, client = _open_sftp(entry)
        try:
            sftp.rename(old, new)
        finally:
            sftp.close()
            client.close()

    await asyncio.get_event_loop().run_in_executor(None, _rename)
    log_action(db, current_user.id, "sftp.rename", "password", password_id, f"重命名 {old} → {new}")
    return {"success": True}


# ---- 删除 ----

@router.delete("/{password_id}/delete")
async def delete_file(
    password_id: int,
    path: str = Query(..., max_length=4096),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    entry = _get_entry(password_id, current_user, db)
    safe_path = _validate_path(path)

    def _delete():
        sftp, client = _open_sftp(entry)
        try:
            st = sftp.stat(safe_path)
            if stat.S_ISDIR(st.st_mode):
                _rmdir_recursive(sftp, safe_path)
            else:
                sftp.remove(safe_path)
        finally:
            sftp.close()
            client.close()

    await asyncio.get_event_loop().run_in_executor(None, _delete)
    log_action(db, current_user.id, "sftp.delete", "password", password_id, f"删除 {safe_path}")
    return {"success": True}


def _rmdir_recursive(sftp, path: str):
    """递归删除目录。"""
    for attr in sftp.listdir_attr(path):
        child = posixpath.join(path, attr.filename)
        if stat.S_ISDIR(attr.st_mode):
            _rmdir_recursive(sftp, child)
        else:
            sftp.remove(child)
    sftp.rmdir(path)


# ---- 下载 ----

@router.get("/{password_id}/download")
async def download_file(
    password_id: int,
    path: str = Query(..., max_length=4096),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    entry = _get_entry(password_id, current_user, db)
    safe_path = _validate_path(path)
    filename = posixpath.basename(safe_path)

    def _read():
        sftp, client = _open_sftp(entry)
        try:
            buf = BytesIO()
            sftp.getfo(safe_path, buf)
            buf.seek(0)
            return buf
        finally:
            sftp.close()
            client.close()

    loop = asyncio.get_event_loop()
    data = await loop.run_in_executor(None, _read)

    log_action(db, current_user.id, "sftp.download", "password", password_id, f"下载 {safe_path}")
    return StreamingResponse(
        data,
        media_type="application/octet-stream",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# ---- 上传 ----

@router.post("/{password_id}/upload")
async def upload_file(
    password_id: int,
    path: str = Query(..., max_length=4096, description="目标目录"),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    entry = _get_entry(password_id, current_user, db)
    safe_dir = _validate_path(path)
    remote_path = posixpath.join(safe_dir, file.filename)

    # 读取文件到内存（限制大小）
    chunks = []
    total = 0
    while True:
        chunk = await file.read(65536)
        if not chunk:
            break
        total += len(chunk)
        if total > MAX_UPLOAD_SIZE:
            raise HTTPException(status_code=413, detail=f"文件大小超过限制 ({MAX_UPLOAD_SIZE // 1024 // 1024}MB)")
        chunks.append(chunk)
    content = b"".join(chunks)

    def _upload():
        sftp, client = _open_sftp(entry)
        try:
            with sftp.open(remote_path, "wb") as f:
                f.write(content)
        finally:
            sftp.close()
            client.close()

    await asyncio.get_event_loop().run_in_executor(None, _upload)
    log_action(db, current_user.id, "sftp.upload", "password", password_id,
               f"上传 {file.filename} → {remote_path} ({total} bytes)")
    return {"success": True, "name": file.filename, "size": total, "path": remote_path}
