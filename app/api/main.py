from fastapi import FastAPI, HTTPException, Depends, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse, RedirectResponse
from contextlib import asynccontextmanager
from typing import Optional
from pydantic import ValidationError
from collections import defaultdict
from datetime import datetime, timedelta

from config import settings, logger
from app.core.application import RAGAgentApp
from app.api.models import (
    ChatRequest,
    ChatResponse,
    SessionCreateRequest,
    SessionCreateResponse,
    StatsResponse,
    HealthResponse,
    RegisterRequest,
    RegisterResponse,
    LoginRequest,
    LoginResponse,
    UserResponse,
    ResendVerificationRequest,
    VerifyEmailResponse
)
from app.utils.input_sanitizer import InputSanitizationError
from app.db.database import init_db, close_db
from app.api.session_manager import (
    create_session,
    get_session,
    clear_session,
    require_csrf
)
from app.api.auth_middleware import get_current_user
from app.services.auth_service import AuthService
from app.db.models import User
import json
import asyncio

rag_app: Optional[RAGAgentApp] = None
auth_service = AuthService()
rate_limit_store = defaultdict(list)
resend_limit_store = defaultdict(list)
RATE_LIMIT_REQUESTS = 60
RATE_LIMIT_WINDOW = 60
RESEND_LIMIT_REQUESTS = 3
RESEND_LIMIT_WINDOW = 3600  # 1 hour


@asynccontextmanager
async def lifespan(app: FastAPI):
    global rag_app
    logger.info("Starting FastAPI application")
    await init_db()
    rag_app = RAGAgentApp()
    yield
    logger.info("Shutting down FastAPI application")
    await close_db()
    rag_app = None


app = FastAPI(
    title=settings.app_name,
    version=settings.version,
    lifespan=lifespan
)


@app.middleware("http")
async def disable_compression_for_streams(request: Request, call_next):
    response = await call_next(request)
    if request.url.path.endswith("/stream"):
        if "content-encoding" in response.headers:
            del response.headers["content-encoding"]
    return response


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "X-CSRF-Token", "Authorization", "X-API-Token"],
    expose_headers=["X-CSRF-Token"],
)


def get_app() -> RAGAgentApp:
    if rag_app is None:
        raise HTTPException(status_code=503, detail="Service not initialized")
    return rag_app


def check_rate_limit(client_id: str) -> bool:
    now = datetime.now()
    cutoff = now - timedelta(seconds=RATE_LIMIT_WINDOW)
    rate_limit_store[client_id] = [
        timestamp for timestamp in rate_limit_store[client_id]
        if timestamp > cutoff
    ]
    if len(rate_limit_store[client_id]) >= RATE_LIMIT_REQUESTS:
        return False
    rate_limit_store[client_id].append(now)
    return True


def check_resend_limit(client_id: str) -> bool:
    """Check rate limit for resend verification email (3 per hour)."""
    now = datetime.now()
    cutoff = now - timedelta(seconds=RESEND_LIMIT_WINDOW)
    resend_limit_store[client_id] = [
        timestamp for timestamp in resend_limit_store[client_id]
        if timestamp > cutoff
    ]
    if len(resend_limit_store[client_id]) >= RESEND_LIMIT_REQUESTS:
        return False
    resend_limit_store[client_id].append(now)
    return True


async def rate_limit_dependency(request: Request):
    client_id = request.client.host if request.client else "unknown"
    if not check_rate_limit(client_id):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Please try again later."
        )


@app.exception_handler(ValidationError)
async def validation_exception_handler(request: Request, exc: ValidationError):
    logger.warning(f"Validation error: {exc}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": "Input validation failed", "errors": exc.errors()}
    )


@app.exception_handler(InputSanitizationError)
async def sanitization_exception_handler(request: Request, exc: InputSanitizationError):
    logger.warning(f"Sanitization error: {exc}")
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": "Input validation failed", "error": str(exc)}
    )


@app.get("/health", response_model=HealthResponse)
async def health_check():
    return HealthResponse(status="healthy", version=settings.version)


# ============================================================================
# AUTHENTICATION ENDPOINTS
# ============================================================================

@app.post(
    "/register",
    response_model=RegisterResponse,
    dependencies=[Depends(rate_limit_dependency)]
)
async def register(request_data: RegisterRequest):
    """Register a new user and send verification email."""
    try:
        user, error = await auth_service.create_user(
            username=request_data.username,
            email=request_data.email,
            password=request_data.password
        )

        if error:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error
            )

        return RegisterResponse(
            user_id=str(user.id),
            username=user.username,
            email=user.email,
            message="Registration successful. Please check your email to verify your account."
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during registration: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
        )


@app.get("/verify-email", response_model=VerifyEmailResponse)
async def verify_email(token: str):
    """Verify email with token from email link."""
    try:
        success, error = await auth_service.verify_email(token)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error or "Verification failed"
            )

        # Return simple success page or redirect to frontend
        return VerifyEmailResponse(
            message="Email verified successfully! You can now login.",
            verified=True
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during email verification: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Verification failed"
        )


@app.post(
    "/resend-verification",
    dependencies=[Depends(rate_limit_dependency)]
)
async def resend_verification(request: Request, request_data: ResendVerificationRequest):
    """Resend verification email (rate limited: 3 per hour)."""
    try:
        # Check resend-specific rate limit
        client_id = request.client.host if request.client else "unknown"
        if not check_resend_limit(client_id):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many resend requests. Please try again later."
            )

        success, error = await auth_service.resend_verification_email(request_data.email)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error or "Failed to resend verification email"
            )

        return {"message": "Verification email sent. Please check your inbox."}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resending verification: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to resend verification email"
        )


