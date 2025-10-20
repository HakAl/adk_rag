from datetime import datetime, timedelta
from typing import Optional
from fastapi import Request, HTTPException, status
from sqlalchemy import select, delete, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.db.models import RateLimit, LoginAttempt
from config import logger

# Rate limit configurations
RATE_LIMITS = {
    # Unauthenticated endpoints (per IP)
    "unauth_general": {"requests": 10, "window": 60},  # 10 req/min
    "register": {"requests": 3, "window": 3600},  # 3 req/hour
    "login": {"requests": 5, "window": 900},  # 5 req/15min
    "resend_verification": {"requests": 3, "window": 3600},  # 3 req/hour

    # Authenticated endpoints (per user)
    "auth_chat": {"requests": 30, "window": 60},  # 30 req/min
    "auth_general": {"requests": 60, "window": 60},  # 60 req/min
}

# Login lockout configuration
LOGIN_LOCKOUT_THRESHOLD = 5  # attempts
LOGIN_LOCKOUT_DURATION = timedelta(minutes=15)


async def check_rate_limit(
        client_id: str,
        endpoint: str,
        limit_config: dict
) -> bool:
    """
    Check if request is within rate limit.

    Args:
        client_id: IP address or user ID
        endpoint: Endpoint identifier
        limit_config: Dict with 'requests' and 'window' (seconds)

    Returns:
        True if allowed, False if rate limited
    """
    max_requests = limit_config["requests"]
    window_seconds = limit_config["window"]
    now = datetime.utcnow()
    window_start = now - timedelta(seconds=window_seconds)

    async for db in get_db():
        try:
            # Get or create rate limit entry
            result = await db.execute(
                select(RateLimit).where(
                    RateLimit.client_id == client_id,
                    RateLimit.endpoint == endpoint
                )
            )
            rate_limit = result.scalar_one_or_none()

            if not rate_limit:
                # First request - create entry
                rate_limit = RateLimit(
                    client_id=client_id,
                    endpoint=endpoint,
                    request_count=1,
                    window_start=now,
                    last_request=now
                )
                db.add(rate_limit)
                await db.commit()
                return True

            # Check if window has expired
            if rate_limit.window_start < window_start:
                # Reset window
                rate_limit.request_count = 1
                rate_limit.window_start = now
                rate_limit.last_request = now
                await db.commit()
                return True

            # Check if limit exceeded
            if rate_limit.request_count >= max_requests:
                return False

            # Increment counter
            rate_limit.request_count += 1
            rate_limit.last_request = now
            await db.commit()
            return True

        except Exception as e:
            logger.error(f"Error checking rate limit: {e}")
            await db.rollback()
            # Fail open - allow request on error
            return True
        break

    return True


async def check_login_lockout(client_id: str, username_or_email: str) -> Optional[datetime]:
    """
    Check if client is locked out from login attempts.

    Args:
        client_id: IP address
        username_or_email: Login identifier

    Returns:
        locked_until datetime if locked, None otherwise
    """
    async for db in get_db():
        try:
            result = await db.execute(
                select(LoginAttempt).where(
                    LoginAttempt.client_id == client_id
                )
            )
            attempt = result.scalar_one_or_none()

            if not attempt:
                return None

            # Check if lockout expired
            if attempt.locked_until and datetime.utcnow() < attempt.locked_until:
                return attempt.locked_until

            return None

        except Exception as e:
            logger.error(f"Error checking login lockout: {e}")
            return None
        break

    return None


async def record_failed_login(client_id: str, username_or_email: str):
    """
    Record a failed login attempt and apply lockout if threshold reached.

    Args:
        client_id: IP address
        username_or_email: Login identifier
    """
    async for db in get_db():
        try:
            result = await db.execute(
                select(LoginAttempt).where(
                    LoginAttempt.client_id == client_id
                )
            )
            attempt = result.scalar_one_or_none()

            now = datetime.utcnow()

            if not attempt:
                # First failed attempt
                attempt = LoginAttempt(
                    client_id=client_id,
                    username_or_email=username_or_email,
                    failed_count=1,
                    last_attempt=now
                )
                db.add(attempt)
            else:
                # Check if lockout expired - reset counter
                if attempt.locked_until and now >= attempt.locked_until:
                    attempt.failed_count = 1
                    attempt.locked_until = None
                else:
                    attempt.failed_count += 1

                attempt.username_or_email = username_or_email
                attempt.last_attempt = now

                # Apply lockout if threshold reached
                if attempt.failed_count >= LOGIN_LOCKOUT_THRESHOLD:
                    attempt.locked_until = now + LOGIN_LOCKOUT_DURATION
                    logger.warning(
                        f"Login lockout applied for {client_id} "
                        f"until {attempt.locked_until}"
                    )

            await db.commit()

        except Exception as e:
            logger.error(f"Error recording failed login: {e}")
            await db.rollback()
        break


async def clear_failed_logins(client_id: str):
    """
    Clear failed login attempts after successful login.

    Args:
        client_id: IP address
    """
    async for db in get_db():
        try:
            await db.execute(
                delete(LoginAttempt).where(LoginAttempt.client_id == client_id)
            )
            await db.commit()
        except Exception as e:
            logger.error(f"Error clearing failed logins: {e}")
            await db.rollback()
        break


async def cleanup_old_rate_limits():
    """Background task to clean up old rate limit entries."""
    cutoff = datetime.utcnow() - timedelta(hours=24)

    async for db in get_db():
        try:
            # Clean up old rate limits
            await db.execute(
                delete(RateLimit).where(RateLimit.last_request < cutoff)
            )

            # Clean up old login attempts (keep for 24 hours after lockout)
            await db.execute(
                delete(LoginAttempt).where(
                    LoginAttempt.last_attempt < cutoff,
                    LoginAttempt.locked_until == None
                )
            )

            await db.commit()
            logger.info("Cleaned up old rate limit data")
        except Exception as e:
            logger.error(f"Error cleaning up rate limits: {e}")
            await db.rollback()
        break