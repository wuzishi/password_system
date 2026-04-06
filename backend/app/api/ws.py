import asyncio
import json
import time
import string
import secrets
import logging
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
logger = logging.getLogger(__name__)


# ---- Security helpers ----

def _get_ssh_client() -> paramiko.SSHClient:
    """创建带安全策略的 SSH client。"""
    client = paramiko.SSHClient()
    # 使用 WarningPolicy 而非 AutoAddPolicy，记录未知 host key 到日志
    client.set_missing_host_key_policy(paramiko.WarningPolicy())
    # 尝试加载系统 known_hosts
    try:
        client.load_system_host_keys()
    except Exception:
        pass
    return client


def _ssh_connect(client: paramiko.SSHClient, host: str, port: int,
                 username: str, password: str, timeout: int = 10):
    """安全 SSH 连接，禁用密钥和 agent。"""
    client.connect(
        hostname=host, port=port, username=username,
        password=password, timeout=timeout,
        look_for_keys=False, allow_agent=False,
        banner_timeout=10, auth_timeout=10,
    )


def _auth_ws(token: str, db: Session) -> User | None:
    if not token or len(token) > 2000:
        return None
    payload = decode_token(token)
    if not payload:
        return None
    user_id = payload.get("sub")
    if not user_id:
        return None
    try:
        uid = int(user_id)
    except (ValueError, TypeError):
        return None
    user = db.query(User).filter(User.id == uid).first()
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
            lower_buf = buf.lower()
            for p in patterns:
                if p.lower() in lower_buf:
                    return buf
        time.sleep(0.1)
    return buf


# ---- Change Password WebSocket ----

@router.websocket("/change-password/{password_id}")
async def ws_change_password(websocket: WebSocket, password_id: int, token: str = ""):
    await websocket.accept()
    db = SessionLocal()
    old_password = None
    new_password = None

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
        client = _get_ssh_client()
        try:
            _ssh_connect(client, host, port, username, old_password)
        except paramiko.AuthenticationException:
            await websocket.send_json({"type": "output", "data": "[错误] 当前密码认证失败\r\n"})
            await websocket.send_json({"type": "status", "data": "failed"})
            log_action(db, user.id, "password.change_fail", "password", entry.id,
                       f"远程改密失败: 认证失败 {host}")
            return
        except Exception:
            logger.exception(f"SSH connect failed to {host}:{port}")
            await websocket.send_json({"type": "output", "data": "[错误] 连接失败，请检查网络和主机地址\r\n"})
            await websocket.send_json({"type": "status", "data": "failed"})
            return

        await websocket.send_json({"type": "output", "data": "[1/5] 连接成功\r\n"})

        # Step 2: Open shell and run passwd
        await websocket.send_json({"type": "output", "data": f"[2/5] 执行 passwd 命令 (用户: {username}) ...\r\n"})
        channel = client.invoke_shell()
        time.sleep(0.5)
        if channel.recv_ready():
            channel.recv(4096)

        is_root = (username == "root")
        if is_root:
            channel.send(f"passwd {username}\n")
        else:
            channel.send("passwd\n")
        time.sleep(0.5)

        if not is_root:
            output = _read_until(channel, ["current", "old", "(current)", "密码"], timeout=10)
            await websocket.send_json({"type": "output", "data": f"  > {output.strip()}\r\n"})
            channel.send(old_password + "\n")
            time.sleep(0.5)

        output = _read_until(channel, ["new", "新"], timeout=10)
        await websocket.send_json({"type": "output", "data": f"  > {output.strip()}\r\n"})
        await websocket.send_json({"type": "output", "data": "[3/5] 输入新密码 ...\r\n"})
        channel.send(new_password + "\n")
        time.sleep(0.5)

        output = _read_until(channel, ["retype", "re-enter", "again", "重新", "确认", "new"], timeout=10)
        await websocket.send_json({"type": "output", "data": f"  > {output.strip()}\r\n"})
        channel.send(new_password + "\n")
        time.sleep(1)

        output = _read_until(channel, ["success", "updated", "已更新", "password:", "$", "#"], timeout=10)
        await websocket.send_json({"type": "output", "data": f"  > {output.strip()}\r\n"})

        channel.close()
        client.close()

        # Step 4: Verify with new password
        await websocket.send_json({"type": "output", "data": "[4/5] 用新密码验证连接 ...\r\n"})
        verify_client = _get_ssh_client()
        try:
            _ssh_connect(verify_client, host, port, username, new_password)
            verify_client.close()
            await websocket.send_json({"type": "output", "data": "[4/5] 新密码验证成功\r\n"})
        except paramiko.AuthenticationException:
            await websocket.send_json({"type": "output", "data": "[4/5] 新密码验证失败\r\n"})
            await websocket.send_json({"type": "output", "data": "[回滚] 密码可能未修改成功，数据库不更新\r\n"})
            await websocket.send_json({"type": "status", "data": "failed"})
            log_action(db, user.id, "password.change_fail", "password", entry.id,
                       f"远程改密: 新密码验证失败 {host}")
            return
        except Exception:
            logger.exception(f"SSH verify failed to {host}:{port}")
            await websocket.send_json({"type": "output", "data": "[4/5] 验证连接异常\r\n"})
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

        await websocket.send_json({"type": "output", "data": "[5/5] 数据库已更新\r\n\r\n密码修改完成！\r\n"})
        await websocket.send_json({"type": "status", "data": "success"})

    except WebSocketDisconnect:
        pass
    except Exception:
        logger.exception("ws_change_password error")
        try:
            await websocket.send_json({"type": "error", "data": "服务器内部错误"})
        except Exception:
            pass
    finally:
        # 安全擦除内存中的明文密码
        if old_password:
            del old_password
        if new_password:
            del new_password
        db.close()


