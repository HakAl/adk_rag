"""
Session and CSRF token management with PostgreSQL backend.
"""
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict
from fastapi import Request, HTTPException, status
from fastapi.responses import Response
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.db.models import WebSession
from config import logger

# Configuration
SESSION_COOKIE_NAME = "session_id"
CSRF_HEADER_NAME = "X-CSRF-Token"
SESSION_LIFETIME = timedelta(hours=24)
CSRF_TOKEN_LENGTH = 32


def generate_session_id() -> str:
    """Generate a cryptographically secure session ID."""
    return secrets.token_urlsafe(32)


def generate_csrf_token() -> str:
    """Generate a cryptographically secure CSRF token."""
    return secrets.token_urlsafe(CSRF_TOKEN_LENGTH)


async def create_session(response: Response, user_id: str, chat_session_id: str) -> str:
    """
    Create a new session and set secure cookie.

    Args:
        response: FastAPI response object
        user_id: User identifier
        chat_session_id: Chat session ID from database

    Returns:
        session_id: The generated session ID
    """
    session_id = generate_session_id()
    csrf_token = generate_csrf_token()
    now = datetime.utcnow()
    expires_at = now + SESSION_LIFETIME

    # Store session in database
    async for db in get_db():
        try:
            session = WebSession(
                id=session_id,
                user_id=user_id,
                chat_session_id=chat_session_id,
                csrf_token=csrf_token,
                created_at=now,
                last_activity=now,
                expires_at=expires_at
            )
            db.add(session)
            await db.commit()
        except Exception as e:
            logger.error(f"Error creating session: {e}")
            await db.rollback()
            raise
        break

    # Set secure HttpOnly cookie
    # Note: secure=True for production, secure=False for local dev
    # You should use environment variable to control this
    from config import settings
    is_production = settings.environment == "production"

    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=session_id,
        httponly=True,
        secure=is_production,  # HTTPS only in production
        samesite="strict",
        max_age=int(SESSION_LIFETIME.total_seconds())
    )

    # Send CSRF token in response header
    response.headers[CSRF_HEADER_NAME] = csrf_token

    return session_id


async def get_session(request: Request) -> Optional[Dict]:
    """
    Get session data from cookie.

    Args:
        request: FastAPI request object

    Returns:
        Session data dict or None if invalid/expired
    """
    session_id = request.cookies.get(SESSION_COOKIE_NAME)

    if not session_id:
        return None

    async for db in get_db():
        try:
            # Query session
            result = await db.execute(
                select(WebSession).where(WebSession.id == session_id)
            )
            session = result.scalar_one_or_none()

            if not session:
                return None

            # Check expiration
            if datetime.utcnow() > session.expires_at:
                await delete_session(session_id)
                return None

            # Update last activity
            session.last_activity = datetime.utcnow()
            await db.commit()

            return {
                "user_id": str(session.user_id),
                "chat_session_id": session.chat_session_id,
                "created_at": session.created_at,
                "last_activity": session.last_activity
            }

        except Exception as e:
            logger.error(f"Error getting session: {e}")
            return None
        break

    return None


async def verify_csrf_token(request: Request) -> bool:
    """
    Verify CSRF token from request header matches session.

    Args:
        request: FastAPI request object

    Returns:
        True if valid, False otherwise
    """
    session_id = request.cookies.get(SESSION_COOKIE_NAME)
    csrf_token = request.headers.get(CSRF_HEADER_NAME)

    if not session_id or not csrf_token:
        return False

    async for db in get_db():
        try:
            result = await db.execute(
                select(WebSession).where(WebSession.id == session_id)
            )
            session = result.scalar_one_or_none()

            if not session:
                return False

            # Constant-time comparison to prevent timing attacks
            return secrets.compare_digest(csrf_token, session.csrf_token)

        except Exception as e:
            logger.error(f"Error verifying CSRF token: {e}")
            return False
        break

    return False


async def delete_session(session_id: str):
    """Delete session from database."""
    async for db in get_db():
        try:
            await db.execute(
                delete(WebSession).where(WebSession.id == session_id)
            )
            await db.commit()
        except Exception as e:
            logger.error(f"Error deleting session: {e}")
            await db.rollback()
        break


async def clear_session(response: Response, request: Request):
    """Clear session cookie and data."""
    session_id = request.cookies.get(SESSION_COOKIE_NAME)
    if session_id:
        await delete_session(session_id)

    from config import settings
    is_production = settings.environment == "production"

    response.delete_cookie(
        key=SESSION_COOKIE_NAME,
        httponly=True,
        secure=is_production,
        samesite="strict"
    )


async def require_session(request: Request) -> Dict:
    """
    Dependency to require valid session.

    Raises:
        HTTPException: If session is invalid or missing
    """
    session = await get_session(request)

    if not session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session"
        )

    return session


async def require_csrf(request: Request):
    """
    Dependency to require valid CSRF token for state-changing operations.

    Raises:
        HTTPException: If CSRF token is invalid or missing
    """
    if request.method in ["POST", "PUT", "DELETE", "PATCH"]:
        if not await verify_csrf_token(request):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid or missing CSRF token"
            )


async def cleanup_expired_sessions():
    """Background task to clean up expired sessions."""
    async for db in get_db():
        try:
            await db.execute(
                delete(WebSession).where(WebSession.expires_at < datetime.utcnow())
            )
            await db.commit()
            logger.info("Cleaned up expired sessions")
        except Exception as e:
            logger.error(f"Error cleaning up sessions: {e}")
            await db.rollback()
        break