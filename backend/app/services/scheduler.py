import asyncio
import logging
from datetime import datetime, timezone

import paramiko

from app.config import settings
from app.database import SessionLocal
from app.models.password_entry import PasswordEntry
from app.services.crypto_service import decrypt

logger = logging.getLogger("scheduler")


def _verify_single(entry: PasswordEntry, db) -> str:
    """SSH verify a single server password. Returns status string."""
    plaintext_password = decrypt(entry.encrypted_password)
    port = entry.port or 22
    username = entry.username or "root"

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.WarningPolicy())
    try:
        client.load_system_host_keys()
    except Exception:
        pass
    try:
        client.connect(
            hostname=entry.host,
            port=port,
            username=username,
            password=plaintext_password,
            timeout=10,
            look_for_keys=False,
            allow_agent=False,
        )
        client.close()
        return "valid"
    except paramiko.AuthenticationException:
        return "invalid"
    except Exception as e:
        logger.warning(f"SSH verify error for {entry.title} ({entry.host}): {e}")
        return "error"
    finally:
        client.close()


def run_verify_all():
    """Verify all server passwords with SSH connection."""
    db = SessionLocal()
    try:
        entries = db.query(PasswordEntry).filter(
            PasswordEntry.category == "server",
            PasswordEntry.host != "",
            PasswordEntry.host.isnot(None),
        ).all()

        if not entries:
            logger.info("No server passwords to verify")
            return

        now = datetime.now(timezone.utc)
        logger.info(f"Starting auto-verify for {len(entries)} server passwords")

        for entry in entries:
            try:
                status = _verify_single(entry, db)
                entry.verify_status = status
                entry.last_verified_at = now
                db.commit()
                logger.info(f"  [{status}] {entry.title} ({entry.host}:{entry.port or 22})")
            except Exception as e:
                db.rollback()
                logger.error(f"  [error] {entry.title}: {e}")

        logger.info("Auto-verify completed")
    finally:
        db.close()


async def scheduler_loop():
    """Background loop that runs verification periodically."""
    interval = settings.VERIFY_INTERVAL_HOURS * 3600
    # Wait 60 seconds after startup before first run
    await asyncio.sleep(60)
    while True:
        try:
            logger.info("Scheduler: running auto-verify...")
            await asyncio.get_event_loop().run_in_executor(None, run_verify_all)
        except Exception as e:
            logger.error(f"Scheduler error: {e}")
        await asyncio.sleep(interval)