@app.post(
    "/login",
    response_model=LoginResponse,
    dependencies=[Depends(rate_limit_dependency)]
)
async def login(
    request_data: LoginRequest,
    request: Request,
    response: Response,
    app: RAGAgentApp = Depends(get_app)
):
    """Login and create session (requires verified email)."""
    try:
        # Authenticate user
        user, error_type = await auth_service.authenticate_user(
            username_or_email=request_data.username_or_email,
            password=request_data.password
        )

        if error_type == "email_not_verified":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Email not verified"
            )

        if error_type == "invalid_credentials" or not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )

        # Create chat session
        chat_session_id = await app.create_coordinator_session(str(user.id))

        # Create web session with cookie
        create_session(response, str(user.id), chat_session_id)

        return LoginResponse(
            user_id=str(user.id),
            username=user.username,
            email=user.email
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during login: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )


@app.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """Get current user info."""
    return UserResponse(
        user_id=str(current_user.id),
        username=current_user.username,
        email=current_user.email,
        is_active=current_user.is_active,
        created_at=current_user.created_at.isoformat()
    )


@app.post("/logout")
async def logout(request: Request, response: Response):
    """Logout and clear session."""
    session = get_session(request)
    if session:
        clear_session(response, request)
        return {"message": "Logged out successfully"}
    return {"message": "No active session"}


# ============================================================================
# SESSION ENDPOINTS (Now require authentication)
# ============================================================================

@app.post(
    "/sessions/coordinator",
    response_model=SessionCreateResponse,
    dependencies=[Depends(rate_limit_dependency)]
)
async def create_coordinator_session(
    request: Request,
    response: Response,
    app: RAGAgentApp = Depends(get_app),
    current_user: User = Depends(get_current_user)
):
    """Create a new coordinator session (requires authentication)."""
    try:
        chat_session_id = await app.create_coordinator_session(str(current_user.id))

        # For web users, create/update session cookie
        session = get_session(request)
        if not session:
            create_session(response, str(current_user.id), chat_session_id)

        return SessionCreateResponse(
            session_id=chat_session_id,
            user_id=str(current_user.id)
        )
    except Exception as e:
        logger.error(f"Error creating coordinator session: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# CHAT ENDPOINTS (Now use authentication)
# ============================================================================

@app.post(
    "/chat/coordinator",
    response_model=ChatResponse,
    dependencies=[Depends(rate_limit_dependency)]
)
async def chat_coordinator(
    request_data: ChatRequest,
    request: Request,
    app: RAGAgentApp = Depends(get_app),
    current_user: User = Depends(get_current_user)
):
    """Chat with coordinator (requires authentication)."""
    try:
        # Get session ID from cookie or request body (backward compatible)
        session = get_session(request)

        if session:
            # Web: use session from cookie
            from app.api.session_manager import verify_csrf_token
            if not verify_csrf_token(request):
                raise HTTPException(status_code=403, detail="Invalid CSRF token")
            chat_session_id = session["chat_session_id"]
        elif request_data.session_id:
            # CLI: use session from request body
            chat_session_id = request_data.session_id
        else:
            raise HTTPException(
                status_code=400,
                detail="Session ID required"
            )

        response = await app.coordinator_chat(
            message=request_data.message,
            user_id=str(current_user.id),
            session_id=chat_session_id
        )

        return ChatResponse(
            response=response,
            session_id=chat_session_id,
            routing_info=None
        )

    except InputSanitizationError as e:
        logger.warning(f"Input sanitization failed: {e}")
        raise HTTPException(status_code=400, detail=f"Input validation failed: {str(e)}")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in chat/coordinator: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post(
    "/chat/coordinator/stream",
    dependencies=[Depends(rate_limit_dependency)]
)
async def chat_coordinator_stream(
    request_data: ChatRequest,
    request: Request,
    app: RAGAgentApp = Depends(get_app),
    current_user: User = Depends(get_current_user)
):
    """Stream chat with coordinator (requires authentication)."""
    async def event_generator():
        try:
            session = get_session(request)

            if session:
                from app.api.session_manager import verify_csrf_token
                if not verify_csrf_token(request):
                    error_event = {"type": "error", "data": {"message": "Invalid CSRF token"}}
                    yield f"data: {json.dumps(error_event)}\n\n"
                    return
                chat_session_id = session["chat_session_id"]
            elif request_data.session_id:
                chat_session_id = request_data.session_id
            else:
                error_event = {"type": "error", "data": {"message": "Session ID required"}}
                yield f"data: {json.dumps(error_event)}\n\n"
                return

            async for event in app.coordinator_chat_stream(
                message=request_data.message,
                user_id=str(current_user.id),
                session_id=chat_session_id
            ):
                sse_data = f"data: {json.dumps(event)}\n\n"
                yield sse_data
                await asyncio.sleep(0.001)

        except InputSanitizationError as e:
            logger.warning(f"Input sanitization failed: {e}")
            error_event = {"type": "error", "data": {"message": f"Input validation failed: {str(e)}"}}
            yield f"data: {json.dumps(error_event)}\n\n"
        except Exception as e:
            logger.error(f"Error in streaming chat: {e}", exc_info=True)
            error_event = {"type": "error", "data": {"message": str(e)}}
            yield f"data: {json.dumps(error_event)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        }
    )


@app.get("/stats", response_model=StatsResponse)
async def get_stats(app: RAGAgentApp = Depends(get_app)):
    """Get application statistics (public)."""
    stats = app.get_stats()
    return StatsResponse(**stats)