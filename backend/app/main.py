import asyncio
import logging
import os
import secrets
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from app.database import engine, Base, SessionLocal
from app.models.user import User
from app.models.team import Team
from app.models.team_member import TeamMember
from app.models.password_entry import PasswordEntry
from app.models.password_share import PasswordShare
from app.models.audit_log import AuditLog
from app.models.approval import ApprovalRequest
from app.models.invitation import Invitation
from app.models.role_permission import RolePermission, ALL_PERMISSIONS, DEFAULT_PERMISSIONS
from app.services.auth_service import hash_password
from app.core.security import Role
from app.api import auth, users, teams, passwords, audit, ws, approvals, permissions, sftp


logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    _create_default_admin()
    _init_default_permissions()
    from app.services.scheduler import scheduler_loop
    task = asyncio.create_task(scheduler_loop())
    yield
    task.cancel()


def _create_default_admin():
    from app.config import settings as cfg

    db = SessionLocal()
    try:
        existing = db.query(User).filter(User.username == "admin").first()
        if not existing:
            password = cfg.ADMIN_PASSWORD or secrets.token_urlsafe(16)
            admin = User(
                username="admin",
                email="admin@example.com",
                hashed_password=hash_password(password),
                role=Role.ADMIN,
            )
            db.add(admin)
            db.commit()
            if not cfg.ADMIN_PASSWORD:
                logging.warning("=" * 50)
                logging.warning(f"  初始管理员密码（请立即修改）: {password}")
                logging.warning("=" * 50)
            else:
                logging.info("已使用 ADMIN_PASSWORD 创建管理员账号")
    finally:
        db.close()


def _init_default_permissions():
    db = SessionLocal()
    try:
        existing_count = db.query(RolePermission).count()
        if existing_count > 0:
            return  # Already initialized
        for role, perm_keys in DEFAULT_PERMISSIONS.items():
            for key, _ in ALL_PERMISSIONS:
                perm = RolePermission(
                    role=role,
                    permission_key=key,
                    enabled=(key in perm_keys),
                )
                db.add(perm)
        db.commit()
        logging.info("Default permissions initialized")
    finally:
        db.close()


limiter = Limiter(key_func=get_remote_address)
_docs_enabled = os.getenv("DOCS_ENABLED", "").lower() == "true"
app = FastAPI(
    title="团队协作密码平台",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs" if _docs_enabled else None,
    redoc_url="/redoc" if _docs_enabled else None,
    openapi_url="/openapi.json" if _docs_enabled else None,
)
app.state.limiter = limiter


@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(status_code=429, content={"detail": "请求过于频繁，请稍后再试"})


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """全局异常处理：不向客户端暴露内部错误详情，但放行 HTTPException。"""
    from fastapi.exceptions import HTTPException as FastAPIHTTPException
    from starlette.exceptions import HTTPException as StarletteHTTPException
    if isinstance(exc, (FastAPIHTTPException, StarletteHTTPException)):
        raise exc
    logging.error(f"Unhandled error on {request.method} {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(status_code=500, content={"detail": "服务器内部错误"})


from app.config import settings as app_settings
from app.middleware.security import SecurityHeadersMiddleware

app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=app_settings.get_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(teams.router)
app.include_router(passwords.router)
app.include_router(audit.router)
app.include_router(ws.router)
app.include_router(approvals.router)
app.include_router(permissions.router)
app.include_router(sftp.router)


@app.get("/api/health")
def health():
    return {"status": "ok"}
