import re
from pydantic import BaseModel, field_validator, Field


class LoginRequest(BaseModel):
    username: str = Field(..., min_length=1, max_length=50)
    password: str = Field(..., min_length=1, max_length=200)


class Token(BaseModel):
    access_token: str
    refresh_token: str = ""
    token_type: str = "bearer"
    role: str
    username: str
    user_id: int


PASSWORD_MIN_LENGTH = 8
PASSWORD_PATTERN = re.compile(
    r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[!@#$%^&*()_+\-=\[\]{};:\'",.<>?/\\|`~]).{8,}$'
)


def validate_strong_password(v: str) -> str:
    """密码强度校验：至少 8 位，包含大小写字母、数字、特殊字符。"""
    if len(v) < PASSWORD_MIN_LENGTH:
        raise ValueError(f"密码长度不能少于 {PASSWORD_MIN_LENGTH} 位")
    if not re.search(r'[a-z]', v):
        raise ValueError("密码必须包含小写字母")
    if not re.search(r'[A-Z]', v):
        raise ValueError("密码必须包含大写字母")
    if not re.search(r'\d', v):
        raise ValueError("密码必须包含数字")
    if not re.search(r'[!@#$%^&*()_+\-=\[\]{};:\'",.<>?/\\|`~]', v):
        raise ValueError("密码必须包含特殊字符")
    return v
