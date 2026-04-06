import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
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
from app.api import auth, users, teams, passwords, audit, ws, approvals, permissions


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
    db = SessionLocal()
    try:
        existing = db.query(User).filter(User.username == "admin").first()
        if not existing:
            admin = User(
                username="admin",
                email="admin@example.com",
                hashed_password=hash_password("admin123"),
                role=Role.ADMIN,
            )
            db.add(admin)
            db.commit()
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


app = FastAPI(title="团队协作密码平台", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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


@app.get("/api/health")
def health():
    return {"status": "ok"}
