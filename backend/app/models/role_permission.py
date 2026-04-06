from sqlalchemy import Column, Integer, String, Boolean, UniqueConstraint
from app.database import Base


class RolePermission(Base):
    __tablename__ = "role_permissions"

    id = Column(Integer, primary_key=True, index=True)
    role = Column(String(20), nullable=False, index=True)
    permission_key = Column(String(100), nullable=False)
    enabled = Column(Boolean, default=False)

    __table_args__ = (UniqueConstraint("role", "permission_key", name="uq_role_perm"),)


# All permission keys with labels
ALL_PERMISSIONS = [
    ("page.dashboard", "工作台"),
    ("page.passwords", "密码库"),
    ("page.servers", "服务器管理"),
    ("page.teams", "团队管理"),
    ("page.approvals", "审批管理"),
    ("page.users", "用户管理"),
    ("page.audit", "审计日志"),
    ("page.permissions", "权限管理"),
    ("func.password.create", "创建密码"),
    ("func.password.share", "分享/授权密码"),
    ("func.password.delete", "删除密码"),
    ("func.server.terminal", "打开终端"),
    ("func.server.change_pwd", "远程改密"),
    ("func.team.manage", "管理团队成员"),
]

# Default permissions per role
DEFAULT_PERMISSIONS = {
    "admin": [k for k, _ in ALL_PERMISSIONS],  # admin gets everything
    "product": [
        "page.dashboard", "page.passwords", "page.approvals",
        "func.password.create", "func.password.share",
    ],
    "developer": [
        "page.dashboard", "page.passwords", "page.servers", "page.approvals",
        "func.password.create", "func.server.terminal", "func.server.change_pwd",
    ],
}