# ---- Change Database Password WebSocket ----

@router.websocket("/change-db-password/{password_id}")
async def ws_change_db_password(websocket: WebSocket, password_id: int, token: str = ""):
    await websocket.accept()
    db = SessionLocal()

    async def out(text: str):
        await websocket.send_json({"type": "output", "data": text})

    try:
        user = _auth_ws(token, db)
        if not user:
            await websocket.send_json({"type": "error", "data": "认证失败"})
            await websocket.close()
            return

        entry = db.query(PasswordEntry).filter(PasswordEntry.id == password_id).first()
        if not entry or entry.category != "database" or not entry.host:
            await websocket.send_json({"type": "error", "data": "无效的数据库密码条目"})
            await websocket.close()
            return

        msg = await websocket.receive_json()
        new_password = msg.get("new_password") or _generate_strong_password()
        await websocket.send_json({"type": "new_password", "data": new_password})

        old_password = decrypt(entry.encrypted_password)
        host = entry.host
        username = entry.username or "root"
        db_type = (entry.db_type or "mysql").lower()
        db_name = entry.db_name or ""

        if db_type in ("mysql", "mariadb"):
            await _change_mysql_password(websocket, out, entry, db, user,
                                         host, entry.port or 3306, username,
                                         old_password, new_password, db_name)
        elif db_type in ("postgresql", "postgres", "pg"):
            await _change_pg_password(websocket, out, entry, db, user,
                                      host, entry.port or 5432, username,
                                      old_password, new_password, db_name)
        else:
            await out(f"[错误] 不支持在线改密的数据库类型: {db_type}\r\n")
            await websocket.send_json({"type": "status", "data": "failed"})

    except WebSocketDisconnect:
        pass
    except Exception:
        logger.exception("ws_change_db_password error")
        try:
            await websocket.send_json({"type": "error", "data": "服务器内部错误"})
        except Exception:
            pass
    finally:
        db.close()


