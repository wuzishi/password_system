import enum


class Role(str, enum.Enum):
    ADMIN = "admin"
    PRODUCT = "product"
    DEVELOPER = "developer"


# Permission matrix
PERMISSIONS = {
    "user.manage": [Role.ADMIN],
    "team.create": [Role.ADMIN],
    "team.edit": [Role.ADMIN],
    "team.delete": [Role.ADMIN],
    "team.manage_members": [Role.ADMIN],
    "password.create_team": [Role.ADMIN, Role.PRODUCT],
    "password.edit_team": [Role.ADMIN, Role.PRODUCT],
    "password.delete": [Role.ADMIN],
    "password.share": [Role.ADMIN, Role.PRODUCT],
    "password.view_team": [Role.ADMIN, Role.PRODUCT, Role.DEVELOPER],
    "password.create_personal": [Role.ADMIN, Role.PRODUCT, Role.DEVELOPER],
    "audit.view": [Role.ADMIN],
}


def has_permission(role: Role, permission: str) -> bool:
    allowed_roles = PERMISSIONS.get(permission, [])
    return role in allowed_roles
