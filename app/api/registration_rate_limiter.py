"""
Registration attempt tracking and CAPTCHA escalation logic.
"""
from datetime import datetime, timedelta
from typing import Optional, Tuple
from sqlalchemy import select, delete
from app.db.database import get_db
from app.db.models import RegistrationAttempt
from config import settings, logger


async def check_registration_captcha_required(client_id: str) -> Tuple[bool, int]:
    """
    Check if visible CAPTCHA is required for this IP.

    Args:
        client_id: IP address

    Returns:
        Tuple of (captcha_required: bool, failed_count: int)
    """
    window_start = datetime.utcnow() - timedelta(seconds=settings.registration_attempt_window)

    async for db in get_db():
        try:
            result = await db.execute(
                select(RegistrationAttempt).where(
                    RegistrationAttempt.client_id == client_id
                )
            )
            attempt = result.scalar_one_or_none()

            if not attempt:
                return False, 0

            # Check if window expired - reset
            if attempt.last_attempt < window_start:
                attempt.failed_count = 0
                attempt.last_attempt = datetime.utcnow()
                await db.commit()
                return False, 0

            # Check threshold
            captcha_required = attempt.failed_count >= settings.registration_captcha_threshold
            return captcha_required, attempt.failed_count

        except Exception as e:
            logger.error(f"Error checking registration captcha: {e}")
            return False, 0
        break

    return False, 0


async def record_registration_attempt(
        client_id: str,
        success: bool,
        error_type: Optional[str] = None
):
    """
    Record a registration attempt.

    Args:
        client_id: IP address
        success: Whether registration succeeded
        error_type: Type of error if failed ('captcha_failed', 'user_exists', etc.)
    """
    async for db in get_db():
        try:
            result = await db.execute(
                select(RegistrationAttempt).where(
                    RegistrationAttempt.client_id == client_id
                )
            )
            attempt = result.scalar_one_or_none()

            now = datetime.utcnow()
            window_start = now - timedelta(seconds=settings.registration_attempt_window)

            if success:
                # Clear attempts on success
                if attempt:
                    await db.delete(attempt)
                    await db.commit()
                return

            # Record failure
            if not attempt:
                attempt = RegistrationAttempt(
                    client_id=client_id,
                    failed_count=1,
                    last_attempt=now,
                    last_error_type=error_type
                )
                db.add(attempt)
            else:
                # Reset if window expired
                if attempt.last_attempt < window_start:
                    attempt.failed_count = 1
                else:
                    attempt.failed_count += 1

                attempt.last_attempt = now
                attempt.last_error_type = error_type

            await db.commit()

            # Log if threshold reached
            if attempt.failed_count >= settings.registration_captcha_threshold:
                logger.warning(
                    f"CAPTCHA threshold reached for IP {client_id}: "
                    f"{attempt.failed_count} failed attempts"
                )

        except Exception as e:
            logger.error(f"Error recording registration attempt: {e}")
            await db.rollback()
        break


async def cleanup_old_registration_attempts():
    """Background task to clean up old registration attempts."""
    cutoff = datetime.utcnow() - timedelta(hours=24)

    async for db in get_db():
        try:
            await db.execute(
                delete(RegistrationAttempt).where(
                    RegistrationAttempt.last_attempt < cutoff
                )
            )
            await db.commit()
            logger.info("Cleaned up old registration attempts")
        except Exception as e:
            logger.error(f"Error cleaning up registration attempts: {e}")
            await db.rollback()
        break