import json
import time
import string
import secrets
import threading
from datetime import datetime, timezone

import paramiko
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.user import User
from app.models.password_entry import PasswordEntry
from app.services.auth_service import decode_token
from app.services.crypto_service import encrypt, decrypt
from app.services.audit_service import log_action

router = APIRouter(prefix="/api/ws", tags=["WebSocket"])


def _auth_ws(token: str, db: Session) -> User | None:
    payload = decode_token(token)
    if not payload:
        return None
    user_id = payload.get("sub")
    if not user_id:
        return None
    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user or not user.is_active:
        return None
    return user


def _generate_strong_password(length: int = 20) -> str:
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    while True:
        pwd = ''.join(secrets.choice(alphabet) for _ in range(length))
        if (any(c.islower() for c in pwd) and any(c.isupper() for c in pwd)
                and any(c.isdigit() for c in pwd) and any(c in "!@#$%^&*" for c in pwd)):
            return pwd


def _read_until(channel, patterns: list[str], timeout: float = 30) -> str:
    """Read from SSH channel until one of the patterns is found."""
    buf = ""
    start = time.time()
    while time.time() - start < timeout:
        if channel.recv_ready():
            chunk = channel.recv(4096).decode("utf-8", errors="replace")
            buf += chunk
            for p in patterns:
                if p.lower() in buf.lower():
                    return buf
        time.sleep(0.1)
    return buf


# ---- Change Password WebSocket ----

@router.websocket("/change-password/{password_id}")
async def ws_change_password(websocket: WebSocket, password_id: int, token: str = ""):
    await websocket.accept()
    db = SessionLocal()

    try:
        # Auth
        user = _auth_ws(token, db)
        if not user:
            await websocket.send_json({"type": "error", "data": "认证失败"})
            await websocket.close()
            return

        entry = db.query(PasswordEntry).filter(PasswordEntry.id == password_id).first()
        if not entry or entry.category != "server" or not entry.host:
            await websocket.send_json({"type": "error", "data": "无效的服务器密码条目"})
            await websocket.close()
            return

        # Wait for client to send start command
        msg = await websocket.receive_json()
        new_password = msg.get("new_password") or _generate_strong_password()
        await websocket.send_json({"type": "new_password", "data": new_password})

        old_password = decrypt(entry.encrypted_password)
        host = entry.host
        port = entry.port or 22
        username = entry.username or "root"

        # Step 1: Connect
        await websocket.send_json({"type": "output", "data": f"[1/5] 连接服务器 {host}:{port} ...\r\n"})
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            client.connect(hostname=host, port=port, username=username,
                           password=old_password, timeout=10,
                           look_for_keys=False, allow_agent=False)
        except paramiko.AuthenticationException:
            await websocket.send_json({"type": "output", "data": "[错误] 当前密码认证失败，无法��接\r\n"})
            await websocket.send_json({"type": "status", "data": "failed"})
            return
        except Exception as e:
            await websocket.send_json({"type": "output", "data": f"[错误] 连接失败: {e}\r\n"})
            await websocket.send_json({"type": "status", "data": "failed"})
            return

        await websocket.send_json({"type": "output", "data": "[1/5] 连接成功 ✓\r\n"})

        # Step 2: Open shell and run passwd
        await websocket.send_json({"type": "output", "data": f"[2/5] 执行 passwd 命令 (用户: {username}) ...\r\n"})
        channel = client.invoke_shell()
        time.sleep(0.5)
        # Clear initial banner
        if channel.recv_ready():
            channel.recv(4096)

        # Determine if root (root doesn't need current password)
        is_root = (username == "root")

        if is_root:
            channel.send(f"passwd {username}\n")
        else:
            channel.send("passwd\n")
        time.sleep(0.5)

        # For non-root, enter current password
        if not is_root:
            output = _read_until(channel, ["current", "old", "(current)", "密码"], timeout=10)
            await websocket.send_json({"type": "output", "data": f"  > {output.strip()}\r\n"})
            channel.send(old_password + "\n")
            time.sleep(0.5)

        # Enter new password
        output = _read_until(channel, ["new", "新"], timeout=10)
        await websocket.send_json({"type": "output", "data": f"  > {output.strip()}\r\n"})
        await websocket.send_json({"type": "output", "data": "[3/5] 输入新密码 ...\r\n"})
        channel.send(new_password + "\n")
        time.sleep(0.5)

        # Retype new password
        output = _read_until(channel, ["retype", "re-enter", "again", "重新", "确认", "new"], timeout=10)
        await websocket.send_json({"type": "output", "data": f"  > {output.strip()}\r\n"})
        channel.send(new_password + "\n")
        time.sleep(1)

        # Check result
        output = _read_until(channel, ["success", "updated", "已更新", "password:", "$", "#"], timeout=10)
        await websocket.send_json({"type": "output", "data": f"  > {output.strip()}\r\n"})

        channel.close()
        client.close()

        passwd_success = any(kw in output.lower() for kw in ["success", "updated", "已更新"])
        if not passwd_success:
            # Could still have succeeded, verify with new password
            pass

        # Step 4: Verify with new password
        await websocket.send_json({"type": "output", "data": "[4/5] 用新��码验证连接 ...\r\n"})
        verify_client = paramiko.SSHClient()
        verify_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            verify_client.connect(hostname=host, port=port, username=username,
                                  password=new_password, timeout=10,
                                  look_for_keys=False, allow_agent=False)
            verify_client.close()
            await websocket.send_json({"type": "output", "data": "[4/5] 新密码验证成功 ✓\r\n"})
        except paramiko.AuthenticationException:
            await websocket.send_json({"type": "output", "data": "[4/5] 新密码验证失败 ✗\r\n"})
            await websocket.send_json({"type": "output", "data": "[回滚] 密码可能未修改成功，数据库不更新\r\n"})
            await websocket.send_json({"type": "status", "data": "failed"})
            return
        except Exception as e:
            await websocket.send_json({"type": "output", "data": f"[4/5] 验证连接异常: {e}\r\n"})
            await websocket.send_json({"type": "status", "data": "failed"})
            return

        # Step 5: Update database
        await websocket.send_json({"type": "output", "data": "[5/5] 更新数据库记录 ...\r\n"})
        entry.encrypted_password = encrypt(new_password)
        entry.password_changed_at = datetime.now(timezone.utc)
        entry.verify_status = "valid"
        entry.last_verified_at = datetime.now(timezone.utc)
        db.commit()

        log_action(db, user.id, "password.change_server", "password", entry.id,
                   f"远程修改服务器密码 {entry.title} ({host})")

        await websocket.send_json({"type": "output", "data": "[5/5] 数据库已更新 ✓\r\n\r\n密码修改完成！\r\n"})
        await websocket.send_json({"type": "status", "data": "success"})

    except WebSocketDisconnect:
        pass
    except Exception as e:
        try:
            await websocket.send_json({"type": "error", "data": str(e)})
        except:
            pass
    finally:
        db.close()