async def _change_mysql_password(websocket, out, entry, db, user,
                                  host, port, username, old_password, new_password, db_name):
    """MySQL/MariaDB 在线改密 — 实时展示每条 SQL。"""
    import pymysql
    import asyncio

    prompt = f"mysql> "
    banner = f"MySQL [{host}:{port}]"

    await out(f"$ mysql -h {host} -P {port} -u {username} -p\r\n")
    await out(f"Enter password: ********\r\n")
    await asyncio.sleep(0.3)

    # Step 1: Connect
    try:
        conn = pymysql.connect(host=host, port=port, user=username,
                               password=old_password, database=db_name or None,
                               connect_timeout=10)
    except pymysql.err.OperationalError as e:
        err = str(e)
        await out(f"ERROR {err}\r\n")
        await websocket.send_json({"type": "status", "data": "failed"})
        return
    except Exception as e:
        await out(f"ERROR: 连接失败 - {type(e).__name__}\r\n")
        await websocket.send_json({"type": "status", "data": "failed"})
        return

    cursor = conn.cursor()

    # 获取版本
    cursor.execute("SELECT VERSION()")
    version = cursor.fetchone()[0]
    await out(f"Welcome to the MySQL monitor.  Server version: {version}\r\n")
    await out(f"Connection id: {conn.thread_id()}\r\n\r\n")
    await asyncio.sleep(0.2)

    # Step 2: 查看当前用户
    sql_cmd = "SELECT CURRENT_USER();"
    await out(f"{prompt}{sql_cmd}\r\n")
    await asyncio.sleep(0.2)
    cursor.execute("SELECT CURRENT_USER()")
    current_user = cursor.fetchone()[0]
    await out(f"+----------------+\r\n")
    await out(f"| CURRENT_USER() |\r\n")
    await out(f"+----------------+\r\n")
    await out(f"| {current_user:<14} |\r\n")
    await out(f"+----------------+\r\n")
    await out(f"1 row in set\r\n\r\n")
    await asyncio.sleep(0.3)

    # Step 3: ALTER USER
    alter_sql = f"ALTER USER '{username}'@'%' IDENTIFIED BY '***新密码***';"
    await out(f"{prompt}{alter_sql}\r\n")
    await asyncio.sleep(0.3)
    try:
        cursor.execute("ALTER USER %s@'%%' IDENTIFIED BY %s", (username, new_password))
        await out(f"Query OK, 0 rows affected\r\n\r\n")
    except Exception as e:
        await out(f"ERROR: {e}\r\n")
        cursor.close()
        conn.close()
        await websocket.send_json({"type": "status", "data": "failed"})
        return
    await asyncio.sleep(0.2)

    # Step 4: FLUSH PRIVILEGES
    flush_sql = "FLUSH PRIVILEGES;"
    await out(f"{prompt}{flush_sql}\r\n")
    await asyncio.sleep(0.2)
    try:
        cursor.execute("FLUSH PRIVILEGES")
        await out(f"Query OK, 0 rows affected\r\n\r\n")
    except Exception as e:
        await out(f"ERROR: {e}\r\n")

    await asyncio.sleep(0.2)

    # Step 5: 验证 — 查看用户信息
    check_sql = f"SELECT user, host, password_expired FROM mysql.user WHERE user='{username}';"
    await out(f"{prompt}{check_sql}\r\n")
    await asyncio.sleep(0.2)
    try:
        cursor.execute("SELECT user, host, password_expired FROM mysql.user WHERE user=%s", (username,))
        rows = cursor.fetchall()
        await out(f"+{'-'*12}+{'-'*8}+{'-'*18}+\r\n")
        await out(f"| {'user':<10} | {'host':<6} | {'password_expired':<16} |\r\n")
        await out(f"+{'-'*12}+{'-'*8}+{'-'*18}+\r\n")
        for row in rows:
            await out(f"| {str(row[0]):<10} | {str(row[1]):<6} | {str(row[2]):<16} |\r\n")
        await out(f"+{'-'*12}+{'-'*8}+{'-'*18}+\r\n")
        await out(f"{len(rows)} row(s) in set\r\n\r\n")
    except Exception:
        await out(f"(跳过用户表查询)\r\n\r\n")

    cursor.close()
    conn.close()
    await asyncio.sleep(0.2)

    # Step 6: 用新密码重新连接验证
    await out(f"{prompt}\\q\r\nBye\r\n\r\n")
    await asyncio.sleep(0.3)
    await out(f"$ mysql -h {host} -P {port} -u {username} -p\r\n")
    await out(f"Enter password: ********  (使用新密码)\r\n")
    await asyncio.sleep(0.3)

    try:
        verify_conn = pymysql.connect(host=host, port=port, user=username,
                                      password=new_password, connect_timeout=10)
        v_cursor = verify_conn.cursor()
        v_cursor.execute("SELECT 1 AS connection_test")
        v_cursor.fetchone()
        await out(f"Welcome to the MySQL monitor.  Server version: {version}\r\n\r\n")
        await out(f"{prompt}SELECT 1 AS connection_test;\r\n")
        await out(f"+-----------------+\r\n")
        await out(f"| connection_test  |\r\n")
        await out(f"+-----------------+\r\n")
        await out(f"| 1               |\r\n")
        await out(f"+-----------------+\r\n")
        await out(f"1 row in set\r\n\r\n")
        await out(f"{prompt}\\q\r\nBye\r\n\r\n")
        v_cursor.close()
        verify_conn.close()
    except Exception as e:
        await out(f"ERROR: 新密码连接失败 - {e}\r\n")
        await out(f"[回滚] 密码可能未修改成功，数据库记录不更新\r\n")
        log_action(db, user.id, "password.change_db_fail", "password", entry.id,
                   f"数据库改密失败(验证): {entry.title} ({host})")
        await websocket.send_json({"type": "status", "data": "failed"})
        return

    await asyncio.sleep(0.2)

    # Step 7: 更新系统记录
    await out(f"-- 更新密码管理平台记录 --\r\n")
    await out(f"UPDATE password_entries SET encrypted_password='***', verify_status='valid' WHERE id={entry.id};\r\n")
    await asyncio.sleep(0.2)
    entry.encrypted_password = encrypt(new_password)
    entry.password_changed_at = datetime.now(timezone.utc)
    entry.verify_status = "valid"
    entry.last_verified_at = datetime.now(timezone.utc)
    db.commit()
    await out(f"Query OK, 1 row affected\r\n\r\n")

    log_action(db, user.id, "password.change_db", "password", entry.id,
               f"远程修改数据库密码 {entry.title} ({host})")

    await out(f"✓ 密码修改完成！新密码已同步到平台。\r\n")
    await websocket.send_json({"type": "status", "data": "success"})


