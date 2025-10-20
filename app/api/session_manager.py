"""
Session and CSRF token management for secure cookie-based sessions.
"""
import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Dict
from fastapi import Request, HTTPException, status
from fastapi.responses import Response

# In-memory storage (replace with Redis/PostgreSQL in production)
session_store: Dict[str, Dict] = {}
csrf_store: Dict[str, str] = {}  # session_id -> csrf_token

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


def create_session(response: Response, user_id: str, chat_session_id: str) -> str:
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

    # Store session data
    session_store[session_id] = {
        "user_id": user_id,
        "chat_session_id": chat_session_id,
        "created_at": datetime.now(),
        "last_activity": datetime.now()
    }

    # Store CSRF token
    csrf_store[session_id] = csrf_token

    # Set secure HttpOnly cookie
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=session_id,
        httponly=True,  # Prevents JavaScript access
        secure=True,  # HTTPS only (set to False for local dev)
        samesite="strict",  # CSRF protection
        max_age=int(SESSION_LIFETIME.total_seconds())
    )

    # Send CSRF token in response header (frontend will store and send back)
    response.headers[CSRF_HEADER_NAME] = csrf_token

    return session_id


def get_session(request: Request) -> Optional[Dict]:
    """
    Get session data from cookie.

    Args:
        request: FastAPI request object

    Returns:
        Session data dict or None if invalid/expired
    """
    session_id = request.cookies.get(SESSION_COOKIE_NAME)

    if not session_id or session_id not in session_store:
        return None

    session = session_store[session_id]

    # Check expiration
    if datetime.now() - session["created_at"] > SESSION_LIFETIME:
        delete_session(session_id)
        return None

    # Update last activity
    session["last_activity"] = datetime.now()

    return session


def verify_csrf_token(request: Request) -> bool:
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

    stored_token = csrf_store.get(session_id)

    if not stored_token:
        return False

    # Constant-time comparison to prevent timing attacks
    return secrets.compare_digest(csrf_token, stored_token)


def delete_session(session_id: str):
    """Delete session and associated CSRF token."""
    session_store.pop(session_id, None)
    csrf_store.pop(session_id, None)


def clear_session(response: Response, request: Request):
    """Clear session cookie and data."""
    session_id = request.cookies.get(SESSION_COOKIE_NAME)
    if session_id:
        delete_session(session_id)

    response.delete_cookie(
        key=SESSION_COOKIE_NAME,
        httponly=True,
        secure=True,
        samesite="strict"
    )


async def require_session(request: Request) -> Dict:
    """
    Dependency to require valid session.

    Raises:
        HTTPException: If session is invalid or missing
    """
    session = get_session(request)

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
    # Only check CSRF for state-changing methods
    if request.method in ["POST", "PUT", "DELETE", "PATCH"]:
        if not verify_csrf_token(request):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid or missing CSRF token"
            )