# ---- SSH Terminal WebSocket ----

@router.websocket("/terminal/{password_id}")
async def ws_terminal(websocket: WebSocket, password_id: int, token: str = ""):
    await websocket.accept()
    db = SessionLocal()

    try:
        user = _auth_ws(token, db)
        if not user:
            await websocket.send_text("\r\n认证失败\r\n")
            await websocket.close()
            return

        entry = db.query(PasswordEntry).filter(PasswordEntry.id == password_id).first()
        if not entry or entry.category != "server" or not entry.host:
            await websocket.send_text("\r\n无效的服务��条目\r\n")
            await websocket.close()
            return

        password = decrypt(entry.encrypted_password)
        host = entry.host
        port = entry.port or 22
        username = entry.username or "root"

        log_action(db, user.id, "terminal.open", "password", entry.id,
                   f"打开终端 {entry.title} ({host})")
        db.close()
        db = None

        # SSH connect
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            client.connect(hostname=host, port=port, username=username,
                           password=password, timeout=10,
                           look_for_keys=False, allow_agent=False)
        except Exception as e:
            await websocket.send_text(f"\r\nSSH 连接失败: {e}\r\n")
            await websocket.close()
            return

        channel = client.invoke_shell(term="xterm-256color", width=120, height=40)
        channel.setblocking(0)

        # Read SSH output and send to browser
        stop_event = threading.Event()

        async def read_ssh():
            while not stop_event.is_set():
                try:
                    if channel.recv_ready():
                        data = channel.recv(4096)
                        if data:
                            await websocket.send_bytes(data)
                    else:
                        import asyncio
                        await asyncio.sleep(0.02)
                except:
                    break

        import asyncio
        read_task = asyncio.create_task(read_ssh())

        # Read browser input and send to SSH
        try:
            while True:
                msg = await websocket.receive()
                if msg.get("type") == "websocket.disconnect":
                    break
                if "text" in msg:
                    text = msg["text"]
                    # Handle resize
                    if text.startswith('{"resize":'):
                        try:
                            data = json.loads(text)
                            channel.resize_pty(
                                width=data["resize"]["cols"],
                                height=data["resize"]["rows"],
                            )
                        except:
                            pass
                    else:
                        channel.send(text)
                elif "bytes" in msg:
                    channel.send(msg["bytes"])
        except WebSocketDisconnect:
            pass
        finally:
            stop_event.set()
            read_task.cancel()
            channel.close()
            client.close()

    except WebSocketDisconnect:
        pass
    except Exception as e:
        try:
            await websocket.send_text(f"\r\n错误: {e}\r\n")
        except:
            pass
    finally:
        if db:
            db.close()