async def _change_pg_password(websocket, out, entry, db, user,
                               host, port, username, old_password, new_password, db_name):
    """PostgreSQL 在线改密 — 实时展示每条 SQL。"""
    import asyncio
    connect_db = db_name or "postgres"

    await out(f"$ psql -h {host} -p {port} -U {username} -d {connect_db}\r\n")
    await out(f"Password: ********\r\n")
    await asyncio.sleep(0.3)

    try:
        import psycopg2
        from psycopg2 import sql as pg_sql
        conn = psycopg2.connect(host=host, port=port, user=username,
                                password=old_password, dbname=connect_db,
                                connect_timeout=10)
        conn.autocommit = True
    except Exception as e:
        err = str(e).strip()
        await out(f"psql: error: {err}\r\n")
        await websocket.send_json({"type": "status", "data": "failed"})
        return

    cursor = conn.cursor()

    # 版本
    cursor.execute("SELECT version()")
    pg_version = cursor.fetchone()[0].split(",")[0]
    await out(f"psql ({pg_version})\r\n")
    await out(f'Type "help" for help.\r\n\r\n')
    await asyncio.sleep(0.2)

    prompt = f"{connect_db}=# "

    # 查看当前用户
    await out(f"{prompt}SELECT current_user, inet_server_addr(), inet_server_port();\r\n")
    await asyncio.sleep(0.2)
    cursor.execute("SELECT current_user, inet_server_addr(), inet_server_port()")
    row = cursor.fetchone()
    await out(f" current_user | inet_server_addr | inet_server_port\r\n")
    await out(f"--------------+-----------------+------------------\r\n")
    await out(f" {str(row[0]):<12} | {str(row[1] or host):<15} | {str(row[2] or port):<16}\r\n")
    await out(f"(1 row)\r\n\r\n")
    await asyncio.sleep(0.3)

    # ALTER ROLE
    alter_display = f"ALTER ROLE {username} WITH PASSWORD '***新密码***';"
    await out(f"{prompt}{alter_display}\r\n")
    await asyncio.sleep(0.3)
    try:
        cursor.execute(
            pg_sql.SQL("ALTER ROLE {} WITH PASSWORD %s").format(pg_sql.Identifier(username)),
            (new_password,)
        )
        await out(f"ALTER ROLE\r\n\r\n")
    except Exception as e:
        await out(f"ERROR: {e}\r\n")
        cursor.close()
        conn.close()
        await websocket.send_json({"type": "status", "data": "failed"})
        return
    await asyncio.sleep(0.2)

    # 查看角色信息
    await out(f"{prompt}\\du {username}\r\n")
    await asyncio.sleep(0.2)
    try:
        cursor.execute("SELECT rolname, rolsuper, rolcanlogin FROM pg_roles WHERE rolname=%s", (username,))
        row = cursor.fetchone()
        if row:
            await out(f"                       List of roles\r\n")
            await out(f" Role name | Superuser | Can login\r\n")
            await out(f"-----------+-----------+-----------\r\n")
            await out(f" {str(row[0]):<9} | {'yes' if row[1] else 'no':<9} | {'yes' if row[2] else 'no':<9}\r\n")
            await out(f"(1 row)\r\n\r\n")
    except Exception:
        pass

    cursor.close()
    conn.close()
    await asyncio.sleep(0.2)

    # 用新密码重连验证
    await out(f"{prompt}\\q\r\n\r\n")
    await asyncio.sleep(0.3)
    await out(f"$ psql -h {host} -p {port} -U {username} -d {connect_db}\r\n")
    await out(f"Password: ********  (使用新密码)\r\n")
    await asyncio.sleep(0.3)

    try:
        verify_conn = psycopg2.connect(host=host, port=port, user=username,
                                       password=new_password, dbname=connect_db,
                                       connect_timeout=10)
        verify_conn.autocommit = True
        v_cursor = verify_conn.cursor()
        v_cursor.execute("SELECT 1 AS connection_test")
        v_cursor.fetchone()
        await out(f"psql ({pg_version})\r\n\r\n")
        await out(f"{prompt}SELECT 1 AS connection_test;\r\n")
        await out(f" connection_test\r\n")
        await out(f"-----------------\r\n")
        await out(f"               1\r\n")
        await out(f"(1 row)\r\n\r\n")
        await out(f"{prompt}\\q\r\n\r\n")
        v_cursor.close()
        verify_conn.close()
    except Exception as e:
        await out(f"psql: error: {e}\r\n")
        await out(f"[回滚] 密码可能未修改成功，数据库记录不更新\r\n")
        log_action(db, user.id, "password.change_db_fail", "password", entry.id,
                   f"数据库改密失败(验证): {entry.title} ({host})")
        await websocket.send_json({"type": "status", "data": "failed"})
        return

    await asyncio.sleep(0.2)

    # 更新系统记录
    await out(f"-- 更新密码管理平台记录 --\r\n")
    await out(f"UPDATE password_entries SET encrypted_password='***', verify_status='valid' WHERE id={entry.id};\r\n")
    await asyncio.sleep(0.2)
    entry.encrypted_password = encrypt(new_password)
    entry.password_changed_at = datetime.now(timezone.utc)
    entry.verify_status = "valid"
    entry.last_verified_at = datetime.now(timezone.utc)
    db.commit()
    await out(f"UPDATE 1\r\n\r\n")

    log_action(db, user.id, "password.change_db", "password", entry.id,
               f"远程修改数据库密码 {entry.title} ({host})")

    await out(f"✓ 密码修改完成！新密码已同步到平台。\r\n")
    await websocket.send_json({"type": "status", "data": "success"})


