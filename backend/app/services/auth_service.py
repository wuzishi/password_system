import uuid
import threading
import time
from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
import bcrypt
from app.config import settings


# ---- 密码哈希 ----

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt(rounds=12)).decode()


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


# ---- JWT Token ----

ACCESS_TOKEN_MINUTES = min(settings.JWT_EXPIRE_MINUTES, 30)
REFRESH_TOKEN_DAYS = 7


class _TTLBlacklist:
    """带 TTL 自动清理的 token 黑名单。避免内存无限增长。"""

    def __init__(self, cleanup_interval: int = 300):
        self._store: dict[str, float] = {}  # jti -> expire_timestamp
        self._lock = threading.Lock()
        self._cleanup_interval = cleanup_interval
        self._last_cleanup = time.time()

    def add(self, jti: str, expires_at: float):
        with self._lock:
            self._store[jti] = expires_at
            self._maybe_cleanup()

    def __contains__(self, jti: str) -> bool:
        with self._lock:
            exp = self._store.get(jti)
            if exp is None:
                return False
            if time.time() > exp:
                del self._store[jti]
                return False
            return True

    def _maybe_cleanup(self):
        now = time.time()
        if now - self._last_cleanup < self._cleanup_interval:
            return
        self._last_cleanup = now
        expired = [k for k, v in self._store.items() if now > v]
        for k in expired:
            del self._store[k]


_token_blacklist = _TTLBlacklist()


def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_MINUTES)
    jti = uuid.uuid4().hex
    to_encode.update({"exp": expire, "jti": jti, "type": "access"})
    return jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_DAYS)
    jti = uuid.uuid4().hex
    to_encode.update({"exp": expire, "jti": jti, "type": "refresh"})
    return jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> dict | None:
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        jti = payload.get("jti")
        if jti and jti in _token_blacklist:
            return None
        return payload
    except JWTError:
        return None


def revoke_token(token: str):
    """将 token 加入黑名单，TTL 为 token 剩余有效期。"""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM],
                             options={"verify_exp": False})
        jti = payload.get("jti")
        exp = payload.get("exp", 0)
        if jti:
            _token_blacklist.add(jti, float(exp))
    except JWTError:
        pass


# ---- Decrypt Token ----

def create_decrypt_token(user_id: int) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.DECRYPT_TOKEN_MINUTES)
    return jwt.encode(
        {"sub": str(user_id), "scope": "decrypt", "exp": expire, "jti": uuid.uuid4().hex},
        settings.JWT_SECRET,
        algorithm=settings.JWT_ALGORITHM,
    )


def verify_decrypt_token(token: str, user_id: int) -> bool:
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        jti = payload.get("jti")
        if jti and jti in _token_blacklist:
            return False
        return payload.get("scope") == "decrypt" and payload.get("sub") == str(user_id)
    except JWTError:
        return False
