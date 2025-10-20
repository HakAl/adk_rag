from fastapi import FastAPI, HTTPException, Depends, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse, RedirectResponse
from contextlib import asynccontextmanager
from typing import Optional
from pydantic import ValidationError

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

from app.api.registration_rate_limiter import (
    check_registration_captcha_required,
    record_registration_attempt,
    cleanup_old_registration_attempts
)
from app.services.hcaptcha_service import HCaptchaService

from app.api.session_manager import (
    create_session,
    get_session,
    clear_session,
    require_csrf,
    cleanup_expired_sessions
)
from app.api.rate_limiter import (
    check_rate_limit,
    check_login_lockout,
    record_failed_login,
    clear_failed_logins,
    cleanup_old_rate_limits,
    RATE_LIMITS
)
from app.api.auth_middleware import get_current_user
from app.services.auth_service import AuthService
from app.db.models import User
import json
import asyncio

rag_app: Optional[RAGAgentApp] = None
auth_service = AuthService()
hcaptcha_service = HCaptchaService()


def get_client_id(request: Request) -> str:
    """Get client identifier (IP address)."""
    return request.client.host if request.client else "unknown"


async def rate_limit_dependency(request: Request):
    """Rate limit for general unauthenticated requests."""
    # Check if CLI (has Authorization header with Bearer token)
    if request.headers.get("Authorization", "").startswith("Bearer "):
        # CLI request - no rate limit
        return

    client_id = get_client_id(request)

    if not await check_rate_limit(client_id, "unauth_general", RATE_LIMITS["unauth_general"]):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Please try again later."
        )


async def register_rate_limit(request: Request):
    """Rate limit for registration endpoint."""
    client_id = get_client_id(request)

    if not await check_rate_limit(client_id, "register", RATE_LIMITS["register"]):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many registration attempts. Please try again later."
        )


async def login_rate_limit(request: Request):
    """Rate limit for login endpoint."""
    client_id = get_client_id(request)

    if not await check_rate_limit(client_id, "login", RATE_LIMITS["login"]):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many login attempts. Please try again in 15 minutes."
        )


async def resend_rate_limit(request: Request):
    """Rate limit for resend verification endpoint."""
    client_id = get_client_id(request)

    if not await check_rate_limit(client_id, "resend_verification", RATE_LIMITS["resend_verification"]):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many resend requests. Please try again later."
        )


async def chat_rate_limit(request: Request, current_user: User = Depends(get_current_user)):
    """Rate limit for authenticated chat endpoints."""
    # Check if CLI (has Authorization header with Bearer token)
    if request.headers.get("Authorization", "").startswith("Bearer "):
        # CLI request - no rate limit
        return

    # Use user_id for authenticated rate limiting
    client_id = str(current_user.id)

    if not await check_rate_limit(client_id, "auth_chat", RATE_LIMITS["auth_chat"]):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Chat rate limit exceeded. Please slow down."
        )


@asynccontextmanager
async def lifespan(app: FastAPI):
    global rag_app
    logger.info("Starting FastAPI application")
    await init_db()
    rag_app = RAGAgentApp()

    # Start background cleanup tasks
    async def cleanup_loop():
        while True:
            await asyncio.sleep(3600)  # Run every hour
            await cleanup_expired_sessions()
            await cleanup_old_rate_limits()
            await cleanup_old_registration_attempts()

    cleanup_task = asyncio.create_task(cleanup_loop())

    yield

    logger.info("Shutting down FastAPI application")
    cleanup_task.cancel()
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


# CORS - Environment-based configuration
allowed_origins = [
    "http://localhost:3000",
    "http://localhost:5173"
]

# Add production origins when deployed
if settings.environment == "production":
    # TODO: Add your GitHub Pages URL here when deployed
    # allowed_origins.append("https://yourusername.github.io")
    pass

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "X-CSRF-Token", "Authorization", "X-API-Token"],
    expose_headers=["X-CSRF-Token"],
)


