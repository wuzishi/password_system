import os
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from app.config import settings

_fernet = None
_aesgcm = None

V2_PREFIX = "v2:"


def _get_fernet() -> Fernet:
    global _fernet
    if _fernet is None:
        key = settings.get_fernet_key()
        _fernet = Fernet(key.encode() if isinstance(key, str) else key)
    return _fernet


def _get_aesgcm() -> AESGCM:
    global _aesgcm
    if _aesgcm is None:
        _aesgcm = AESGCM(settings.get_aes_key())
    return _aesgcm


def encrypt(plaintext: str) -> str:
    """Encrypt with AES-256-GCM. Output: 'v2:' + base64(nonce + ciphertext)."""
    nonce = os.urandom(12)
    ciphertext = _get_aesgcm().encrypt(nonce, plaintext.encode(), None)
    blob = base64.b64encode(nonce + ciphertext).decode()
    return V2_PREFIX + blob


def decrypt(ciphertext: str) -> str:
    """Decrypt. Supports both v2 (AES-256-GCM) and legacy Fernet format."""
    if not ciphertext:
        return ""
    if ciphertext.startswith(V2_PREFIX):
        raw = base64.b64decode(ciphertext[len(V2_PREFIX):])
        nonce, ct = raw[:12], raw[12:]
        return _get_aesgcm().decrypt(nonce, ct, None).decode()
    else:
        return _get_fernet().decrypt(ciphertext.encode()).decode()


def migrate_if_needed(ciphertext: str) -> tuple[str, bool]:
    """Decrypt and re-encrypt with AES-256-GCM if still in legacy format.
    Returns (new_ciphertext, was_migrated)."""
    if not ciphertext:
        return ciphertext, False
    if ciphertext.startswith(V2_PREFIX):
        return ciphertext, False
    plaintext = decrypt(ciphertext)
    return encrypt(plaintext), True