# ---- SSH Terminal WebSocket ----

@router.websocket("/terminal/{password_id}")
async def ws_terminal(websocket: WebSocket, password_id: int, token: str = ""):
    await websocket.accept()
    db = SessionLocal()
    password = None

    try:
        user = _auth_ws(token, db)
        if not user:
            await websocket.send_text("\r\n认证失败\r\n")
            await websocket.close()
            return

        entry = db.query(PasswordEntry).filter(PasswordEntry.id == password_id).first()
        if not entry or entry.category != "server" or not entry.host:
            await websocket.send_text("\r\n无效的服务器条目\r\n")
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
        client = _get_ssh_client()
        try:
            _ssh_connect(client, host, port, username, password)
        except Exception:
            logger.exception(f"Terminal SSH connect failed to {host}:{port}")
            await websocket.send_text("\r\nSSH 连接失败，请检查主机地址和密码\r\n")
            await websocket.close()
            return
        finally:
            # 连接后立即擦除密码
            if password:
                del password
                password = None

        channel = client.invoke_shell(term="xterm-256color", width=120, height=40)
        channel.settimeout(0.1)

        output_queue = asyncio.Queue()
        stop_event = threading.Event()

        def ssh_reader():
            while not stop_event.is_set():
                try:
                    if channel.recv_ready():
                        data = channel.recv(4096)
                        if data:
                            output_queue.put_nowait(data)
                    else:
                        time.sleep(0.02)
                except Exception:
                    break

        reader_thread = threading.Thread(target=ssh_reader, daemon=True)
        reader_thread.start()

        async def send_output():
            while not stop_event.is_set():
                try:
                    data = await asyncio.wait_for(output_queue.get(), timeout=0.1)
                    await websocket.send_bytes(data)
                except asyncio.TimeoutError:
                    continue
                except Exception:
                    break

        send_task = asyncio.create_task(send_output())

        try:
            while True:
                msg = await websocket.receive()
                if msg.get("type") == "websocket.disconnect":
                    break
                if "text" in msg:
                    text = msg["text"]
                    if text.startswith('{"resize":'):
                        try:
                            data = json.loads(text)
                            cols = min(max(data["resize"]["cols"], 10), 500)
                            rows = min(max(data["resize"]["rows"], 5), 200)
                            channel.resize_pty(width=cols, height=rows)
                        except Exception:
                            pass
                    else:
                        # 限制单次输入长度，防止注入超大数据
                        channel.send(text[:4096])
                elif "bytes" in msg:
                    channel.send(msg["bytes"][:4096])
        except WebSocketDisconnect:
            pass
        finally:
            stop_event.set()
            send_task.cancel()
            try:
                reader_thread.join(timeout=2)
            except Exception:
                pass
            channel.close()
            client.close()

    except WebSocketDisconnect:
        pass
    except Exception:
        logger.exception("ws_terminal error")
        try:
            await websocket.send_text("\r\n服务器内部错误\r\n")
        except Exception:
            pass
    finally:
        if password:
            del password
        if db:
            db.close()
