import base64
import logging
from pydantic_settings import BaseSettings

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    DATABASE_URL: str = "mysql+pymysql://root:password@localhost:3306/password_system?charset=utf8mb4"
    JWT_SECRET: str = ""
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 480
    FERNET_KEY: str = ""
    AES_KEY: str = ""
    DECRYPT_TOKEN_MINUTES: int = 5
    VERIFY_INTERVAL_HOURS: int = 24
    SMTP_HOST: str = ""
    SMTP_PORT: int = 465
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_USE_SSL: bool = True
    SITE_URL: str = "http://localhost:3000"
    INVITE_EXPIRE_HOURS: int = 72
    ADMIN_PASSWORD: str = ""
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173"

    class Config:
        env_file = ".env"

    def get_fernet_key(self) -> str:
        if not self.FERNET_KEY:
            raise ValueError("FERNET_KEY 未配置，请在 .env 中设置")
        return self.FERNET_KEY

    def get_aes_key(self) -> bytes:
        if not self.AES_KEY:
            raise ValueError("AES_KEY 未配置，请在 .env 中设置")
        raw = base64.b64decode(self.AES_KEY)
        if len(raw) != 32:
            raise ValueError("AES_KEY must be 32 bytes (base64 encoded)")
        return raw

    def get_cors_origins(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    def validate_required(self):
        """启动时检查关键配置项。"""
        errors = []
        if not self.JWT_SECRET:
            errors.append("JWT_SECRET")
        if not self.FERNET_KEY:
            errors.append("FERNET_KEY")
        if not self.AES_KEY:
            errors.append("AES_KEY")
        if errors:
            raise ValueError(f"缺少必要配置项: {', '.join(errors)}，请检查 .env 文件")


settings = Settings()
settings.validate_required()
