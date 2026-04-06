import base64
from pydantic_settings import BaseSettings
from cryptography.fernet import Fernet


class Settings(BaseSettings):
    DATABASE_URL: str = "mysql+pymysql://root:Sjzyt130@localhost:3306/password_system?charset=utf8mb4"
    JWT_SECRET: str = "your-super-secret-jwt-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 480
    FERNET_KEY: str = ""
    AES_KEY: str = ""
    DECRYPT_TOKEN_MINUTES: int = 5
    VERIFY_INTERVAL_HOURS: int = 24

    class Config:
        env_file = ".env"

    def get_fernet_key(self) -> str:
        if not self.FERNET_KEY:
            key = Fernet.generate_key().decode()
            self.FERNET_KEY = key
        return self.FERNET_KEY

    def get_aes_key(self) -> bytes:
        if not self.AES_KEY:
            key = base64.b64encode(__import__("os").urandom(32)).decode()
            self.AES_KEY = key
        raw = base64.b64decode(self.AES_KEY)
        if len(raw) != 32:
            raise ValueError("AES_KEY must be 32 bytes (base64 encoded)")
        return raw


settings = Settings()