def get_app() -> RAGAgentApp:
    if rag_app is None:
        raise HTTPException(status_code=503, detail="Service not initialized")
    return rag_app


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
    response_model=RegisterResponse
)
async def register(request_data: RegisterRequest, request: Request):
    """Register a new user with hCaptcha verification."""
    client_id = get_client_id(request)

    try:
        # Check if visible CAPTCHA is required
        captcha_required, failed_count = await check_registration_captcha_required(client_id)

        # Verify hCaptcha token if provided or required
        if request_data.captcha_token:
            success, error = await hcaptcha_service.verify_token(
                request_data.captcha_token,
                client_ip=client_id
            )

            if not success:
                await record_registration_attempt(client_id, False, "captcha_failed")

                # Tell frontend if visible CAPTCHA is now required
                new_captcha_required, new_count = await check_registration_captcha_required(client_id)

                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=error or "CAPTCHA verification failed",
                    headers={"X-Require-Visible-Captcha": str(new_captcha_required).lower()}
                )

        elif captcha_required:
            # No token provided but CAPTCHA is required
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="CAPTCHA verification required",
                headers={"X-Require-Visible-Captcha": "true"}
            )

        # Proceed with registration
        user, error = await auth_service.create_user(
            username=request_data.username,
            email=request_data.email,
            password=request_data.password
        )

        if error:
            # Record failure (user already exists, etc.)
            await record_registration_attempt(client_id, False, "user_exists")

            # Check if CAPTCHA should now be required
            new_captcha_required, _ = await check_registration_captcha_required(client_id)

            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error,
                headers={"X-Require-Visible-Captcha": str(new_captcha_required).lower()}
            )

        # Success - clear attempts
        await record_registration_attempt(client_id, True)

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


@app.get("/register/captcha-status")
async def get_captcha_status(request: Request):
    """Check if visible CAPTCHA is required for this IP."""
    client_id = get_client_id(request)
    captcha_required, failed_count = await check_registration_captcha_required(client_id)

    return {
        "captcha_required": captcha_required,
        "failed_count": failed_count
    }


@app.get("/verify-email", response_model=VerifyEmailResponse)
async def verify_email(token: str, request: Request):
    """Verify email with token from email link."""
    try:
        success, error = await auth_service.verify_email(token)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error or "Verification failed"
            )

        # Clear any failed login attempts for this IP on successful verification
        client_id = get_client_id(request)
        await clear_failed_logins(client_id)

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
    dependencies=[Depends(resend_rate_limit)]
)
async def resend_verification(request: Request, request_data: ResendVerificationRequest):
    """Resend verification email (rate limited: 3 per hour)."""
    try:
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
    dependencies=[Depends(login_rate_limit)]
)
async def login(
        request_data: LoginRequest,
        request: Request,
        response: Response,
        app: RAGAgentApp = Depends(get_app)
):
    """Login and create session (requires verified email)."""
    try:
        client_id = get_client_id(request)

        # Check if locked out
        locked_until = await check_login_lockout(client_id, request_data.username_or_email)
        if locked_until:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Too many failed login attempts. Try again after {locked_until.strftime('%H:%M:%S UTC')}"
            )

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
            # Record failed attempt
            await record_failed_login(client_id, request_data.username_or_email)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )

        # Clear failed login attempts on success
        await clear_failed_logins(client_id)

        # Create chat session
        chat_session_id = await app.create_coordinator_session(str(user.id))

        # Create web session with cookie
        await create_session(response, str(user.id), chat_session_id)

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
    session = await get_session(request)
    if session:
        await clear_session(response, request)
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
        session = await get_session(request)
        if not session:
            await create_session(response, str(current_user.id), chat_session_id)

        return SessionCreateResponse(
            session_id=chat_session_id,
            user_id=str(current_user.id)
        )
    except Exception as e:
        logger.error(f"Error creating coordinator session: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# CHAT ENDPOINTS (Now use authentication and rate limiting)
# ============================================================================

@app.post(
    "/chat/coordinator",
    response_model=ChatResponse,
    dependencies=[Depends(chat_rate_limit)]
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
        session = await get_session(request)

        if session:
            # Web: use session from cookie
            from app.api.session_manager import verify_csrf_token
            if not await verify_csrf_token(request):
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
    dependencies=[Depends(chat_rate_limit)]
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
            session = await get_session(request)

            if session:
                from app.api.session_manager import verify_csrf_token
                if not await verify_csrf_token(request):
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