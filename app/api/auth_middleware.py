from typing import Optional
from fastapi import Request, HTTPException, status, Header
from app.services.auth_service import AuthService
from app.db.models import User
from app.api.session_manager import get_session
from config import logger

auth_service = AuthService()


async def get_current_user(
        request: Request,
        authorization: Optional[str] = Header(None)
) -> User:
    """
    Get current authenticated user from session cookie OR API token.

    Priority:
    1. Session cookie (web)
    2. Authorization header with Bearer token (CLI)
    3. X-API-Token header (alternative)

    Raises:
        HTTPException: 401 if not authenticated
    """
    # Try session cookie first (web)
    session = await get_session(request)  # ✅ Added await
    if session and session.get("user_id"):
        user = await auth_service.get_user_by_id(session["user_id"])
        if user and user.is_active:
            return user

    # Try Authorization header (Bearer token)
    if authorization and authorization.startswith('Bearer '):
        token = authorization.replace('Bearer ', '').strip()
        user = await auth_service.validate_api_token(token)
        if user:
            return user

    # Try X-API-Token header (alternative)
    api_token = request.headers.get('X-API-Token')
    if api_token:
        user = await auth_service.validate_api_token(api_token)
        if user:
            return user

    # No valid authentication found
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required. Please login or provide a valid API token.",
        headers={"WWW-Authenticate": "Bearer"}
    )


async def get_current_user_optional(
        request: Request,
        authorization: Optional[str] = Header(None)
) -> Optional[User]:
    """
    Get current authenticated user, or None if not authenticated.

    Same as get_current_user but returns None instead of raising exception.
    """
    try:
        return await get_current_user(request, authorization)
    except HTTPException:
        return None