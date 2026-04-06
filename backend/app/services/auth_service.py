from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
import bcrypt
from app.config import settings


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> dict | None:
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except JWTError:
        return None


def create_decrypt_token(user_id: int) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.DECRYPT_TOKEN_MINUTES)
    return jwt.encode(
        {"sub": str(user_id), "scope": "decrypt", "exp": expire},
        settings.JWT_SECRET,
        algorithm=settings.JWT_ALGORITHM,
    )


def verify_decrypt_token(token: str, user_id: int) -> bool:
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        return payload.get("scope") == "decrypt" and payload.get("sub") == str(user_id)
    except JWTError:
        return False
